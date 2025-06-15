"""
Gamification Service API
Handles user rewards, badges, quests, streaks, XP management, and reflections.
SECURE: All endpoints use JWT authentication - users can only access their own data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
import uuid

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

# Import database
from .database import get_db
from .models import Reflection, Quest, Badge, UserBadge, UserQuest
from .services import (
    GamificationService,
    ReflectionService,
    QuestService,
    BadgeService,
    StreakService,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/gamification", tags=["gamification"])

# Initialize services
gamification_service = GamificationService()
reflection_service = ReflectionService()
quest_service = QuestService()
badge_service = BadgeService()
streak_service = StreakService()


# Pydantic models for API (user_id always comes from JWT)
class ReflectionRequest(BaseModel):
    mood: str = Field(..., description="User's mood")
    note: str = Field(..., description="Reflection note")
    tags: List[str] = Field(..., description="Tags for the reflection")


class ReflectionResponse(BaseModel):
    id: str
    mood: str
    note: str
    tags: List[str]
    created_at: str


class QuestRequest(BaseModel):
    title: str = Field(..., description="Quest title")
    description: Optional[str] = Field(None, description="Quest description")
    time_frame: str = Field(..., description="daily, weekly, monthly, or one_time")
    frequency: int = Field(..., description="Required frequency to complete")
    xp_reward: int = Field(..., description="XP reward for completion")


class QuestResponse(BaseModel):
    id: str
    key: str
    title: str
    description: Optional[str]
    type: str
    frequency: int
    time_frame: str
    xp_reward: int
    progress: Dict[str, Any]
    created_at: str


class BadgeResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    threshold_type: str
    threshold_value: int
    xp_award: int
    unlocked: bool


class StreakStatsResponse(BaseModel):
    currentStreak: int
    weekProgress: float
    monthProgress: float


# 🔐 SECURE GAMIFICATION ENDPOINTS - JWT Authentication Required


@router.post("/reflections", response_model=ReflectionResponse)
async def create_reflection(
    request: ReflectionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new reflection and award XP. JWT secured."""
    try:
        reflection = await reflection_service.create_reflection(
            db=db,
            user_id=user_id,
            mood=request.mood.lower(),
            note=request.note,
            tags=request.tags,
        )

        return ReflectionResponse(
            id=str(reflection.id),
            mood=reflection.mood,
            note=reflection.note,
            tags=reflection.tags,
            created_at=reflection.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error creating reflection for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reflections")
async def get_reflections(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user's reflections. JWT secured."""
    try:
        reflections = await reflection_service.get_user_reflections(
            db=db, user_id=user_id
        )

        return [
            {
                "id": str(r.id),
                "mood": r.mood,
                "note": r.note,
                "tags": r.tags,
                "created_at": r.created_at.isoformat(),
            }
            for r in reflections
        ]

    except Exception as e:
        logger.error(f"Error fetching reflections for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quests")
async def get_user_quests(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user's quests with progress. JWT secured."""
    try:
        quests_data = await quest_service.get_user_quests_with_progress(
            db=db, user_id=user_id
        )

        return quests_data

    except Exception as e:
        logger.error(f"Error fetching quests for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quests", response_model=QuestResponse)
async def create_quest(
    request: QuestRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new user quest. JWT secured."""
    try:
        quest = await quest_service.create_user_quest(
            db=db,
            user_id=user_id,
            title=request.title,
            description=request.description,
            time_frame=request.time_frame,
            frequency=request.frequency,
            xp_reward=request.xp_reward,
        )

        return QuestResponse(
            id=str(quest.id),
            key=quest.key,
            title=quest.title,
            description=quest.description,
            type=quest.type,
            frequency=quest.frequency,
            time_frame=quest.time_frame,
            xp_reward=quest.xp_reward,
            progress={},
            created_at=quest.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error creating quest for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/quests/{quest_id}/complete")
async def complete_quest(
    quest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Complete a user quest and award XP. JWT secured."""
    try:
        result = await quest_service.complete_quest(
            db=db, user_id=user_id, quest_id=quest_id
        )

        return result

    except Exception as e:
        logger.error(f"Error completing quest {quest_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/badges")
async def get_user_badges(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user's badges grouped by type. JWT secured."""
    try:
        badges_data = await badge_service.get_badges_grouped_by_type(
            db=db, user_id=user_id
        )

        return badges_data

    except Exception as e:
        logger.error(f"Error fetching badges for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streak-stats", response_model=StreakStatsResponse)
async def get_streak_stats(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get user's streak statistics. JWT secured."""
    try:
        stats = await streak_service.get_streak_stats(db=db, user_id=user_id)

        return StreakStatsResponse(
            currentStreak=stats["current_streak"],
            weekProgress=stats["week_progress"],
            monthProgress=stats["month_progress"],
        )

    except Exception as e:
        logger.error(f"Error fetching streak stats for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_user_stats(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get comprehensive user gamification stats. JWT secured."""
    try:
        stats = await gamification_service.get_user_stats(db=db, user_id=user_id)

        return stats

    except Exception as e:
        logger.error(f"Error fetching user stats for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reflections/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a user's reflection. JWT secured."""
    try:
        await reflection_service.delete_reflection(
            db=db, user_id=user_id, reflection_id=reflection_id
        )

        return {"message": "Reflection deleted successfully"}

    except Exception as e:
        logger.error(
            f"Error deleting reflection {reflection_id} for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/reflections/{reflection_id}")
async def update_reflection(
    reflection_id: str,
    request: ReflectionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a user's reflection. JWT secured."""
    try:
        reflection = await reflection_service.update_reflection(
            db=db,
            user_id=user_id,
            reflection_id=reflection_id,
            mood=request.mood.lower(),
            note=request.note,
            tags=request.tags,
        )

        return {
            "id": str(reflection.id),
            "mood": reflection.mood,
            "note": reflection.note,
            "tags": reflection.tags,
            "created_at": reflection.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Error updating reflection {reflection_id} for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))
