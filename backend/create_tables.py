#!/usr/bin/env python3
"""
Database table creation script for Nura App
Creates all required tables including action_plans, action_steps, and action_subtasks
"""

import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models to ensure they're registered with SQLAlchemy
from models import (
    Base,
    User,
    UserServiceProfile,
    UserSyncLog,
    UserPrivacySettings,
    Conversation,
    Message,
    ConversationSummary,
    SystemEvent,
    Badge,
    UserBadge,
    Quest,
    UserQuest,
    Reflection,
    XPEvent,
    UserStreak,
    UserFreezeUsage,
    Voice,
    VoiceCall,
    VoiceSchedule,
    CallSummary,
    WebhookEvent,
    Schedule,
    ScheduleExecution,
    UserBlock,
    SafetyContact,
    ContactLog,
    SafetyNetworkRequest,
    SafetyNetworkResponse,
    SafetyPermissionChange,
    GeneratedImage,
    ActionPlan,
    ActionStep,
    ActionSubtask,
)
from utils.database import DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_all_tables():
    """Create all database tables."""
    try:
        # Get database URL
        database_url = DatabaseConfig.get_database_url()
        logger.info(f"Connecting to database...")

        # Create engine
        engine = create_engine(database_url)

        # Create all tables
        logger.info("Creating all database tables...")
        Base.metadata.create_all(bind=engine)

        logger.info("✅ Successfully created all database tables!")

        # List created tables
        tables = Base.metadata.tables.keys()
        logger.info(f"Created tables: {', '.join(sorted(tables))}")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


def check_tables_exist():
    """Check which tables exist in the database."""
    try:
        database_url = DatabaseConfig.get_database_url()
        engine = create_engine(database_url)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        logger.info(f"Existing tables: {', '.join(sorted(existing_tables))}")

        # Check for action plan tables specifically
        action_plan_tables = ["action_plans", "action_steps", "action_subtasks"]
        missing_tables = [
            table for table in action_plan_tables if table not in existing_tables
        ]

        if missing_tables:
            logger.warning(f"Missing action plan tables: {', '.join(missing_tables)}")
        else:
            logger.info("✅ All action plan tables exist!")

        return existing_tables

    except Exception as e:
        logger.error(f"❌ Error checking tables: {e}")
        return []


if __name__ == "__main__":
    print("🚀 Nura Database Table Creation Script")
    print("=" * 50)

    # Check existing tables
    print("\n1️⃣ Checking existing tables...")
    existing_tables = check_tables_exist()

    # Create missing tables
    print("\n2️⃣ Creating missing tables...")
    success = create_all_tables()

    if success:
        print("\n✅ Database initialization completed successfully!")
        print("\n3️⃣ Final table check...")
        check_tables_exist()
    else:
        print("\n❌ Database initialization failed!")
        exit(1)
