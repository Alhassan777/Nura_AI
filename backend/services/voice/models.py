"""
Database models for Voice Service.
Separate from memory service models for clean architecture.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Integer,
    JSON,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class VoiceUser(Base):
    """
    User table for voice service.
    Note: This might sync with main auth service or be separate.
    """

    __tablename__ = "voice_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)  # For outbound calls
    password_hash = Column(String, nullable=True)  # If handling auth separately
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calls = relationship("VoiceCall", back_populates="user")
    schedules = relationship("VoiceSchedule", back_populates="user")
    summaries = relationship("CallSummary", back_populates="user")


class Voice(Base):
    """
    Available voices/assistants from Vapi.
    Each voice maps to a Vapi assistantId.
    """

    __tablename__ = "voices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # User-friendly name
    assistant_id = Column(String, nullable=False, unique=True)  # Vapi assistantId
    description = Column(Text, nullable=True)
    sample_url = Column(String, nullable=True)  # URL to audio sample
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    calls = relationship("VoiceCall", back_populates="voice")
    schedules = relationship("VoiceSchedule", back_populates="voice")


class VoiceCall(Base):
    """
    Voice call records.
    Links to Vapi call but stores our metadata.
    """

    __tablename__ = "voice_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vapi_call_id = Column(String, nullable=False, unique=True)  # From Vapi webhook
    user_id = Column(String, ForeignKey("voice_users.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("voices.assistant_id"), nullable=False)

    # Call details
    channel = Column(String, nullable=False)  # "browser" or "phone"
    status = Column(String, nullable=False)  # "in-progress", "completed", "failed"
    phone_number = Column(String, nullable=True)  # For outbound calls

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Cost tracking (from Vapi)
    cost_total = Column(
        String, nullable=True
    )  # Store as string to avoid float precision issues
    cost_breakdown = Column(JSON, nullable=True)  # Full cost details from Vapi

    # Relationships
    user = relationship("VoiceUser", back_populates="calls")
    voice = relationship("Voice", back_populates="calls")
    summary = relationship("CallSummary", uselist=False, back_populates="call")


class VoiceSchedule(Base):
    """
    Scheduled voice calls.
    Supports cron expressions for recurring calls.
    """

    __tablename__ = "voice_schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("voice_users.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("voices.assistant_id"), nullable=False)

    # Schedule details
    name = Column(String, nullable=False)  # User-friendly name
    cron_expression = Column(String, nullable=False)  # Standard cron format
    timezone = Column(String, default="UTC")

    # Next execution
    next_run_at = Column(DateTime, nullable=False)
    last_run_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional call customization
    custom_metadata = Column(JSON, nullable=True)  # Additional data for the call

    # Relationships
    user = relationship("VoiceUser", back_populates="schedules")
    voice = relationship("Voice", back_populates="schedules")


class CallSummary(Base):
    """
    Call summaries and analysis from Vapi.
    NO raw transcripts stored - only processed summaries.
    """

    __tablename__ = "call_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("voice_calls.id"), nullable=False)
    user_id = Column(String, ForeignKey("voice_users.id"), nullable=False)

    # Summary data (from Vapi webhook)
    summary_json = Column(JSON, nullable=False)  # Complete analysis from Vapi

    # Extracted key fields for easy querying
    duration_seconds = Column(Integer, nullable=True)
    sentiment = Column(String, nullable=True)  # positive/negative/neutral
    key_topics = Column(JSON, nullable=True)  # Array of topics discussed
    action_items = Column(JSON, nullable=True)  # Array of action items

    # Mental health specific fields (if applicable)
    crisis_indicators = Column(JSON, nullable=True)  # Any crisis detection results
    emotional_state = Column(String, nullable=True)  # Overall emotional assessment

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call = relationship("VoiceCall", back_populates="summary")
    user = relationship("VoiceUser", back_populates="summaries")


class WebhookEvent(Base):
    """
    Webhook event log for debugging and audit.
    """

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vapi_call_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # call-start, call-end, etc.
    payload = Column(JSON, nullable=False)  # Full webhook payload
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="pending")  # pending/processed/failed
    error_message = Column(Text, nullable=True)
