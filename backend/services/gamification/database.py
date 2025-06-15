"""
Database configuration for Gamification Service.
Handles PostgreSQL connection using the centralized database system.
"""

# Use centralized database configuration directly
from utils.database import get_database_manager


# Get database manager for gamification service
_db_manager = get_database_manager("gamification")


# Export the get_db function for FastAPI dependency injection
def get_db():
    """Get database session for gamification service."""
    session = _db_manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
