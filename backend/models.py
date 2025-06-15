"""
Unified Database Models for Nura App
Single source of truth for all database models across all services.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
    Date,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid
import enum

# Unified base for all services - SINGLE SOURCE OF TRUTH
Base = declarative_base()


# ================================
# CORE USER MODELS
# ================================


class User(Base):
    """
    Central User table - Single source of truth for all user data.
    Uses Supabase Auth user ID as primary key to maintain consistency.
    """

    __tablename__ = "users"

    # Primary identifier - UUID type to match Supabase Auth
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core user information
    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True, index=True)

    # Profile information
    full_name = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Auth metadata (synced from Supabase)
    email_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    phone_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    last_sign_in_at = Column(DateTime(timezone=True), nullable=True)

    # Status and gamification
    is_active = Column(Boolean, default=True, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    freeze_credits = Column(Integer, default=3, nullable=False)  # Streak freeze credits
    last_activity = Column(
        DateTime(timezone=True), nullable=True
    )  # Last gamification activity

    # Settings and metadata
    privacy_settings = Column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    service_profiles = relationship(
        "UserServiceProfile", back_populates="user", cascade="all, delete-orphan"
    )
    user_badges = relationship("UserBadge", back_populates="user")
    user_quests = relationship("UserQuest", back_populates="user")
    reflections = relationship("Reflection", back_populates="user")
    xp_events = relationship("XPEvent", back_populates="user")
    user_streaks = relationship("UserStreak", back_populates="user")
    freeze_usages = relationship("UserFreezeUsage", back_populates="user")

    # Indexes for performance
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_phone", "phone_number"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_created", "created_at"),
        Index("idx_users_last_active", "last_active_at"),
        Index("idx_users_deleted", "deleted_at"),
        Index("idx_users_full_name", "full_name"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"

    @property
    def first_name(self):
        """Extract first name from full name for backward compatibility."""
        if self.full_name:
            parts = self.full_name.strip().split()
            return parts[0] if parts else None
        return None

    @property
    def last_name(self):
        """Extract last name from full name for backward compatibility."""
        if self.full_name:
            parts = self.full_name.strip().split()
            return " ".join(parts[1:]) if len(parts) > 1 else None
        return None

    @property
    def display_name_or_fallback(self):
        """Get display name with fallbacks."""
        if self.display_name:
            return self.display_name
        elif self.full_name:
            parts = self.full_name.strip().split()
            return parts[0] if parts else self.email.split("@")[0]
        return self.email.split("@")[0]

    @property
    def is_verified(self):
        """Check if user has verified email or phone."""
        return bool(self.email_confirmed_at or self.phone_confirmed_at)


class ServiceType(enum.Enum):
    """Enumeration of available services."""

    CHAT = "chat"
    VOICE = "voice"
    MEMORY = "memory"
    SAFETY_NETWORK = "safety_network"
    SCHEDULING = "scheduling"
    GAMIFICATION = "gamification"
    IMAGE_GENERATION = "image_generation"


class UserServiceProfile(Base):
    """Service-specific user metadata and preferences."""

    __tablename__ = "user_service_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    service_type = Column(String, nullable=False)

    # Service-specific preferences and metadata
    service_preferences = Column(JSON, default=dict, nullable=False)
    service_metadata = Column(JSON, default=dict, nullable=False)
    usage_stats = Column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="service_profiles")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "service_type", name="uq_user_service"),
        Index("idx_user_service_profiles_user", "user_id"),
        Index("idx_user_service_profiles_service", "service_type"),
    )


class UserSyncLog(Base):
    """Log table to track synchronization between Supabase Auth and backend user data."""

    __tablename__ = "user_sync_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Sync operation details
    sync_type = Column(
        String, nullable=False
    )  # 'create', 'update', 'delete', 'auth_change'
    source = Column(String, nullable=False)  # 'supabase_auth', 'backend_api', 'webhook'

    # Data involved in sync
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)

    # Sync result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Additional context
    request_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_sync_logs_user", "user_id"),
        Index("idx_user_sync_logs_type", "sync_type"),
        Index("idx_user_sync_logs_created", "created_at"),
    )


class UserPrivacySettings(Base):
    """User privacy settings and consent tracking."""

    __tablename__ = "user_privacy_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Privacy preferences
    data_retention_days = Column(Integer, default=365)
    allow_long_term_storage = Column(Boolean, default=True)
    auto_anonymize_pii = Column(Boolean, default=False)
    pii_handling_preferences = Column(JSON, default=dict)

    # Consent tracking
    consent_version = Column(String, nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ================================
# CHAT MODELS
# ================================


class Conversation(Base):
    """Chat conversation model."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Chat message model."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    message_type = Column(String, default="text")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class ConversationSummary(Base):
    """Conversation summaries for efficient retrieval."""

    __tablename__ = "conversation_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemEvent(Base):
    """System events and audit log."""

    __tablename__ = "system_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    event_type = Column(String, nullable=False)
    event_data = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ================================
# GAMIFICATION MODELS
# ================================


class Badge(Base):
    """Badge definitions - achievements users can unlock."""

    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    threshold_type = Column(
        String, nullable=False
    )  # e.g., "xp", "streak", "reflection_count"
    threshold_value = Column(Integer, nullable=False)
    icon = Column(String, nullable=True)  # Icon identifier or URL
    tier = Column(String, nullable=True)  # "bronze", "silver", "gold", etc.
    xp_award = Column(Integer, nullable=True)  # XP awarded when badge is earned
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    """Junction table for user-earned badges."""

    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    badge_id = Column(
        UUID(as_uuid=True), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False
    )
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
        Index("idx_user_badges_user", "user_id"),
        Index("idx_user_badges_earned", "earned_at"),
    )


class Quest(Base):
    """Quest definitions - tasks/challenges for users."""

    __tablename__ = "quests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    xp_reward = Column(Integer, nullable=False)
    key = Column(Text, nullable=True)
    frequency = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    type = Column(Text, nullable=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    user_quests = relationship("UserQuest", back_populates="quest")


class UserQuest(Base):
    """User quest progress and completion tracking."""

    __tablename__ = "user_quests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quest_id = Column(
        UUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=True
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_quests")
    quest = relationship("Quest", back_populates="user_quests")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),
        Index("idx_user_quests_user", "user_id"),
    )


class Reflection(Base):
    """User daily reflections - core gamification activity."""

    __tablename__ = "reflections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mood = Column(String, nullable=False)  # "happy", "sad", "anxious", etc.
    note = Column(Text, nullable=False)  # User's reflection text
    tags = Column(JSON, default=list)  # Array of tags/categories
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="reflections")

    # Indexes
    __table_args__ = (
        Index("idx_reflections_user_created", "user_id", "created_at"),
        Index("idx_reflections_mood", "mood"),
    )


class XPEvent(Base):
    """XP tracking events - records all XP gains and losses."""

    __tablename__ = "xp_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount = Column(Integer, nullable=False)  # XP amount (can be negative)
    event_type = Column(
        String, nullable=False
    )  # "reflection", "quest_completion", "badge_earned", etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="xp_events")

    # Indexes
    __table_args__ = (
        Index("idx_xp_events_user_created", "user_id", "created_at"),
        Index("idx_xp_events_type", "event_type"),
    )


class UserStreak(Base):
    """Historical streak records - archived completed streaks."""

    __tablename__ = "user_streaks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    length = Column(Integer, nullable=False)  # Number of days in the streak
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_streaks")

    # Indexes
    __table_args__ = (
        Index("idx_user_streaks_user", "user_id"),
        Index("idx_user_streaks_length", "length"),
    )


class UserFreezeUsage(Base):
    """Streak freeze usage tracking."""

    __tablename__ = "user_freeze_usages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    frozen_date = Column(Date, nullable=False)  # The date that was "frozen"
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    freeze_metadata = Column(JSON, nullable=True)  # Additional freeze-related data

    # Relationships
    user = relationship("User", back_populates="freeze_usages")

    # Indexes
    __table_args__ = (
        Index("idx_user_freeze_usages_user", "user_id"),
        Index("idx_user_freeze_usages_frozen_date", "frozen_date"),
    )


# ================================
# VOICE SERVICE MODELS
# ================================


class Voice(Base):
    """Available voices/assistants from Vapi."""

    __tablename__ = "voices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # User-friendly name
    assistant_id = Column(String, nullable=False, unique=True)  # Vapi assistantId
    description = Column(Text, nullable=True)
    sample_url = Column(String, nullable=True)  # URL to audio sample
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    calls = relationship("VoiceCall", back_populates="voice")
    schedules = relationship("VoiceSchedule", back_populates="voice")


class VoiceCall(Base):
    """Voice call records linked to Vapi calls."""

    __tablename__ = "voice_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vapi_call_id = Column(String, nullable=False, unique=True)  # From Vapi webhook
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assistant_id = Column(String, ForeignKey("voices.assistant_id"), nullable=False)

    # Call details
    channel = Column(String, nullable=False)  # "browser" or "phone"
    status = Column(String, nullable=False)  # "in-progress", "completed", "failed"
    phone_number = Column(String, nullable=True)  # For outbound calls

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Cost tracking (from Vapi)
    cost_total = Column(String, nullable=True)  # Store as string
    cost_breakdown = Column(JSON, nullable=True)  # Full cost details from Vapi

    # Relationships
    voice = relationship("Voice", back_populates="calls")
    summary = relationship("CallSummary", uselist=False, back_populates="call")


class VoiceSchedule(Base):
    """Scheduled voice calls with cron expressions."""

    __tablename__ = "voice_schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assistant_id = Column(String, ForeignKey("voices.assistant_id"), nullable=False)

    # Schedule details
    name = Column(String, nullable=False)  # User-friendly name
    cron_expression = Column(String, nullable=False)  # Standard cron format
    timezone = Column(String, default="UTC")

    # Next execution
    next_run_at = Column(DateTime(timezone=True), nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Optional call customization
    custom_metadata = Column(JSON, nullable=True)

    # Relationships
    voice = relationship("Voice", back_populates="schedules")


class CallSummary(Base):
    """Call summaries and analysis from Vapi."""

    __tablename__ = "call_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("voice_calls.id"), nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Summary data (from Vapi webhook)
    summary_json = Column(JSON, nullable=False)  # Complete analysis from Vapi

    # Extracted key fields for easy querying
    duration_seconds = Column(Integer, nullable=True)
    sentiment = Column(String, nullable=True)  # positive/negative/neutral
    key_topics = Column(JSON, nullable=True)  # Array of topics discussed
    action_items = Column(JSON, nullable=True)  # Array of action items

    # Mental health specific fields
    crisis_indicators = Column(JSON, nullable=True)  # Crisis detection results
    emotional_state = Column(String, nullable=True)  # Overall emotional assessment

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    call = relationship("VoiceCall", back_populates="summary")


class WebhookEvent(Base):
    """Webhook event log for debugging and audit."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vapi_call_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # call-start, call-end, etc.
    payload = Column(JSON, nullable=False)  # Full webhook payload
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String, default="pending")  # pending/processed/failed
    error_message = Column(Text, nullable=True)


# ================================
# SCHEDULING SERVICE MODELS
# ================================


class ReminderMethod(enum.Enum):
    """Enumeration of available reminder methods."""

    CALL = "call"
    SMS = "sms"
    EMAIL = "email"


class ScheduleType(enum.Enum):
    """Enumeration of schedule types."""

    CHAT_CHECKUP = "chat_checkup"
    VOICE_CHECKUP = "voice_checkup"


class Schedule(Base):
    """Generalized schedule table for both chat and voice assistant checkups."""

    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule details
    name = Column(String, nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)  # Purpose and topics to discuss
    schedule_type = Column(String, nullable=False, default="chat_checkup")

    # Timing configuration
    cron_expression = Column(String, nullable=False)  # Standard cron format
    timezone = Column(String, default="UTC")

    # Execution tracking
    next_run_at = Column(DateTime(timezone=True), nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    # Reminder configuration
    reminder_method = Column(String, nullable=False, default="email")
    phone_number = Column(String, nullable=True)  # For call/SMS reminders
    email = Column(String, nullable=True)  # For email reminders

    # Assistant configuration (for voice checkups)
    assistant_id = Column(String, nullable=True)  # Vapi assistant ID for voice calls

    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Additional customization
    custom_metadata = Column(JSON, nullable=True)

    # Conversation context for better continuity
    context_summary = Column(Text, nullable=True)


class ScheduleExecution(Base):
    """Log of schedule execution attempts and results."""

    __tablename__ = "schedule_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_id = Column(String, ForeignKey("schedules.id"), nullable=False)

    # Execution details
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False)  # "success", "failed", "skipped"
    error_message = Column(Text, nullable=True)

    # Results (for tracking engagement)
    user_responded = Column(Boolean, nullable=True)
    response_time_minutes = Column(Integer, nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)

    # Metadata
    execution_metadata = Column(JSON, nullable=True)


# ================================
# SAFETY NETWORK MODELS
# ================================


class UserBlock(Base):
    """User blocking system for safety network invitations and discovery."""

    __tablename__ = "user_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocking_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User who is doing the blocking
    blocked_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User who is being blocked

    block_type = Column(
        String, nullable=False, default="invitations"
    )  # "invitations", "discovery", "all"
    blocker_reason = Column(Text, nullable=True)  # Private note for blocker

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("blocking_user_id", "blocked_user_id", name="uq_user_blocks"),
        Index("idx_user_blocks_blocking", "blocking_user_id"),
        Index("idx_user_blocks_blocked", "blocked_user_id"),
    )

    def __repr__(self):
        return f"<UserBlock(blocker={self.blocking_user_id}, blocked={self.blocked_user_id}, type={self.block_type})>"


class CommunicationMethod(enum.Enum):
    """Enumeration of available communication methods."""

    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"


class SafetyContact(Base):
    """Safety network contacts for users."""

    __tablename__ = "safety_contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys to central user database
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # Person who owns this safety network
    contact_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # If contact is also a system user

    # Contact details (only for external contacts not in our system)
    external_first_name = Column(String, nullable=True)
    external_last_name = Column(String, nullable=True)
    external_phone_number = Column(String, nullable=True)
    external_email = Column(String, nullable=True)

    # Safety network specific data
    priority_order = Column(Integer, nullable=False)  # 1 = highest priority
    allowed_communication_methods = Column(JSON, nullable=False)  # Array of methods
    preferred_communication_method = Column(String, nullable=False, default="phone")

    # Relationship and context
    relationship_type = Column(String, nullable=True)  # "family", "friend", "therapist"
    notes = Column(Text, nullable=True)

    # Availability and preferences
    preferred_contact_time = Column(
        String, nullable=True
    )  # "business_hours", "anytime"
    timezone = Column(String, default="UTC")

    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_emergency_contact = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Last contact tracking
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    last_contact_method = Column(String, nullable=True)
    last_contact_successful = Column(Boolean, nullable=True)

    # Additional metadata
    custom_metadata = Column(JSON, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_safety_contacts_user", "user_id"),
        Index("idx_safety_contacts_contact_user", "contact_user_id"),
        Index("idx_safety_contacts_priority", "user_id", "priority_order"),
        Index("idx_safety_contacts_active", "user_id", "is_active"),
        Index("idx_safety_contacts_emergency", "user_id", "is_emergency_contact"),
    )

    def __repr__(self):
        return f"<SafetyContact(id={self.id}, user_id={self.user_id}, priority={self.priority_order})>"


class ContactLog(Base):
    """Log of contact attempts with safety network contacts."""

    __tablename__ = "contact_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    safety_contact_id = Column(String, ForeignKey("safety_contacts.id"), nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Contact attempt details
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    contact_method = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)

    # Context
    reason = Column(String, nullable=False)  # "crisis_intervention", "wellness_check"
    initiated_by = Column(String, nullable=False)  # "system", "user", "admin"

    # Response tracking
    response_received = Column(Boolean, nullable=True)
    response_time_minutes = Column(Integer, nullable=True)
    response_summary = Column(Text, nullable=True)

    # Technical details
    message_content = Column(Text, nullable=True)  # What was sent
    error_message = Column(Text, nullable=True)  # If failed

    # Metadata
    contact_metadata = Column(JSON, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_contact_logs_user", "user_id"),
        Index("idx_contact_logs_contact", "safety_contact_id"),
        Index("idx_contact_logs_attempted", "attempted_at"),
        Index("idx_contact_logs_reason", "reason"),
    )

    def __repr__(self):
        return f"<ContactLog(id={self.id}, safety_contact_id={self.safety_contact_id}, success={self.success})>"


class SafetyNetworkRequestStatus(enum.Enum):
    """Status of safety network invitation requests."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SafetyNetworkRequest(Base):
    """Safety network invitation requests - one-way invitations to become safety contacts."""

    __tablename__ = "safety_network_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Request participants
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User requesting help (Alice)
    requested_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User being asked to help (Bob)

    # Request details
    relationship_type = Column(
        String, nullable=True
    )  # "family", "friend", "therapist", "partner"
    invitation_message = Column(Text, nullable=True)  # Personal message from requester

    # Permissions being requested
    requested_permissions = Column(
        JSON, nullable=False, default=dict
    )  # What Alice wants from Bob

    # Priority preferences
    requested_priority_order = Column(
        Integer, nullable=True
    )  # Priority order requested by sender (1 = highest)

    # New privacy-aware fields
    recipient_default_permissions = Column(
        JSON, nullable=True
    )  # Bob's usual defaults for this relationship type
    permission_conflicts = Column(
        JSON, nullable=True
    )  # Array of conflicts between requested vs defaults
    auto_accept_eligible = Column(
        Boolean, default=False
    )  # Whether this invitation could be auto-accepted
    invitation_preview = Column(
        JSON, nullable=True
    )  # Additional metadata for UI display

    # Request status and timing
    status = Column(
        String, nullable=False, default=SafetyNetworkRequestStatus.PENDING.value
    )
    expires_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When invitation expires

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "requester_id", "requested_id", name="uq_safety_network_request"
        ),
        Index("idx_safety_requests_requester", "requester_id"),
        Index("idx_safety_requests_requested", "requested_id"),
        Index("idx_safety_requests_status", "status"),
        Index("idx_safety_requests_expires", "expires_at"),
        Index("idx_safety_requests_auto_accept", "auto_accept_eligible"),
        Index("idx_safety_requests_recipient_status", "requested_id", "status"),
    )

    def __repr__(self):
        return f"<SafetyNetworkRequest(id={self.id}, requester={self.requester_id}, requested={self.requested_id}, status={self.status})>"


class SafetyNetworkResponse(Base):
    """Safety network invitation responses - Bob's response to Alice's request."""

    __tablename__ = "safety_network_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(
        String,
        ForeignKey("safety_network_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One response per request
        index=True,
    )

    # Response details
    response_type = Column(String, nullable=False)  # "accept", "decline"
    response_message = Column(Text, nullable=True)  # Optional message from Bob

    # Permissions granted (only for accepted requests)
    granted_permissions = Column(JSON, nullable=True)  # What Bob actually agrees to

    # Timestamps
    responded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    request = relationship("SafetyNetworkRequest", backref="response")

    # Indexes
    __table_args__ = (
        Index("idx_safety_responses_request", "request_id"),
        Index("idx_safety_responses_type", "response_type"),
        Index("idx_safety_responses_responded", "responded_at"),
    )

    def __repr__(self):
        return f"<SafetyNetworkResponse(id={self.id}, request_id={self.request_id}, response_type={self.response_type})>"


class SafetyPermissionChange(Base):
    """Log of permission changes to safety contacts after initial invitation acceptance."""

    __tablename__ = "safety_permission_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    safety_contact_id = Column(
        String,
        ForeignKey("safety_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User who owns the safety contact
    changed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # User who made the change

    old_permissions = Column(JSON, nullable=False)
    new_permissions = Column(JSON, nullable=False)
    change_reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("idx_permission_changes_contact", "safety_contact_id"),
        Index("idx_permission_changes_user", "user_id"),
        Index("idx_permission_changes_changed_by", "changed_by_user_id"),
        Index("idx_permission_changes_created", "created_at"),
    )

    def __repr__(self):
        return f"<SafetyPermissionChange(id={self.id}, contact_id={self.safety_contact_id}, changed_by={self.changed_by_user_id})>"


class GeneratedImage(Base):
    """Stores generated images for each user."""

    __tablename__ = "generated_images"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    prompt = Column(Text, nullable=False)
    image_data = Column(Text, nullable=False)  # base64 or URL to file
    image_format = Column(String, default="png")
    image_metadata = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    name = Column(String, nullable=True, index=True)  # Optional user-friendly name

    # Relationships
    user = relationship("User", backref="generated_images")

    __table_args__ = (
        Index("idx_generated_images_user", "user_id"),
        Index("idx_generated_images_created", "created_at"),
    )


# Action Plan Models for AI-generated task management


class ActionPlan(Base):
    """AI-generated action plans for users' goals and mental health."""

    __tablename__ = "action_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic plan information
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    plan_type = Column(
        String, nullable=False
    )  # therapeutic_emotional, personal_achievement, hybrid
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="active")  # active, completed, paused, deleted

    # AI generation metadata
    generated_by_ai = Column(Boolean, default=True)
    generation_prompt = Column(
        Text, nullable=True
    )  # The prompt used to generate this plan
    ai_metadata = Column(
        JSON, nullable=True
    )  # AI generation details, user emotional state, etc.

    # Progress tracking
    progress_percentage = Column(Integer, default=0)

    # Scheduling and completion
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Additional metadata
    tags = Column(JSON, default=list)  # User-defined tags
    custom_metadata = Column(JSON, default=dict)  # Additional flexible data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", backref="action_plans")
    steps = relationship(
        "ActionStep",
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="ActionStep.order_index",
    )

    # Indexes
    __table_args__ = (
        Index("idx_action_plans_user", "user_id"),
        Index("idx_action_plans_status", "status"),
        Index("idx_action_plans_type", "plan_type"),
        Index("idx_action_plans_created", "created_at"),
        Index("idx_action_plans_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<ActionPlan(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ActionStep(Base):
    """Individual steps within an action plan."""

    __tablename__ = "action_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action_plan_id = Column(
        String,
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)  # Order within the plan

    # Step metadata (from AI generation)
    time_needed = Column(String, nullable=True)  # e.g., "30 minutes", "1 week"
    difficulty = Column(String, nullable=True)  # easy, moderate, challenging
    purpose = Column(Text, nullable=True)  # Why this step matters
    success_criteria = Column(Text, nullable=True)  # What success looks like

    # Status and progress
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)  # User notes about this step

    # Scheduling
    due_date = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)

    # AI-specific fields
    ai_metadata = Column(JSON, nullable=True)  # Additional AI-generated data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    action_plan = relationship("ActionPlan", back_populates="steps")
    subtasks = relationship(
        "ActionSubtask",
        back_populates="action_step",
        cascade="all, delete-orphan",
        order_by="ActionSubtask.order_index",
    )

    # Indexes
    __table_args__ = (
        Index("idx_action_steps_plan", "action_plan_id"),
        Index("idx_action_steps_completed", "completed"),
        Index("idx_action_steps_order", "action_plan_id", "order_index"),
        Index("idx_action_steps_due", "due_date"),
    )

    def __repr__(self):
        return f"<ActionStep(id={self.id}, plan_id={self.action_plan_id}, title={self.title})>"


class ActionSubtask(Base):
    """Subtasks within action steps for detailed breakdown."""

    __tablename__ = "action_subtasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action_step_id = Column(
        String,
        ForeignKey("action_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Subtask details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)  # Order within the step

    # Status
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)  # User notes

    # Scheduling
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    action_step = relationship("ActionStep", back_populates="subtasks")

    # Indexes
    __table_args__ = (
        Index("idx_action_subtasks_step", "action_step_id"),
        Index("idx_action_subtasks_completed", "completed"),
        Index("idx_action_subtasks_order", "action_step_id", "order_index"),
    )

    def __repr__(self):
        return f"<ActionSubtask(id={self.id}, step_id={self.action_step_id}, title={self.title})>"
