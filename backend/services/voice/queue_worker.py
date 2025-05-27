"""
Job queue worker for scheduled voice calls.
Uses Redis for queue management with BullMQ-style job processing.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from croniter import croniter

# Import centralized Redis utilities
from utils.redis_client import get_redis_client

from .config import config
from .vapi_client import vapi_client
from .models import VoiceSchedule, VoiceCall, VoiceUser
from .database import get_db_session

logger = logging.getLogger(__name__)


class VoiceCallQueue:
    """Redis-based job queue for voice calls."""

    def __init__(self):
        # Use centralized Redis client instead of direct initialization
        self.queue_name = config.QUEUE_NAME
        self.max_retries = config.MAX_RETRIES

    async def enqueue_call(
        self,
        user_id: str,
        assistant_id: str,
        phone_number: str,
        metadata: Optional[Dict[str, Any]] = None,
        delay_seconds: int = 0,
    ) -> str:
        """
        Enqueue a voice call job.

        Args:
            user_id: User ID
            assistant_id: Vapi assistant ID
            phone_number: Phone number to call
            metadata: Additional call metadata
            delay_seconds: Delay before processing job

        Returns:
            Job ID
        """
        job_id = f"call_{user_id}_{datetime.utcnow().timestamp()}"

        job_data = {
            "id": job_id,
            "type": "outbound_call",
            "user_id": user_id,
            "assistant_id": assistant_id,
            "phone_number": phone_number,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": 0,
            "max_retries": self.max_retries,
        }

        # Calculate execution time
        execute_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        score = execute_at.timestamp()

        # Use centralized Redis client
        redis_client = await get_redis_client()

        # Add to delayed queue
        await redis_client.zadd(
            f"{self.queue_name}:delayed", {json.dumps(job_data): score}
        )

        logger.info(f"Enqueued call job {job_id} for execution at {execute_at}")
        return job_id

    async def enqueue_scheduled_call(self, schedule_id: str) -> Optional[str]:
        """
        Enqueue a call from a schedule.

        Args:
            schedule_id: Schedule ID to execute

        Returns:
            Job ID if successful
        """
        try:
            with get_db_session() as db:
                schedule = (
                    db.query(VoiceSchedule)
                    .filter(
                        VoiceSchedule.id == schedule_id, VoiceSchedule.is_active == True
                    )
                    .first()
                )

                if not schedule:
                    logger.error(f"Schedule {schedule_id} not found or inactive")
                    return None

                # Get user details
                user = (
                    db.query(VoiceUser).filter(VoiceUser.id == schedule.user_id).first()
                )
                if not user or not user.phone:
                    logger.error(
                        f"User {schedule.user_id} not found or has no phone number"
                    )
                    return None

                # Enqueue the call
                metadata = {
                    "schedule_id": schedule_id,
                    "scheduled_call": True,
                    **(schedule.custom_metadata or {}),
                }

                job_id = await self.enqueue_call(
                    user_id=schedule.user_id,
                    assistant_id=schedule.assistant_id,
                    phone_number=user.phone,
                    metadata=metadata,
                )

                # Update schedule
                schedule.last_run_at = datetime.utcnow()

                # Calculate next run time
                cron = croniter(schedule.cron_expression, datetime.utcnow())
                schedule.next_run_at = cron.get_next(datetime)

                logger.info(f"Scheduled call job {job_id} for schedule {schedule_id}")
                return job_id

        except Exception as e:
            logger.error(f"Error enqueuing scheduled call {schedule_id}: {e}")
            return None

    async def process_delayed_jobs(self):
        """Process jobs that are ready to execute."""
        try:
            current_time = datetime.utcnow().timestamp()

            # Get jobs ready for execution
            redis_client = await get_redis_client()
            jobs = await redis_client.zrangebyscore(
                f"{self.queue_name}:delayed", 0, current_time, withscores=True
            )

            for job_data, score in jobs:
                try:
                    job = json.loads(job_data)
                    await self._execute_call_job(job)

                    # Remove from delayed queue
                    await redis_client.zrem(f"{self.queue_name}:delayed", job_data)

                except Exception as e:
                    logger.error(f"Error processing job: {e}")
                    await self._handle_job_failure(job_data, str(e))

        except Exception as e:
            logger.error(f"Error processing delayed jobs: {e}")

    async def _execute_call_job(self, job: Dict[str, Any]):
        """Execute a call job."""
        try:
            logger.info(f"Executing call job {job['id']}")

            # Create outbound call via Vapi
            call_response = await vapi_client.create_outbound_call(
                assistant_id=job["assistant_id"],
                phone_number=job["phone_number"],
                user_id=job["user_id"],
                custom_metadata=job.get("metadata", {}),
            )

            # Store call record
            with get_db_session() as db:
                call_record = VoiceCall(
                    vapi_call_id=call_response["id"],
                    user_id=job["user_id"],
                    assistant_id=job["assistant_id"],
                    channel="phone",
                    status="in-progress",
                    phone_number=job["phone_number"],
                )
                db.add(call_record)

            logger.info(
                f"Successfully executed call job {job['id']}, Vapi call ID: {call_response['id']}"
            )

        except Exception as e:
            logger.error(f"Failed to execute call job {job['id']}: {e}")
            raise

    async def _handle_job_failure(self, job_data: str, error: str):
        """Handle failed job with retry logic."""
        try:
            job = json.loads(job_data)
            job["retry_count"] += 1

            if job["retry_count"] < job["max_retries"]:
                # Retry with exponential backoff
                delay = 60 * (2 ** job["retry_count"])  # 60s, 120s, 240s
                execute_at = datetime.utcnow() + timedelta(seconds=delay)

                redis_client = await get_redis_client()
                await redis_client.zadd(
                    f"{self.queue_name}:delayed",
                    {json.dumps(job): execute_at.timestamp()},
                )

                logger.info(
                    f"Retrying job {job['id']} in {delay} seconds (attempt {job['retry_count']})"
                )
            else:
                # Max retries exceeded, move to failed queue
                redis_client = await get_redis_client()
                await redis_client.lpush(
                    f"{self.queue_name}:failed",
                    json.dumps(
                        {
                            **job,
                            "failed_at": datetime.utcnow().isoformat(),
                            "error": error,
                        }
                    ),
                )

                logger.error(
                    f"Job {job['id']} failed permanently after {job['retry_count']} retries"
                )

            # Remove from delayed queue
            await redis_client.zrem(f"{self.queue_name}:delayed", job_data)

        except Exception as e:
            logger.error(f"Error handling job failure: {e}")


class ScheduleWorker:
    """Worker for managing scheduled calls."""

    def __init__(self):
        self.queue = VoiceCallQueue()
        self.check_interval = config.SCHEDULER_CHECK_INTERVAL_SECONDS
        self.running = False

    async def start(self):
        """Start the schedule worker."""
        self.running = True
        logger.info("Schedule worker started")

        while self.running:
            try:
                await self._check_schedules()
                await self.queue.process_delayed_jobs()
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in schedule worker: {e}")
                await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the schedule worker."""
        self.running = False
        logger.info("Schedule worker stopped")

    async def _check_schedules(self):
        """Check for schedules that need to be executed."""
        try:
            with get_db_session() as db:
                current_time = datetime.utcnow()

                # Find schedules ready to run
                schedules = (
                    db.query(VoiceSchedule)
                    .filter(
                        VoiceSchedule.is_active == True,
                        VoiceSchedule.next_run_at <= current_time,
                    )
                    .all()
                )

                for schedule in schedules:
                    await self.queue.enqueue_scheduled_call(schedule.id)

        except Exception as e:
            logger.error(f"Error checking schedules: {e}")


# Global instances
voice_queue = VoiceCallQueue()
schedule_worker = ScheduleWorker()
