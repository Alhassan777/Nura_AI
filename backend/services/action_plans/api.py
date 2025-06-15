"""
Action Plans API - RESTful endpoints for AI-generated action plans.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .service import ActionPlanService
from models import (
    ActionPlan as DBActionPlan,
    ActionStep as DBActionStep,
    ActionSubtask as DBActionSubtask,
)
from utils.database import get_db
from utils.auth import get_current_user_id

import logging

logger = logging.getLogger(__name__)

# Initialize router and service
router = APIRouter(prefix="/action-plans", tags=["action-plans"])
action_plan_service = ActionPlanService()


# Pydantic models for API responses
class ActionSubtask(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[str] = None
    created_at: str
    order_index: int

    class Config:
        from_attributes = True


class ActionStep(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[str] = None
    notes: Optional[str] = None
    subtasks: List[ActionSubtask] = []
    created_at: str
    order_index: int
    time_needed: Optional[str] = None
    difficulty: Optional[str] = None
    purpose: Optional[str] = None
    success_criteria: Optional[str] = None

    class Config:
        from_attributes = True


class ActionPlan(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    plan_type: str
    priority: str = "medium"
    status: str = "active"
    progress_percentage: int = 0
    steps: List[ActionStep] = []
    tags: List[str] = []
    due_date: Optional[str] = None
    created_at: str
    updated_at: str
    generated_by_ai: bool = False
    ai_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Request models
class CreateActionPlanRequest(BaseModel):
    title: str
    description: str
    plan_type: str = Field(
        ..., pattern="^(therapeutic_emotional|personal_achievement|hybrid)$"
    )
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    tags: List[str] = Field(default_factory=list)
    due_date: Optional[str] = None


class UpdateActionPlanRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    plan_type: Optional[str] = Field(
        None, pattern="^(therapeutic_emotional|personal_achievement|hybrid)$"
    )
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(active|completed|paused|deleted)$")
    tags: Optional[List[str]] = None
    due_date: Optional[str] = None


class GenerateActionPlanRequest(BaseModel):
    conversation_context: str
    user_message: str


class AddStepRequest(BaseModel):
    title: str
    description: Optional[str] = None


class AddSubtaskRequest(BaseModel):
    title: str
    description: Optional[str] = None


class UpdateStepStatusRequest(BaseModel):
    completed: bool
    notes: Optional[str] = None


class UpdateSubtaskStatusRequest(BaseModel):
    completed: bool


def _convert_db_to_pydantic(db_plan: DBActionPlan) -> ActionPlan:
    """Convert database model to Pydantic model."""
    steps = []
    for db_step in db_plan.steps:
        subtasks = [
            ActionSubtask(
                id=db_subtask.id,
                title=db_subtask.title,
                description=db_subtask.description,
                completed=db_subtask.completed,
                due_date=(
                    db_subtask.due_date.isoformat() if db_subtask.due_date else None
                ),
                created_at=db_subtask.created_at.isoformat(),
                order_index=db_subtask.order_index,
            )
            for db_subtask in db_step.subtasks
        ]

        steps.append(
            ActionStep(
                id=db_step.id,
                title=db_step.title,
                description=db_step.description,
                completed=db_step.completed,
                due_date=db_step.due_date.isoformat() if db_step.due_date else None,
                notes=db_step.notes,
                subtasks=subtasks,
                created_at=db_step.created_at.isoformat(),
                order_index=db_step.order_index,
                time_needed=db_step.time_needed,
                difficulty=db_step.difficulty,
                purpose=db_step.purpose,
                success_criteria=db_step.success_criteria,
            )
        )

    return ActionPlan(
        id=db_plan.id,
        title=db_plan.title,
        description=db_plan.description,
        plan_type=db_plan.plan_type,
        priority=db_plan.priority,
        status=db_plan.status,
        progress_percentage=db_plan.progress_percentage,
        steps=steps,
        tags=db_plan.tags or [],
        due_date=db_plan.due_date.isoformat() if db_plan.due_date else None,
        created_at=db_plan.created_at.isoformat(),
        updated_at=db_plan.updated_at.isoformat(),
        generated_by_ai=db_plan.generated_by_ai,
        ai_metadata=db_plan.ai_metadata,
    )


# API Endpoints


@router.get("/", response_model=List[ActionPlan])
async def get_action_plans(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get all action plans for the authenticated user."""
    try:
        db_plans = action_plan_service.get_action_plans(user_id, db)
        return [_convert_db_to_pydantic(plan) for plan in db_plans]
    except Exception as e:
        logger.error(f"Error getting action plans for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve action plans")


@router.get("/{plan_id}", response_model=ActionPlan)
async def get_action_plan(
    plan_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific action plan by ID."""
    try:
        db_plan = action_plan_service.get_action_plan(plan_id, user_id, db)
        if not db_plan:
            raise HTTPException(status_code=404, detail="Action plan not found")

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action plan {plan_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve action plan")


@router.post("/", response_model=ActionPlan)
async def create_action_plan(
    request: CreateActionPlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new manual action plan."""
    try:
        db_plan = action_plan_service.create_action_plan(
            user_id=user_id,
            title=request.title,
            description=request.description,
            plan_type=request.plan_type,
            priority=request.priority,
            tags=request.tags,
            db=db,
        )

        return _convert_db_to_pydantic(db_plan)
    except Exception as e:
        logger.error(f"Error creating action plan for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create action plan")


@router.post("/generate", response_model=ActionPlan)
async def generate_action_plan(
    request: GenerateActionPlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate an AI-powered action plan from conversation context."""
    try:
        result = await action_plan_service.generate_action_plan_from_conversation(
            user_id=user_id,
            conversation_context=request.conversation_context,
            user_message=request.user_message,
            db=db,
        )

        if not result or not result.get("should_suggest"):
            raise HTTPException(
                status_code=400,
                detail="Unable to generate action plan from provided context",
            )

        db_plan = result["action_plan"]
        return _convert_db_to_pydantic(db_plan)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating action plan for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate action plan")


@router.put("/{plan_id}", response_model=ActionPlan)
async def update_action_plan(
    plan_id: str,
    request: UpdateActionPlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update an existing action plan."""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}

        db_plan = action_plan_service.update_action_plan(plan_id, user_id, updates, db)
        if not db_plan:
            raise HTTPException(status_code=404, detail="Action plan not found")

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating action plan {plan_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update action plan")


@router.delete("/{plan_id}")
async def delete_action_plan(
    plan_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete an action plan (soft delete)."""
    try:
        success = action_plan_service.delete_action_plan(plan_id, user_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Action plan not found")

        return {"message": "Action plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting action plan {plan_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete action plan")


@router.put("/{plan_id}/steps/{step_id}/status", response_model=ActionPlan)
async def update_step_status(
    plan_id: str,
    step_id: str,
    request: UpdateStepStatusRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update the completion status of an action step."""
    try:
        db_plan = action_plan_service.update_step_status(
            plan_id, step_id, user_id, request.completed, request.notes, db
        )
        if not db_plan:
            raise HTTPException(status_code=404, detail="Action plan or step not found")

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating step {step_id} for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update step status")


@router.put(
    "/{plan_id}/steps/{step_id}/subtasks/{subtask_id}/status", response_model=ActionPlan
)
async def update_subtask_status(
    plan_id: str,
    step_id: str,
    subtask_id: str,
    request: UpdateSubtaskStatusRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update the completion status of a subtask."""
    try:
        db_plan = action_plan_service.update_subtask_status(
            plan_id, step_id, subtask_id, user_id, request.completed, db
        )
        if not db_plan:
            raise HTTPException(
                status_code=404, detail="Action plan, step, or subtask not found"
            )

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subtask {subtask_id} for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update subtask status")


@router.post("/{plan_id}/steps", response_model=ActionPlan)
async def add_step(
    plan_id: str,
    request: AddStepRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a new step to an action plan."""
    try:
        db_plan = action_plan_service.add_step(
            plan_id, user_id, request.title, request.description, db
        )
        if not db_plan:
            raise HTTPException(status_code=404, detail="Action plan not found")

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding step to plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add step")


@router.post("/{plan_id}/steps/{step_id}/subtasks", response_model=ActionPlan)
async def add_subtask(
    plan_id: str,
    step_id: str,
    request: AddSubtaskRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a new subtask to an action step."""
    try:
        db_plan = action_plan_service.add_subtask(
            plan_id, step_id, user_id, request.title, request.description, db
        )
        if not db_plan:
            raise HTTPException(status_code=404, detail="Action plan or step not found")

        return _convert_db_to_pydantic(db_plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding subtask to step {step_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add subtask")
