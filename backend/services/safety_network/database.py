"""
Database session management for Safety Network Service.
"""

# Use centralized database configuration
from utils.database import get_database_manager

# Create service-specific database manager
_manager = get_database_manager("safety_network")


# Export the get_db function for compatibility
def get_db():
    """Get database session for safety network service."""
    session = _manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
