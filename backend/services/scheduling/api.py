"""
API endpoints for Scheduling Service.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import Schedule, ScheduleType, ReminderMethod
from .scheduler import ScheduleManager
from .database import get_db

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])


class CreateScheduleRequest(BaseModel):
    name: str = Field(..., description="Schedule name")
    description: Optional[str] = Field(None, description="Purpose and focus")
    schedule_type: ScheduleType = Field(..., description="Type of checkup")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field("UTC", description="Timezone for the schedule")
    reminder_method: ReminderMethod = Field(..., description="How to remind the user")
    phone_number: Optional[str] = Field(None, description="Phone number for call/SMS")
    email: Optional[str] = Field(None, description="Email for email reminders")
    assistant_id: Optional[str] = Field(
        None, description="Assistant ID for voice checkups"
    )
    context_summary: Optional[str] = Field(None, description="Why this was scheduled")
    custom_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional data"
    )


class ScheduleResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    schedule_type: ScheduleType
    cron_expression: str
    timezone: str
    next_run_at: datetime
    last_run_at: Optional[datetime]
    reminder_method: ReminderMethod
    phone_number: Optional[str]
    email: Optional[str]
    assistant_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    context_summary: Optional[str]
    custom_metadata: Optional[Dict[str, Any]]


@router.post("/schedules", response_model=Dict[str, str])
async def create_schedule(
    request: CreateScheduleRequest,
    user_id: str,  # This would come from authentication in a real app
):
    """Create a new schedule for a user."""
    try:
        schedule_id = ScheduleManager.create_schedule(
            user_id=user_id,
            name=request.name,
            description=request.description,
            schedule_type=request.schedule_type,
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            reminder_method=request.reminder_method,
            phone_number=request.phone_number,
            email=request.email,
            assistant_id=request.assistant_id,
            context_summary=request.context_summary,
            custom_metadata=request.custom_metadata,
        )

        if not schedule_id:
            raise HTTPException(status_code=500, detail="Failed to create schedule")

        return {"message": "Schedule created successfully", "schedule_id": schedule_id}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create schedule: {str(e)}"
        )


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    user_id: str,  # This would come from authentication in a real app
    active_only: bool = True,
):
    """List user's schedules."""
    try:
        schedules = ScheduleManager.get_user_schedules(user_id, active_only)
        return schedules
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get schedules: {str(e)}"
        )


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: CreateScheduleRequest,
    user_id: str,  # This would come from authentication in a real app
):
    """Update a schedule."""
    try:
        success = ScheduleManager.update_schedule(
            schedule_id=schedule_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            schedule_type=request.schedule_type,
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            reminder_method=request.reminder_method,
            phone_number=request.phone_number,
            email=request.email,
            assistant_id=request.assistant_id,
            context_summary=request.context_summary,
            custom_metadata=request.custom_metadata,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {"message": "Schedule updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update schedule: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user_id: str,  # This would come from authentication in a real app
):
    """Delete a schedule."""
    try:
        success = ScheduleManager.delete_schedule(schedule_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {"message": "Schedule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete schedule: {str(e)}"
        )


@router.patch("/schedules/{schedule_id}/deactivate")
async def deactivate_schedule(
    schedule_id: str,
    user_id: str,  # This would come from authentication in a real app
):
    """Deactivate a schedule."""
    try:
        success = ScheduleManager.deactivate_schedule(schedule_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {"message": "Schedule deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to deactivate schedule: {str(e)}"
        )


@router.get("/schedules/due")
async def get_due_schedules():
    """Get all schedules that are due to run (internal endpoint)."""
    try:
        schedules = ScheduleManager.get_due_schedules()
        return schedules
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get due schedules: {str(e)}"
        )
