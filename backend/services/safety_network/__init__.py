"""
Safety Network Service

Manages emergency contacts and trusted friends network for users.
Provides safety net functionality for crisis situations and support escalation.
"""

from models import SafetyContact, CommunicationMethod
from .database import get_db
from .manager import SafetyNetworkManager

__all__ = [
    "SafetyContact",
    "CommunicationMethod",
    "get_db",
    "SafetyNetworkManager",
]
