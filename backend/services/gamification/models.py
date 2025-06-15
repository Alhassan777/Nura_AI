"""
Database models for Gamification Service.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Reflection(Base):
    """User reflection model."""

    __tablename__ = "reflections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    mood = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Quest(Base):
    """Quest model."""

    __tablename__ = "quests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # "system" or "user"
    user_id = Column(String, nullable=True, index=True)  # Null for system quests
    frequency = Column(Integer, nullable=False, default=1)
    time_frame = Column(
        String, nullable=False
    )  # "daily", "weekly", "monthly", "one_time"
    xp_reward = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserQuest(Base):
    """User quest progress model."""

    __tablename__ = "user_quests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    quest_id = Column(UUID(as_uuid=True), ForeignKey("quests.id"), nullable=False)
    status = Column(
        String, default="IN_PROGRESS"
    )  # "NOT_STARTED", "IN_PROGRESS", "COMPLETED"
    count = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quest = relationship("Quest", backref="user_quests")


class Badge(Base):
    """Badge model."""

    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    threshold_type = Column(
        String, nullable=False
    )  # "reflections", "streak", "friends", etc.
    threshold_value = Column(Integer, nullable=False)
    xp_award = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBadge(Base):
    """User badge model."""

    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    badge = relationship("Badge", backref="user_badges")
