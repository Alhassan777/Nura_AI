"""
Database session management for Safety Network Invitations Service.
"""

# Use centralized database configuration
from utils.database import get_db_context, get_database_manager

# Create service-specific database manager (but will use same DB as safety_network)
_manager = get_database_manager(
    "safety_network"
)  # Use safety_network's database manager


# Export both functions for compatibility
def get_db():
    """Get database session for FastAPI dependency injection."""
    session = _manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_context_local():
    """Get database context manager for manual usage."""
    return get_db_context("safety_network")
