"""
FastAPI router for Voice Service.
Implements the blueprint architecture endpoints.
SECURE: User-specific endpoints use JWT authentication - users can only access their own voice data.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import time
from fastapi.security import HTTPBearer
import os
import aiohttp

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

# Import centralized utilities
from utils.voice import (
    store_call_mapping,
    get_customer_id,
    delete_call_mapping,
    get_call_mapping,
)
from utils.redis_client import cache_set, cache_get

from .database import get_db
from models import Voice, VoiceCall, VoiceSchedule, CallSummary
from .vapi_client import vapi_client
from .vapi_webhook_router import vapi_webhook_router
from .queue_worker import voice_queue
from .config import config
from .user_integration import VoiceUserIntegration
from .vapi_client import VapiClient
from .scheduling_integration import SchedulingIntegration

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/voice", tags=["voice"])
security = HTTPBearer()

# Initialize services
vapi_client = VapiClient()
scheduling_integration = SchedulingIntegration()


# Pydantic models for API
class CreateCallRequest(BaseModel):
    assistant_id: str = Field(..., description="Vapi assistant ID")
    phone_number: Optional[str] = Field(
        None, description="Phone number for outbound calls"
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BrowserCallRequest(BaseModel):
    assistant_id: str = Field(..., description="Vapi assistant ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateScheduleRequest(BaseModel):
    name: str = Field(..., description="Schedule name")
    assistant_id: str = Field(..., description="Vapi assistant ID")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field(default="UTC", description="Timezone")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VoiceMappingRequest(BaseModel):
    callId: str
    customerId: str
    mode: str
    phoneNumber: Optional[str] = None


class VoiceResponse(BaseModel):
    id: str
    name: str
    assistant_id: str
    description: Optional[str]
    sample_url: Optional[str]
    is_active: bool
    created_at: datetime


class CallResponse(BaseModel):
    id: str
    vapi_call_id: str
    user_id: str
    assistant_id: str
    channel: str
    status: str
    phone_number: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    cost_total: Optional[str]


class ScheduleResponse(BaseModel):
    id: str
    name: str
    assistant_id: str
    cron_expression: str
    timezone: str
    next_run_at: datetime
    last_run_at: Optional[datetime]
    is_active: bool


class SummaryResponse(BaseModel):
    id: str
    call_id: str
    summary_json: Dict[str, Any]
    sentiment: Optional[str]
    key_topics: Optional[List[str]]
    action_items: Optional[List[str]]
    emotional_state: Optional[str]
    created_at: datetime


# 🔐 PUBLIC ENDPOINTS (No JWT Required) - Webhooks, Health, Admin


# Voice catalogue endpoints (public - for voice selection)
@router.get("/voices", response_model=List[VoiceResponse])
async def list_voices(db: Session = Depends(get_db)):
    """List available voices/assistants."""
    voices = db.query(Voice).filter(Voice.is_active == True).all()
    return voices


@router.get("/voices/{voice_id}", response_model=VoiceResponse)
async def get_voice(voice_id: str, db: Session = Depends(get_db)):
    """Get specific voice details."""
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


# 🔐 SECURE USER-SPECIFIC VOICE ENDPOINTS - JWT Authentication Required


# Call management endpoints
@router.post("/calls/browser")
async def initiate_browser_call(
    request: BrowserCallRequest, user_id: str = Depends(get_current_user_id)
):
    """Initiate a browser-based voice call. JWT secured - user manages their own calls."""
    try:
        # Get user data from normalized system
        user_data = await VoiceUserIntegration.get_user_for_voice(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Record voice activity
        await VoiceUserIntegration.record_voice_activity(
            user_id,
            "browser_call_initiated",
            {"assistant_id": request.assistant_id},
        )

        # Return configuration for frontend
        return {
            "assistantId": request.assistant_id,
            "metadata": {
                "userId": user_id,
                "channel": "browser",
                **request.metadata,
            },
            "publicKey": config.VAPI_PUBLIC_KEY,
        }

    except Exception as e:
        logger.error(f"Error starting browser call for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start browser call")


@router.post("/calls/phone")
async def create_phone_call(
    request: CreateCallRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a phone call. JWT secured - user creates their own calls."""
    try:
        # Create call record
        call = VoiceCall(
            user_id=user_id,
            assistant_id=request.assistant_id,
            channel="phone",
            status="initializing",
            phone_number=request.phone_number,
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        # Initiate call with Vapi
        result = await vapi_client.create_call(
            assistant_id=request.assistant_id,
            phone_number=request.phone_number,
            metadata={
                "userId": user_id,
                "callId": call.id,
                **request.metadata,
            },
        )

        # Update call with Vapi ID
        call.vapi_call_id = result.get("id")
        call.status = "connecting"
        db.commit()

        logger.info(f"Created phone call {call.id} for user {user_id}")
        return {"call_id": call.id, "vapi_call_id": call.vapi_call_id}

    except Exception as e:
        logger.error(f"Error creating phone call for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create phone call")


@router.get("/calls", response_model=List[CallResponse])
async def list_calls(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's calls. JWT secured - user can only see their own calls."""
    calls = (
        db.query(VoiceCall)
        .filter(VoiceCall.user_id == user_id)
        .order_by(VoiceCall.started_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return calls


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get specific call details. JWT secured - user can only access their own calls."""
    call = (
        db.query(VoiceCall)
        .filter(VoiceCall.id == call_id, VoiceCall.user_id == user_id)
        .first()
    )
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


# Schedule management endpoints
@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: CreateScheduleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a voice schedule via scheduling service API. JWT secured - user creates their own schedules."""
    try:
        # Prepare request for scheduling service
        schedule_request = {
            "name": request.name,
            "description": f"Voice assistant schedule: {request.name}",
            "schedule_type": "voice_checkup",
            "cron_expression": request.cron_expression,
            "timezone": request.timezone,
            "reminder_method": "call",  # Default for voice schedules
            "assistant_id": request.assistant_id,
            "custom_metadata": {
                "created_via": "voice_api",
                "voice_assistant_id": request.assistant_id,
                **request.metadata,
            },
        }

        # Call scheduling service API
        scheduling_api_base = config.get_api_endpoint("scheduling")
        async with aiohttp.ClientSession() as session:
            url = f"{scheduling_api_base}/schedules"
            async with session.post(
                url,
                json=schedule_request,
                params={"user_id": user_id},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    schedule_id = result.get("schedule_id")

                    # Create local voice schedule record for compatibility
                    voice_schedule = VoiceSchedule(
                        id=schedule_id,  # Use same ID as scheduling service
                        user_id=user_id,
                        name=request.name,
                        assistant_id=request.assistant_id,
                        cron_expression=request.cron_expression,
                        timezone=request.timezone,
                        next_run_at=datetime.fromisoformat(
                            result.get("next_run_at").replace("Z", "+00:00")
                        ),
                        metadata=request.metadata,
                    )
                    db.add(voice_schedule)
                    db.commit()
                    db.refresh(voice_schedule)

                    logger.info(
                        f"Created voice schedule {schedule_id} for user {user_id}"
                    )
                    return voice_schedule
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Scheduling service error: {response.status} - {error_text}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create schedule via scheduling service",
                    )

    except aiohttp.ClientError as e:
        logger.error(f"Error calling scheduling service: {e}")
        raise HTTPException(status_code=503, detail="Scheduling service unavailable")
    except Exception as e:
        logger.error(f"Error creating schedule for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """List user's voice schedules via scheduling service API. JWT secured - user can only see their own schedules."""
    try:
        # Call scheduling service API
        scheduling_api_base = config.get_api_endpoint("scheduling")
        async with aiohttp.ClientSession() as session:
            url = f"{scheduling_api_base}/schedules"
            async with session.get(
                url,
                params={"user_id": user_id, "schedule_type": "voice_checkup"},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status == 200:
                    schedules_data = await response.json()

                    # Convert to voice schedule format
                    voice_schedules = []
                    for schedule_data in schedules_data:
                        voice_schedule = ScheduleResponse(
                            id=schedule_data["id"],
                            name=schedule_data["name"],
                            assistant_id=schedule_data.get("assistant_id", ""),
                            cron_expression=schedule_data["cron_expression"],
                            timezone=schedule_data["timezone"],
                            next_run_at=datetime.fromisoformat(
                                schedule_data["next_run_at"].replace("Z", "+00:00")
                            ),
                            last_run_at=(
                                datetime.fromisoformat(
                                    schedule_data["last_run_at"].replace("Z", "+00:00")
                                )
                                if schedule_data.get("last_run_at")
                                else None
                            ),
                            is_active=schedule_data["is_active"],
                        )
                        voice_schedules.append(voice_schedule)

                    return voice_schedules
                else:
                    logger.error(f"Scheduling service error: {response.status}")
                    # Fallback to local database
                    schedules = (
                        db.query(VoiceSchedule)
                        .filter(VoiceSchedule.user_id == user_id)
                        .order_by(VoiceSchedule.created_at.desc())
                        .all()
                    )
                    return schedules

    except aiohttp.ClientError as e:
        logger.error(f"Error calling scheduling service: {e}")
        # Fallback to local database
        schedules = (
            db.query(VoiceSchedule)
            .filter(VoiceSchedule.user_id == user_id)
            .order_by(VoiceSchedule.created_at.desc())
            .all()
        )
        return schedules


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: CreateScheduleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a voice schedule via scheduling service API. JWT secured - user can only update their own schedules."""
    try:
        # Prepare update request
        update_request = {
            "name": request.name,
            "description": f"Voice assistant schedule: {request.name}",
            "cron_expression": request.cron_expression,
            "timezone": request.timezone,
            "assistant_id": request.assistant_id,
            "custom_metadata": {
                "updated_via": "voice_api",
                "voice_assistant_id": request.assistant_id,
                **request.metadata,
            },
        }

        # Call scheduling service API
        scheduling_api_base = config.get_api_endpoint("scheduling")
        async with aiohttp.ClientSession() as session:
            url = f"{scheduling_api_base}/schedules/{schedule_id}"
            async with session.put(
                url,
                json=update_request,
                params={"user_id": user_id},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status == 200:
                    # Update local voice schedule record
                    schedule = (
                        db.query(VoiceSchedule)
                        .filter(
                            VoiceSchedule.id == schedule_id,
                            VoiceSchedule.user_id == user_id,
                        )
                        .first()
                    )
                    if schedule:
                        schedule.name = request.name
                        schedule.assistant_id = request.assistant_id
                        schedule.cron_expression = request.cron_expression
                        schedule.timezone = request.timezone
                        schedule.metadata = request.metadata
                        db.commit()

                    logger.info(
                        f"Updated voice schedule {schedule_id} for user {user_id}"
                    )
                    return {"success": True, "message": "Schedule updated successfully"}
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail="Schedule not found")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Scheduling service error: {response.status} - {error_text}"
                    )
                    raise HTTPException(
                        status_code=500, detail="Failed to update schedule"
                    )

    except aiohttp.ClientError as e:
        logger.error(f"Error calling scheduling service: {e}")
        raise HTTPException(status_code=503, detail="Scheduling service unavailable")
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a voice schedule via scheduling service API. JWT secured - user can only delete their own schedules."""
    try:
        # Call scheduling service API
        scheduling_api_base = config.get_api_endpoint("scheduling")
        async with aiohttp.ClientSession() as session:
            url = f"{scheduling_api_base}/schedules/{schedule_id}"
            async with session.delete(
                url,
                params={"user_id": user_id},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status == 200:
                    # Delete local voice schedule record
                    schedule = (
                        db.query(VoiceSchedule)
                        .filter(
                            VoiceSchedule.id == schedule_id,
                            VoiceSchedule.user_id == user_id,
                        )
                        .first()
                    )
                    if schedule:
                        db.delete(schedule)
                        db.commit()

                    logger.info(
                        f"Deleted voice schedule {schedule_id} for user {user_id}"
                    )
                    return {"success": True, "message": "Schedule deleted successfully"}
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail="Schedule not found")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Scheduling service error: {response.status} - {error_text}"
                    )
                    raise HTTPException(
                        status_code=500, detail="Failed to delete schedule"
                    )

    except aiohttp.ClientError as e:
        logger.error(f"Error calling scheduling service: {e}")
        raise HTTPException(status_code=503, detail="Scheduling service unavailable")
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


# Summary endpoints
@router.get("/summaries", response_model=List[SummaryResponse])
async def list_summaries(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's call summaries. JWT secured - user can only see their own summaries."""
    summaries = (
        db.query(CallSummary)
        .join(VoiceCall)
        .filter(VoiceCall.user_id == user_id)
        .order_by(CallSummary.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return summaries


@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get specific call summary. JWT secured - user can only access their own summaries."""
    summary = (
        db.query(CallSummary)
        .join(VoiceCall)
        .filter(CallSummary.id == summary_id, VoiceCall.user_id == user_id)
        .first()
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


# Call mapping endpoints
@router.post("/mapping")
async def store_voice_mapping(request: VoiceMappingRequest):
    """Store callId to customerId mapping in Redis."""
    try:
        # Use centralized voice utility
        success = await store_call_mapping(
            call_id=request.callId,
            customer_id=request.customerId,
            mode=request.mode,
            phone_number=request.phoneNumber,
            ttl_minutes=30,
        )

        if success:
            logger.info(
                f"Stored voice mapping: {request.callId} -> {request.customerId}"
            )
            return {
                "success": True,
                "callId": request.callId,
                "customerId": request.customerId,
                "ttl_minutes": 30,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store mapping")

    except Exception as e:
        logger.error(f"Failed to store voice mapping: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to store mapping: {str(e)}"
        )


@router.get("/mapping/{call_id}")
async def get_voice_mapping(call_id: str):
    """Get customerId from callId."""
    try:
        # Use centralized voice utility
        customer_id = await get_customer_id(call_id)

        if not customer_id:
            raise HTTPException(status_code=404, detail="Call mapping not found")

        # Get full mapping data for additional details
        mapping_data = await get_call_mapping(call_id)

        if mapping_data:
            return {
                "callId": call_id,
                "customerId": mapping_data["customerId"],
                "mode": mapping_data.get("mode"),
                "phoneNumber": mapping_data.get("phoneNumber"),
                "timestamp": mapping_data.get("timestamp"),
            }
        else:
            return {
                "callId": call_id,
                "customerId": customer_id,
            }

    except Exception as e:
        logger.error(f"Failed to get voice mapping for {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mapping: {str(e)}")


@router.delete("/mapping/{call_id}")
async def delete_voice_mapping_endpoint(call_id: str):
    """Delete callId mapping (cleanup)."""
    try:
        # Use centralized voice utility
        success = await delete_call_mapping(call_id)

        if not success:
            raise HTTPException(status_code=404, detail="Call mapping not found")

        logger.info(f"Deleted voice mapping for call {call_id}")
        return {"success": True, "deleted": True}

    except Exception as e:
        logger.error(f"Failed to delete voice mapping for {call_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete mapping: {str(e)}"
        )


# Metrics endpoints
@router.get("/metrics/latency")
async def get_voice_latency_metrics(date: str = None):
    """Get voice processing latency metrics for a specific date."""
    try:
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        metrics_key = f"voice_metrics:latency:{date}"

        # Use centralized Redis utilities
        raw_metrics = await cache_get(metrics_key, parse_json=False)

        if not raw_metrics:
            return {"date": date, "count": 0, "average_latency_ms": 0, "metrics": []}

        # Handle both single metric and list of metrics
        import json

        if isinstance(raw_metrics, str):
            try:
                metrics = [json.loads(raw_metrics)]
            except json.JSONDecodeError:
                return {
                    "date": date,
                    "count": 0,
                    "average_latency_ms": 0,
                    "metrics": [],
                }
        elif isinstance(raw_metrics, list):
            metrics = []
            for raw_metric in raw_metrics:
                try:
                    if isinstance(raw_metric, str):
                        metric = json.loads(raw_metric)
                    else:
                        metric = raw_metric
                    metrics.append(metric)
                except json.JSONDecodeError:
                    continue
        else:
            metrics = [raw_metrics] if raw_metrics else []

        if not metrics:
            return {"date": date, "count": 0, "average_latency_ms": 0, "metrics": []}

        total_time = sum(metric.get("processing_time_ms", 0) for metric in metrics)

        return {
            "date": date,
            "count": len(metrics),
            "average_latency_ms": round(total_time / len(metrics), 2),
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Failed to get latency metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints for voice management
@router.post("/admin/voices")
async def create_voice(
    name: str,
    assistant_id: str,
    description: Optional[str] = None,
    sample_url: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new voice (admin only)."""
    try:
        # Validate assistant exists in Vapi
        assistant = await vapi_client.get_assistant(assistant_id)

        voice = Voice(
            name=name,
            assistant_id=assistant_id,
            description=description,
            sample_url=sample_url,
        )

        db.add(voice)
        db.commit()
        db.refresh(voice)

        return voice

    except Exception as e:
        logger.error(f"Error creating voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create voice")


@router.get("/users/{user_id}")
async def get_voice_user(user_id: str):
    """Get user data for voice service (using normalized user system)."""
    try:
        user_data = await VoiceUserIntegration.get_user_for_voice(user_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "user": user_data}

    except Exception as e:
        logger.error(f"Error getting voice user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
