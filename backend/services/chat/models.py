"""
SQLAlchemy models for Chat Service.
Designed for Supabase PostgreSQL database.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    Float,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

Base = declarative_base()


class ChatUser(Base):
    """User table for chat service."""

    __tablename__ = "chat_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)

    # User preferences
    privacy_settings = Column(JSON, default=dict)
    notification_preferences = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Relationships
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="user", cascade="all, delete-orphan"
    )
    memory_items = relationship(
        "MemoryItem", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ChatUser(id={self.id}, email={self.email}, full_name={self.full_name})>"
        )


class Conversation(Base):
    """Conversation/session table."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("chat_users.id"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String, nullable=True)  # Auto-generated or user-set
    description = Column(Text, nullable=True)

    # Session tracking
    session_type = Column(String, default="chat")  # chat, voice, crisis, etc.
    status = Column(String, default="active")  # active, archived, deleted

    # Crisis and safety
    crisis_level = Column(String, default="none")  # none, concern, crisis
    safety_plan_triggered = Column(Boolean, default=False)

    # Analytics
    message_count = Column(Integer, default=0)
    total_duration_minutes = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("ChatUser", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_updated", "user_id", "updated_at"),
        Index("idx_conversations_status", "status"),
    )

    def __repr__(self):
        return (
            f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title})>"
        )


class Message(Base):
    """Individual messages in conversations."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id"), nullable=False, index=True
    )
    user_id = Column(String, ForeignKey("chat_users.id"), nullable=False, index=True)

    # Message content
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    message_type = Column(String, default="text")  # text, image, audio, system_alert

    # Processing metadata
    processed_content = Column(Text, nullable=True)  # PII-processed version
    pii_detected = Column(JSON, default=dict)  # PII detection results
    sentiment_score = Column(Float, nullable=True)

    # Crisis detection
    crisis_indicators = Column(JSON, default=dict)
    requires_intervention = Column(Boolean, default=False)

    # Memory and context
    memory_extracted = Column(Boolean, default=False)
    memory_items_created = Column(
        JSON, default=list
    )  # List of memory IDs created from this message

    # Response metadata (for assistant messages)
    response_time_ms = Column(Integer, nullable=True)
    model_used = Column(String, nullable=True)  # gemini-pro, gpt-4, etc.
    tokens_used = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("ChatUser", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_user_created", "user_id", "created_at"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_crisis", "requires_intervention"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class MemoryItem(Base):
    """Memory items extracted from conversations."""

    __tablename__ = "memory_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("chat_users.id"), nullable=False, index=True)
    conversation_id = Column(
        String, ForeignKey("conversations.id"), nullable=True, index=True
    )
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)

    # Memory content
    content = Column(Text, nullable=False)
    processed_content = Column(Text, nullable=True)  # PII-processed version
    memory_type = Column(
        String, nullable=False
    )  # personal_fact, emotional_state, goal, etc.

    # Storage classification
    storage_type = Column(String, default="short_term")  # short_term, long_term
    significance_level = Column(
        String, default="low"
    )  # minimal, low, moderate, high, critical
    significance_category = Column(
        String, nullable=True
    )  # life_changing, emotional_insight, etc.

    # Scoring
    relevance_score = Column(Float, default=0.0)
    stability_score = Column(Float, default=0.0)
    explicitness_score = Column(Float, default=0.0)
    composite_score = Column(Float, default=0.0)

    # Vector embedding (stored as JSON array)
    embedding = Column(JSON, nullable=True)

    # Privacy and consent
    pii_detected = Column(JSON, default=dict)
    user_consent = Column(JSON, default=dict)  # User's privacy choices for this memory
    anonymized_version = Column(Text, nullable=True)

    # Metadata
    extraction_metadata = Column(JSON, default=dict)  # Gemini scoring metadata
    tags = Column(JSON, default=list)  # User or system tags

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)

    # Relationships
    user = relationship("ChatUser", back_populates="memory_items")
    conversation = relationship("Conversation")
    message = relationship("Message")

    # Indexes
    __table_args__ = (
        Index("idx_memory_user_type", "user_id", "memory_type"),
        Index("idx_memory_user_storage", "user_id", "storage_type"),
        Index("idx_memory_significance", "significance_level"),
        Index("idx_memory_composite_score", "composite_score"),
        Index("idx_memory_created", "created_at"),
    )

    def __repr__(self):
        return f"<MemoryItem(id={self.id}, user_id={self.user_id}, type={self.memory_type})>"


class ConversationSummary(Base):
    """Summaries of conversations for quick retrieval."""

    __tablename__ = "conversation_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String, ForeignKey("conversations.id"), nullable=False, unique=True, index=True
    )
    user_id = Column(String, ForeignKey("chat_users.id"), nullable=False, index=True)

    # Summary content
    summary = Column(Text, nullable=False)
    key_topics = Column(JSON, default=list)
    emotional_themes = Column(JSON, default=list)
    action_items = Column(JSON, default=list)

    # Analytics
    sentiment_overall = Column(
        String, nullable=True
    )  # positive, negative, neutral, mixed
    crisis_indicators = Column(JSON, default=dict)
    therapeutic_progress = Column(JSON, default=dict)

    # Metadata
    summary_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    conversation = relationship("Conversation")
    user = relationship("ChatUser")

    def __repr__(self):
        return f"<ConversationSummary(id={self.id}, conversation_id={self.conversation_id})>"


class UserPrivacySettings(Base):
    """User privacy settings and consent tracking."""

    __tablename__ = "user_privacy_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("chat_users.id"), nullable=False, unique=True, index=True
    )

    # Privacy preferences
    data_retention_days = Column(Integer, default=365)  # How long to keep data
    allow_long_term_storage = Column(Boolean, default=True)
    auto_anonymize_pii = Column(Boolean, default=True)

    # Consent tracking
    consent_version = Column(
        String, nullable=False
    )  # Version of privacy policy agreed to
    consent_date = Column(DateTime(timezone=True), nullable=False)

    # PII handling preferences
    pii_handling_preferences = Column(JSON, default=dict)  # Per-PII-type preferences

    # Data sharing
    allow_research_use = Column(Boolean, default=False)
    allow_improvement_use = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("ChatUser")

    def __repr__(self):
        return f"<UserPrivacySettings(id={self.id}, user_id={self.user_id})>"


class SystemEvent(Base):
    """System events and audit log."""

    __tablename__ = "system_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("chat_users.id"), nullable=True, index=True)

    # Event details
    event_type = Column(
        String, nullable=False, index=True
    )  # login, message_sent, crisis_detected, etc.
    event_category = Column(
        String, nullable=False, index=True
    )  # security, user_action, system, crisis

    # Event data
    event_data = Column(JSON, default=dict)
    severity = Column(String, default="info")  # debug, info, warning, error, critical

    # Context
    session_id = Column(String, nullable=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("ChatUser")

    # Indexes
    __table_args__ = (
        Index("idx_events_type_created", "event_type", "created_at"),
        Index("idx_events_category_created", "event_category", "created_at"),
        Index("idx_events_severity", "severity"),
    )

    def __repr__(self):
        return f"<SystemEvent(id={self.id}, type={self.event_type}, category={self.event_category})>"
