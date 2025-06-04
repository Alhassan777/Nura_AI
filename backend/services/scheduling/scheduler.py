"""
Schedule Manager for handling checkup schedules.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from croniter import croniter

from models import Schedule, ScheduleType, ReminderMethod, ScheduleExecution
from .database import get_db

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Manages creation and execution of schedules for both chat and voice checkups."""

    @staticmethod
    def create_schedule(
        user_id: str,
        name: str,
        description: str,
        schedule_type: ScheduleType,
        cron_expression: str,
        reminder_method: ReminderMethod,
        timezone: str = "UTC",
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        assistant_id: Optional[str] = None,
        context_summary: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a new schedule.

        Returns:
            Schedule ID if successful, None if failed
        """
        try:
            with get_db() as db:
                # Calculate next run time
                cron = croniter(cron_expression, datetime.utcnow())
                next_run_at = cron.get_next(datetime)

                # Create schedule
                schedule = Schedule(
                    user_id=user_id,
                    name=name,
                    description=description,
                    schedule_type=schedule_type,
                    cron_expression=cron_expression,
                    timezone=timezone,
                    next_run_at=next_run_at,
                    reminder_method=reminder_method,
                    phone_number=phone_number,
                    email=email,
                    assistant_id=assistant_id,
                    context_summary=context_summary,
                    custom_metadata=custom_metadata,
                )

                db.add(schedule)
                db.flush()  # Get the ID

                logger.info(f"Created schedule {schedule.id} for user {user_id}")
                return schedule.id

        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return None

    @staticmethod
    def get_user_schedules(user_id: str, active_only: bool = True) -> List[Schedule]:
        """Get all schedules for a user."""
        try:
            with get_db() as db:
                query = db.query(Schedule).filter(Schedule.user_id == user_id)

                if active_only:
                    query = query.filter(Schedule.is_active == True)

                return query.order_by(Schedule.created_at.desc()).all()

        except Exception as e:
            logger.error(f"Error getting user schedules: {e}")
            return []

    @staticmethod
    def update_schedule(schedule_id: str, user_id: str, **updates) -> bool:
        """Update an existing schedule."""
        try:
            with get_db() as db:
                schedule = (
                    db.query(Schedule)
                    .filter(Schedule.id == schedule_id, Schedule.user_id == user_id)
                    .first()
                )

                if not schedule:
                    logger.warning(
                        f"Schedule {schedule_id} not found for user {user_id}"
                    )
                    return False

                # Update fields
                for field, value in updates.items():
                    if hasattr(schedule, field):
                        setattr(schedule, field, value)

                # Recalculate next run time if cron expression changed
                if "cron_expression" in updates:
                    cron = croniter(schedule.cron_expression, datetime.utcnow())
                    schedule.next_run_at = cron.get_next(datetime)

                schedule.updated_at = datetime.utcnow()

                logger.info(f"Updated schedule {schedule_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False

    @staticmethod
    def delete_schedule(schedule_id: str, user_id: str) -> bool:
        """Delete a schedule."""
        try:
            with get_db() as db:
                schedule = (
                    db.query(Schedule)
                    .filter(Schedule.id == schedule_id, Schedule.user_id == user_id)
                    .first()
                )

                if not schedule:
                    logger.warning(
                        f"Schedule {schedule_id} not found for user {user_id}"
                    )
                    return False

                db.delete(schedule)
                logger.info(f"Deleted schedule {schedule_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False

    @staticmethod
    def deactivate_schedule(schedule_id: str, user_id: str) -> bool:
        """Deactivate a schedule instead of deleting it."""
        try:
            with get_db() as db:
                schedule = (
                    db.query(Schedule)
                    .filter(Schedule.id == schedule_id, Schedule.user_id == user_id)
                    .first()
                )

                if not schedule:
                    logger.warning(
                        f"Schedule {schedule_id} not found for user {user_id}"
                    )
                    return False

                schedule.is_active = False
                schedule.updated_at = datetime.utcnow()

                logger.info(f"Deactivated schedule {schedule_id}")
                return True

        except Exception as e:
            logger.error(f"Error deactivating schedule: {e}")
            return False

    @staticmethod
    def get_due_schedules() -> List[Schedule]:
        """Get all schedules that are due to run."""
        try:
            with get_db() as db:
                now = datetime.utcnow()
                return (
                    db.query(Schedule)
                    .filter(Schedule.is_active == True, Schedule.next_run_at <= now)
                    .all()
                )

        except Exception as e:
            logger.error(f"Error getting due schedules: {e}")
            return []

    @staticmethod
    def log_execution(
        schedule_id: str,
        status: str,
        error_message: Optional[str] = None,
        user_responded: Optional[bool] = None,
        response_time_minutes: Optional[int] = None,
        session_duration_minutes: Optional[int] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log a schedule execution attempt."""
        try:
            with get_db() as db:
                execution = ScheduleExecution(
                    schedule_id=schedule_id,
                    status=status,
                    error_message=error_message,
                    user_responded=user_responded,
                    response_time_minutes=response_time_minutes,
                    session_duration_minutes=session_duration_minutes,
                    execution_metadata=execution_metadata,
                )

                db.add(execution)

                # Update the schedule's last_run_at time
                schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
                if schedule:
                    schedule.last_run_at = datetime.utcnow()

                    # Calculate next run time
                    cron = croniter(schedule.cron_expression, datetime.utcnow())
                    schedule.next_run_at = cron.get_next(datetime)

                logger.info(f"Logged execution for schedule {schedule_id}: {status}")
                return True

        except Exception as e:
            logger.error(f"Error logging execution: {e}")
            return False
