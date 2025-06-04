"""
Database session management for Safety Network Invitations Service.
"""

# Use centralized database configuration
from utils.database import get_db, get_database_manager

# Create service-specific database manager (but will use same DB as safety_network)
_manager = get_database_manager("safety_invitations")


# Export the get_db function for compatibility
def get_db():
    """Get database session for safety invitations service."""
    return _manager.get_db()
