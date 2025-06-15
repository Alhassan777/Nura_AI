"""
Business logic services for Gamification.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from .models import Reflection, Quest, Badge, UserBadge, UserQuest
from models import User  # From shared models
from utils.database import get_db

logger = logging.getLogger(__name__)


class GamificationService:
    """Main gamification service."""

    async def get_user_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user gamification statistics."""
        try:
            # Get user info
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            # Count reflections
            total_reflections = (
                db.query(Reflection).filter(Reflection.user_id == user_id).count()
            )

            # Count completed quests
            completed_quests = (
                db.query(UserQuest)
                .filter(
                    and_(UserQuest.user_id == user_id, UserQuest.status == "COMPLETED")
                )
                .count()
            )

            # Count earned badges
            earned_badges = (
                db.query(UserBadge).filter(UserBadge.user_id == user_id).count()
            )

            return {
                "user_id": user_id,
                "current_streak": user.current_streak or 0,
                "xp": user.xp or 0,
                "freeze_credits": user.freeze_credits or 0,
                "total_reflections": total_reflections,
                "completed_quests": completed_quests,
                "earned_badges": earned_badges,
            }

        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            raise


class ReflectionService:
    """Service for handling reflections."""

    async def create_reflection(
        self, db: Session, user_id: str, mood: str, note: str, tags: List[str]
    ) -> Reflection:
        """Create a new reflection and award XP."""
        try:
            # Create reflection
            reflection = Reflection(
                user_id=user_id,
                mood=mood.lower(),
                note=note,
                tags=tags,
            )

            db.add(reflection)
            db.flush()  # Get the ID

            # Award XP to user (base XP for reflection)
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.xp = (user.xp or 0) + 10  # Base XP for reflection
                user.last_active_at = datetime.utcnow()

            # Update streak (simplified version)
            await self._update_user_streak(db, user_id)

            db.commit()
            return reflection

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating reflection: {str(e)}")
            raise

    async def get_user_reflections(
        self, db: Session, user_id: str, limit: int = 50
    ) -> List[Reflection]:
        """Get user's reflections."""
        return (
            db.query(Reflection)
            .filter(Reflection.user_id == user_id)
            .order_by(desc(Reflection.created_at))
            .limit(limit)
            .all()
        )

    async def delete_reflection(self, db: Session, user_id: str, reflection_id: str):
        """Delete a user's reflection."""
        reflection = (
            db.query(Reflection)
            .filter(and_(Reflection.id == reflection_id, Reflection.user_id == user_id))
            .first()
        )

        if not reflection:
            raise ValueError("Reflection not found")

        db.delete(reflection)
        db.commit()

    async def update_reflection(
        self,
        db: Session,
        user_id: str,
        reflection_id: str,
        mood: str,
        note: str,
        tags: List[str],
    ) -> Reflection:
        """Update a user's reflection."""
        reflection = (
            db.query(Reflection)
            .filter(and_(Reflection.id == reflection_id, Reflection.user_id == user_id))
            .first()
        )

        if not reflection:
            raise ValueError("Reflection not found")

        reflection.mood = mood.lower()
        reflection.note = note
        reflection.tags = tags
        reflection.updated_at = datetime.utcnow()

        db.commit()
        return reflection

    async def _update_user_streak(self, db: Session, user_id: str):
        """Update user streak based on recent activity."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return

            # Simple streak logic - check if user reflected today
            today = datetime.utcnow().date()
            today_reflection = (
                db.query(Reflection)
                .filter(
                    and_(
                        Reflection.user_id == user_id,
                        func.date(Reflection.created_at) == today,
                    )
                )
                .first()
            )

            if today_reflection and user.last_activity:
                last_activity_date = user.last_activity.date()
                if (today - last_activity_date).days == 1:
                    # Consecutive day - increment streak
                    user.current_streak = (user.current_streak or 0) + 1
                elif (today - last_activity_date).days > 1:
                    # Gap - reset streak
                    user.current_streak = 1
            elif today_reflection:
                # First reflection or starting new streak
                user.current_streak = 1

            user.last_activity = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating user streak: {str(e)}")


class QuestService:
    """Service for handling quests."""

    async def get_user_quests_with_progress(
        self, db: Session, user_id: str
    ) -> Dict[str, Any]:
        """Get user's quests with progress information."""
        try:
            # Get system quests
            system_quests = db.query(Quest).filter(Quest.type == "system").all()
            system_quests_with_progress = []

            for quest in system_quests:
                progress = await self._get_quest_progress(db, quest, user_id)
                quest_dict = {
                    "id": str(quest.id),
                    "key": quest.key,
                    "title": quest.title,
                    "description": quest.description,
                    "type": quest.type,
                    "frequency": quest.frequency,
                    "time_frame": quest.time_frame,
                    "xp_reward": quest.xp_reward,
                    "progress": progress,
                    "created_at": quest.created_at.isoformat(),
                }
                system_quests_with_progress.append(quest_dict)

            # Get user quests
            user_quests = (
                db.query(Quest)
                .filter(and_(Quest.type == "user", Quest.user_id == user_id))
                .all()
            )

            user_quests_with_progress = []
            for quest in user_quests:
                progress = await self._get_quest_progress(db, quest, user_id)
                quest_dict = {
                    "id": str(quest.id),
                    "key": quest.key,
                    "title": quest.title,
                    "description": quest.description,
                    "type": quest.type,
                    "frequency": quest.frequency,
                    "time_frame": quest.time_frame,
                    "xp_reward": quest.xp_reward,
                    "progress": progress,
                    "created_at": quest.created_at.isoformat(),
                }
                user_quests_with_progress.append(quest_dict)

            return {
                "systemQuests": system_quests_with_progress,
                "userQuests": user_quests_with_progress,
            }

        except Exception as e:
            logger.error(f"Error getting user quests: {str(e)}")
            raise

    async def create_user_quest(
        self,
        db: Session,
        user_id: str,
        title: str,
        description: Optional[str],
        time_frame: str,
        frequency: int,
        xp_reward: int,
    ) -> Quest:
        """Create a new user quest."""
        try:
            quest = Quest(
                key=f"user_{uuid.uuid4().hex[:8]}",
                title=title,
                description=description,
                type="user",
                user_id=user_id,
                frequency=frequency,
                time_frame=time_frame,
                xp_reward=xp_reward,
            )

            db.add(quest)
            db.commit()
            return quest

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user quest: {str(e)}")
            raise

    async def complete_quest(
        self, db: Session, user_id: str, quest_id: str
    ) -> Dict[str, Any]:
        """Complete a quest and award XP."""
        try:
            # Get quest
            quest = db.query(Quest).filter(Quest.id == quest_id).first()
            if not quest:
                raise ValueError("Quest not found")

            # Check if user can complete this quest
            if quest.type == "user" and quest.user_id != user_id:
                raise ValueError("Not authorized to complete this quest")

            # Get or create user quest progress
            user_quest = (
                db.query(UserQuest)
                .filter(
                    and_(UserQuest.user_id == user_id, UserQuest.quest_id == quest_id)
                )
                .first()
            )

            if not user_quest:
                user_quest = UserQuest(
                    user_id=user_id, quest_id=quest_id, count=0, status="IN_PROGRESS"
                )
                db.add(user_quest)

            # Increment progress
            user_quest.count += 1

            # Check if quest is completed
            if user_quest.count >= quest.frequency:
                user_quest.status = "COMPLETED"
                user_quest.completed_at = datetime.utcnow()

                # Award XP
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.xp = (user.xp or 0) + quest.xp_reward

            db.commit()

            return {
                "quest_id": str(quest_id),
                "status": user_quest.status,
                "count": user_quest.count,
                "required": quest.frequency,
                "xp_awarded": (
                    quest.xp_reward if user_quest.status == "COMPLETED" else 0
                ),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error completing quest: {str(e)}")
            raise

    async def _get_quest_progress(
        self, db: Session, quest: Quest, user_id: str
    ) -> Dict[str, Any]:
        """Get progress for a specific quest."""
        try:
            if quest.key == "reflections":
                # Special handling for reflection quest
                today = datetime.utcnow().date()
                tomorrow = today + timedelta(days=1)

                count = (
                    db.query(Reflection)
                    .filter(
                        and_(
                            Reflection.user_id == user_id,
                            func.date(Reflection.created_at) == today,
                        )
                    )
                    .count()
                )

                completed = count >= quest.frequency

                return {
                    "count": count,
                    "completed": completed,
                    "status": "COMPLETED" if completed else "IN_PROGRESS",
                }

            # General quest progress
            user_quest = (
                db.query(UserQuest)
                .filter(
                    and_(UserQuest.user_id == user_id, UserQuest.quest_id == quest.id)
                )
                .first()
            )

            if not user_quest:
                return {"count": 0, "completed": False, "status": "NOT_STARTED"}

            return {
                "count": user_quest.count,
                "completed": user_quest.status == "COMPLETED",
                "status": user_quest.status,
                "completedAt": (
                    user_quest.completed_at.isoformat()
                    if user_quest.completed_at
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Error getting quest progress: {str(e)}")
            return {"count": 0, "completed": False, "status": "ERROR"}


class BadgeService:
    """Service for handling badges."""

    async def get_badges_grouped_by_type(
        self, db: Session, user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get all badges grouped by type with user unlock status."""
        try:
            # Get all badges
            badges = db.query(Badge).order_by(Badge.threshold_value).all()

            # Get user's unlocked badges
            user_badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()

            unlocked_badge_ids = {str(ub.badge_id) for ub in user_badges}

            # Group badges by threshold type
            grouped = {}
            for badge in badges:
                threshold_type = badge.threshold_type
                if threshold_type not in grouped:
                    grouped[threshold_type] = []

                badge_dict = {
                    "id": str(badge.id),
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "threshold_type": badge.threshold_type,
                    "threshold_value": badge.threshold_value,
                    "xp_award": badge.xp_award,
                    "unlocked": str(badge.id) in unlocked_badge_ids,
                }

                grouped[threshold_type].append(badge_dict)

            return grouped

        except Exception as e:
            logger.error(f"Error getting badges: {str(e)}")
            raise


class StreakService:
    """Service for handling streak statistics."""

    async def get_streak_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get user's streak statistics."""
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            current_streak = user.current_streak or 0

            # Calculate 7-day progress
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            week_reflections = (
                db.query(Reflection)
                .filter(
                    and_(
                        Reflection.user_id == user_id,
                        Reflection.created_at >= seven_days_ago,
                    )
                )
                .count()
            )

            week_progress = min(100, (week_reflections / 7) * 100)

            # Calculate 30-day progress
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            month_reflections = (
                db.query(Reflection)
                .filter(
                    and_(
                        Reflection.user_id == user_id,
                        Reflection.created_at >= thirty_days_ago,
                    )
                )
                .count()
            )

            month_progress = min(100, (month_reflections / 30) * 100)

            return {
                "current_streak": current_streak,
                "week_progress": week_progress,
                "month_progress": month_progress,
            }

        except Exception as e:
            logger.error(f"Error getting streak stats: {str(e)}")
            raise
