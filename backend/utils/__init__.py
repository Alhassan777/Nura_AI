"""
Nura Backend Utilities
Shared utility modules for all services (memory, chat, voice).
"""

from .auth import *
from .database import *
from .redis_client import *
from .voice import *
from .security import *
from .validation import *

__all__ = [
    # Auth utilities
    "hash_password",
    "verify_password",
    "create_session_token",
    "verify_session_token",
    # Database utilities
    "get_db_connection",
    "execute_query",
    "create_tables_if_not_exist",
    # Redis utilities
    "get_redis_client",
    "cache_set",
    "cache_get",
    "cache_delete",
    # Voice utilities
    "get_customer_id",
    "store_call_mapping",
    "extract_call_id_from_vapi_event",
    # Security utilities
    "sanitize_input",
    "validate_email",
    "check_rate_limit",
    # Validation utilities
    "validate_user_input",
    "validate_phone_number",
    "validate_conversation_data",
]
