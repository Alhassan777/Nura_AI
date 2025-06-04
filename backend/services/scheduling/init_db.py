"""
Database initialization script for Scheduling Service.
Run this to create the database tables.
"""

import asyncio
import logging

from .database import create_tables

logger = logging.getLogger(__name__)


async def init_scheduling_database():
    """Initialize the scheduling service database."""
    try:
        logger.info("Initializing scheduling service database...")
        create_tables()
        logger.info("✅ Scheduling service database initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize scheduling service database: {e}")
        raise


if __name__ == "__main__":
    # Set up logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the initialization
    asyncio.run(init_scheduling_database())
