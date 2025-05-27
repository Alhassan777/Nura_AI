"""
FastAPI router for Voice Service.
Implements the blueprint architecture endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import time

# Import centralized utilities
from utils.voice import (
    store_call_mapping,
    get_customer_id,
    delete_call_mapping,
    get_call_mapping,
)
from utils.redis_client import cache_set, cache_get

from .database import get_db
from .models import VoiceUser, Voice, VoiceCall, VoiceSchedule, CallSummary
from .vapi_client import vapi_client
from .webhook_handler import webhook_handler
from .queue_worker import voice_queue
from .config import config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/voice", tags=["voice"])


# Pydantic models for API
class CreateCallRequest(BaseModel):
    assistant_id: str = Field(..., description="Vapi assistant ID")
    phone_number: Optional[str] = Field(
        None, description="Phone number for outbound calls"
    )
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


class VoiceProcessingResult(BaseModel):
    success: bool
    callId: str
    customerId: Optional[str]
    processingTimeMs: float
    assistantReply: Optional[str] = None
    crisisLevel: Optional[str] = None
    memoryStored: bool = False
    error: Optional[str] = None
    timestamp: str
    # Enhanced voice processing metadata
    voiceOptimized: Optional[bool] = None
    wordCount: Optional[int] = None
    estimatedSpeechTime: Optional[float] = None
    vapiDelivery: Optional[Dict[str, Any]] = None
    controlUrlUsed: Optional[str] = None
    requiresImmediateDelivery: Optional[bool] = None


class VoiceWebhookEventRequest(BaseModel):
    event: Dict[str, Any]
    callId: str
    receivedAt: str
    source: str = "vapi_webhook"


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


# Authentication dependency (simplified for now)
async def get_current_user(request: Request) -> str:
    """
    Extract user ID from request.
    In production, this would validate JWT tokens.
    """
    # For now, extract from header or use demo user
    user_id = request.headers.get("X-User-ID", "demo-user-123")
    return user_id


# Voice catalogue endpoints
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


# Call management endpoints
@router.post("/calls/browser")
async def start_browser_call(
    request: CreateCallRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a browser call (returns configuration for Web SDK).
    This doesn't create the call directly - the frontend SDK does that.
    """
    try:
        # Validate assistant exists
        voice = (
            db.query(Voice)
            .filter(Voice.assistant_id == request.assistant_id, Voice.is_active == True)
            .first()
        )

        if not voice:
            raise HTTPException(status_code=400, detail="Invalid assistant ID")

        # Return configuration for frontend
        return {
            "assistantId": request.assistant_id,
            "metadata": {"userId": user_id, "channel": "browser", **request.metadata},
            "publicKey": config.VAPI_PUBLIC_KEY,
        }

    except Exception as e:
        logger.error(f"Error starting browser call: {e}")
        raise HTTPException(status_code=500, detail="Failed to start browser call")


@router.post("/calls/phone")
async def create_phone_call(
    request: CreateCallRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an outbound phone call."""
    try:
        if not request.phone_number:
            raise HTTPException(
                status_code=400, detail="Phone number required for phone calls"
            )

        # Validate assistant exists
        voice = (
            db.query(Voice)
            .filter(Voice.assistant_id == request.assistant_id, Voice.is_active == True)
            .first()
        )

        if not voice:
            raise HTTPException(status_code=400, detail="Invalid assistant ID")

        # Get user details
        user = db.query(VoiceUser).filter(VoiceUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Enqueue the call
        job_id = await voice_queue.enqueue_call(
            user_id=user_id,
            assistant_id=request.assistant_id,
            phone_number=request.phone_number,
            metadata=request.metadata,
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Call has been queued for processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating phone call: {e}")
        raise HTTPException(status_code=500, detail="Failed to create phone call")


@router.get("/calls", response_model=List[CallResponse])
async def list_calls(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's calls."""
    calls = (
        db.query(VoiceCall)
        .filter(VoiceCall.user_id == user_id)
        .order_by(VoiceCall.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return calls


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific call details."""
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
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new voice call schedule."""
    try:
        # Validate assistant exists
        voice = (
            db.query(Voice)
            .filter(Voice.assistant_id == request.assistant_id, Voice.is_active == True)
            .first()
        )

        if not voice:
            raise HTTPException(status_code=400, detail="Invalid assistant ID")

        # Validate cron expression
        from croniter import croniter

        if not croniter.is_valid(request.cron_expression):
            raise HTTPException(status_code=400, detail="Invalid cron expression")

        # Calculate next run time
        cron = croniter(request.cron_expression, datetime.utcnow())
        next_run = cron.get_next(datetime)

        # Create schedule
        schedule = VoiceSchedule(
            user_id=user_id,
            assistant_id=request.assistant_id,
            name=request.name,
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            next_run_at=next_run,
            custom_metadata=request.metadata,
        )

        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    user_id: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List user's schedules."""
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
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a schedule."""
    schedule = (
        db.query(VoiceSchedule)
        .filter(VoiceSchedule.id == schedule_id, VoiceSchedule.user_id == user_id)
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    try:
        # Validate cron expression
        from croniter import croniter

        if not croniter.is_valid(request.cron_expression):
            raise HTTPException(status_code=400, detail="Invalid cron expression")

        # Update schedule
        schedule.name = request.name
        schedule.assistant_id = request.assistant_id
        schedule.cron_expression = request.cron_expression
        schedule.timezone = request.timezone
        schedule.custom_metadata = request.metadata

        # Recalculate next run time
        cron = croniter(request.cron_expression, datetime.utcnow())
        schedule.next_run_at = cron.get_next(datetime)

        db.commit()
        return {"message": "Schedule updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a schedule."""
    schedule = (
        db.query(VoiceSchedule)
        .filter(VoiceSchedule.id == schedule_id, VoiceSchedule.user_id == user_id)
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()

    return {"message": "Schedule deleted successfully"}


# Summary endpoints
@router.get("/summaries", response_model=List[SummaryResponse])
async def list_summaries(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's call summaries."""
    summaries = (
        db.query(CallSummary)
        .filter(CallSummary.user_id == user_id)
        .order_by(CallSummary.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return summaries


@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific call summary."""
    summary = (
        db.query(CallSummary)
        .filter(CallSummary.id == summary_id, CallSummary.user_id == user_id)
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


# Voice processing endpoint (for memory service integration)
@router.post("/process-event", response_model=VoiceProcessingResult)
async def process_voice_webhook_event(request: VoiceWebhookEventRequest):
    """Process voice webhook events from Vapi - the core voice processing pipeline."""
    start_time = time.time()

    try:
        # Extract event details
        event = request.event
        call_id = request.callId
        event_type = event.get("type") or event.get("eventType")

        logger.info(f"🎯 Processing voice event: {event_type} for call {call_id}")

        # Get customer ID from call mapping
        customer_id = await get_customer_id(call_id)
        if not customer_id:
            logger.warning(f"No customer mapping found for call {call_id}")
            processing_time = (time.time() - start_time) * 1000

            return VoiceProcessingResult(
                success=False,
                callId=call_id,
                customerId=None,
                processingTimeMs=processing_time,
                error="Customer mapping not found for call",
                timestamp=datetime.utcnow().isoformat(),
            )

        logger.info(f"📋 Found customer {customer_id} for call {call_id}")

        # For now, return basic processing result
        # The actual processing logic would integrate with memory service
        processing_time = (time.time() - start_time) * 1000

        return VoiceProcessingResult(
            success=True,
            callId=call_id,
            customerId=customer_id,
            processingTimeMs=processing_time,
            assistantReply="Voice processing completed",
            crisisLevel="SUPPORT",
            memoryStored=False,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Voice processing failed for call {call_id}: {str(e)}")

        return VoiceProcessingResult(
            success=False,
            callId=call_id,
            customerId=customer_id if "customer_id" in locals() else None,
            processingTimeMs=processing_time,
            error=str(e),
            timestamp=datetime.utcnow().isoformat(),
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


# Webhook endpoint
@router.post("/webhook")
async def handle_vapi_webhook(request: Request):
    """
    Handle incoming Vapi webhooks.
    This processes call events and stores summaries.
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("x-vapi-signature", "")

        # Verify signature
        if not webhook_handler.verify_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON payload
        payload = await request.json()

        # Process webhook
        success = await webhook_handler.handle_webhook(payload, signature)

        if success:
            return JSONResponse(content={"status": "success"}, status_code=200)
        else:
            return JSONResponse(content={"status": "error"}, status_code=400)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        # Always return 200 to Vapi to avoid retries
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=200
        )


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


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "voice",
    }
