"""
Initialize Safety Network Database.

Run this script to create the safety network database tables.
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the safety network database."""
    try:
        logger.info("Initializing safety network database...")
        create_tables()
        logger.info("Safety network database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize safety network database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
