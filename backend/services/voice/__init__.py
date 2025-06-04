"""
Voice service module for Vapi integration.
Handles voice calls, scheduling, and summaries without transcript storage.

CONSOLIDATED ARCHITECTURE:
- vapi_webhook_router.py: Unified webhook handling for all tools
- api.py: FastAPI routes for voice endpoints
- vapi_client.py: Vapi API integration
- queue_worker.py: Background job processing for scheduled calls
- config.py: Configuration management
- database.py: Database session management
- user_integration.py: Integration with normalized user system

All webhook functionality has been consolidated into vapi_webhook_router.py
for better maintainability and reduced duplication.
"""

from .vapi_webhook_router import vapi_webhook_router
from .api import router as voice_api_router
from .config import config
from .database import get_db
from .vapi_client import vapi_client
from .user_integration import VoiceUserIntegration

__all__ = [
    "vapi_webhook_router",
    "voice_api_router",
    "config",
    "get_db",
    "vapi_client",
    "VoiceUserIntegration",
]
