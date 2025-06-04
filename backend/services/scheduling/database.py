"""
Database session management for Scheduling Service.
"""

# Use centralized database configuration
from utils.database import get_db, get_database_manager

# Create service-specific database manager
_manager = get_database_manager("scheduling")


# Export the get_db function for compatibility
def get_db():
    """Get database session for scheduling service."""
    return _manager.get_db()
