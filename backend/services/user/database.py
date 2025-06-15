"""
Database configuration for Normalized User Service.
Handles Supabase PostgreSQL connection using the same database as other services.
"""

# Use centralized database configuration
from utils.database import get_db, get_database_manager

# Create service-specific database manager
_manager = get_database_manager("user")


# Export the get_db function for compatibility
def get_db():
    """Get database session for user service."""
    session = _manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
