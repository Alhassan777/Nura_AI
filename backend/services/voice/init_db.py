"""
Database initialization script for Voice Service.
Run this to create the database tables and seed initial data.
"""

import asyncio
import logging
from typing import List

from .database import create_tables, get_db_session
from .models import Voice, VoiceUser
from .config import config

logger = logging.getLogger(__name__)

# Sample voice assistants to seed the database
SAMPLE_VOICES = [
    {
        "name": "Sarah - Empathetic Counselor",
        "assistant_id": "sample-counselor-assistant-id",
        "description": "A warm, empathetic voice specialized in mental health support and crisis intervention",
        "sample_url": None,
    },
    {
        "name": "Alex - Wellness Coach",
        "assistant_id": "sample-wellness-assistant-id",
        "description": "An encouraging, motivational voice focused on daily wellness and coping strategies",
        "sample_url": None,
    },
    {
        "name": "Jordan - Crisis Support",
        "assistant_id": "sample-crisis-assistant-id",
        "description": "A calm, professional voice trained specifically for crisis situations and immediate support",
        "sample_url": None,
    },
]


async def create_sample_voices():
    """Create sample voice assistants in the database."""
    try:
        with get_db_session() as db:
            # Check if we already have voices
            existing_voices = db.query(Voice).count()
            if existing_voices > 0:
                logger.info(
                    f"Database already has {existing_voices} voices, skipping sample creation"
                )
                return

            # Create sample voices
            for voice_data in SAMPLE_VOICES:
                voice = Voice(**voice_data)
                db.add(voice)
                logger.info(f"Created sample voice: {voice_data['name']}")

            logger.info(f"✅ Created {len(SAMPLE_VOICES)} sample voices")

    except Exception as e:
        logger.error(f"❌ Failed to create sample voices: {e}")
        raise


async def create_sample_user():
    """Create a sample user for testing."""
    try:
        with get_db_session() as db:
            # Check if demo user exists
            demo_user = (
                db.query(VoiceUser).filter(VoiceUser.id == "demo-user-123").first()
            )

            if demo_user:
                logger.info("Demo user already exists")
                return

            # Create demo user
            demo_user = VoiceUser(
                id="demo-user-123",
                name="Demo User",
                email="demo@nura.app",
                phone="+1234567890",  # Sample phone number
            )
            db.add(demo_user)

            logger.info("✅ Created demo user for testing")

    except Exception as e:
        logger.error(f"❌ Failed to create demo user: {e}")
        raise


async def init_voice_database():
    """Initialize the voice service database."""
    logger.info("🎙️ Initializing Voice Service Database...")

    try:
        # Create tables
        create_tables()
        logger.info("✅ Database tables created")

        # Create sample data
        await create_sample_voices()
        await create_sample_user()

        logger.info("🎉 Voice Service Database initialization complete!")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(init_voice_database())
        print("✅ Voice Service Database initialized successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
