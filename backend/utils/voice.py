"""
Voice Integration Utilities
Handles Vapi.ai integration, call mappings, and voice-specific operations.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

# Redis client for voice mappings
_redis_client = None


async def get_redis_client():
    """Get or create Redis client for voice operations."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url)
    return _redis_client


async def get_customer_id(call_id: str) -> Optional[str]:
    """
    Get customerId from callId for downstream workers.

    Args:
        call_id: The Vapi call ID

    Returns:
        customerId if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:call:{call_id}"
        mapping_json = await redis_client.get(key)

        if not mapping_json:
            logger.warning(f"No mapping found for call ID: {call_id}")
            return None

        mapping_data = json.loads(mapping_json)
        customer_id = mapping_data.get("customerId")

        if customer_id:
            logger.info(f"Retrieved customer ID {customer_id} for call {call_id}")
        else:
            logger.warning(f"Customer ID not found in mapping for call {call_id}")

        return customer_id

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode mapping data for call {call_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to get customer ID for call {call_id}: {str(e)}")
        return None


async def get_call_mapping(call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get complete call mapping data.

    Args:
        call_id: The Vapi call ID

    Returns:
        Complete mapping data if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:call:{call_id}"
        mapping_json = await redis_client.get(key)

        if not mapping_json:
            return None

        mapping_data = json.loads(mapping_json)
        mapping_data["callId"] = call_id  # Add the call ID to the data

        return mapping_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode mapping data for call {call_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to get call mapping for call {call_id}: {str(e)}")
        return None


async def store_call_mapping(
    call_id: str,
    customer_id: str,
    mode: str = "web",
    phone_number: Optional[str] = None,
    ttl_minutes: int = 30,
    **additional_data,
) -> bool:
    """
    Store callId to customerId mapping with additional metadata.

    Args:
        call_id: The Vapi call ID
        customer_id: The customer/user ID
        mode: "web" or "phone"
        phone_number: Phone number for phone calls
        ttl_minutes: Time to live in minutes
        **additional_data: Any additional data to store

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:call:{call_id}"

        mapping_data = {
            "customerId": customer_id,
            "mode": mode,
            "phoneNumber": phone_number,
            "timestamp": str(datetime.utcnow()),
            **additional_data,  # Include any additional data
        }

        await redis_client.setex(
            key, int(ttl_minutes * 60), json.dumps(mapping_data)  # Convert to seconds
        )

        logger.info(f"Stored voice mapping: {call_id} -> {customer_id} (mode: {mode})")
        return True

    except Exception as e:
        logger.error(f"Failed to store voice mapping: {str(e)}")
        return False


async def delete_call_mapping(call_id: str) -> bool:
    """
    Delete call mapping (cleanup).

    Args:
        call_id: The Vapi call ID

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:call:{call_id}"
        result = await redis_client.delete(key)

        if result > 0:
            logger.info(f"Deleted voice mapping for call {call_id}")
            return True
        else:
            logger.warning(f"No mapping found to delete for call {call_id}")
            return False

    except Exception as e:
        logger.error(f"Failed to delete voice mapping for call {call_id}: {str(e)}")
        return False


def extract_call_id_from_vapi_event(event_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract call ID from Vapi webhook event data.

    Args:
        event_data: The webhook event data

    Returns:
        Call ID if found, None otherwise
    """
    try:
        # Try different possible locations for call ID
        call_id = (
            event_data.get("call", {}).get("id")
            or event_data.get("callId")
            or event_data.get("id")
        )

        if call_id:
            logger.debug(f"Extracted call ID: {call_id}")
        else:
            logger.warning("No call ID found in event data")

        return call_id

    except Exception as e:
        logger.error(f"Failed to extract call ID from event: {str(e)}")
        return None


def is_conversation_update_event(event_data: Dict[str, Any]) -> bool:
    """
    Check if this is a conversation-update event that should be processed.

    Args:
        event_data: The webhook event data

    Returns:
        True if this is a conversation-update event, False otherwise
    """
    try:
        event_type = event_data.get("type") or event_data.get("eventType")
        return event_type == "conversation-update"

    except Exception as e:
        logger.error(f"Failed to check event type: {str(e)}")
        return False


def extract_user_message_from_event(event_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract user message from Vapi conversation-update event.

    Args:
        event_data: The webhook event data

    Returns:
        User message if found, None otherwise
    """
    try:
        # Look for message in different possible locations
        message = (
            event_data.get("message", {}).get("content")
            or event_data.get("content")
            or event_data.get("text")
        )

        # Check if this is a user message
        role = event_data.get("message", {}).get("role") or event_data.get("role")

        if role == "user" and message:
            logger.debug(f"Extracted user message: {message[:100]}...")
            return message

        return None

    except Exception as e:
        logger.error(f"Failed to extract user message from event: {str(e)}")
        return None


async def store_conversation_context(
    call_id: str, context_data: Dict[str, Any], ttl_minutes: int = 60
) -> bool:
    """
    Store conversation context for a call.

    Args:
        call_id: The Vapi call ID
        context_data: Context data to store
        ttl_minutes: Time to live in minutes

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:context:{call_id}"

        context_with_timestamp = {**context_data, "timestamp": str(datetime.utcnow())}

        await redis_client.setex(
            key, int(ttl_minutes * 60), json.dumps(context_with_timestamp)
        )

        logger.info(f"Stored conversation context for call {call_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to store conversation context: {str(e)}")
        return False


async def get_conversation_context(call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get conversation context for a call.

    Args:
        call_id: The Vapi call ID

    Returns:
        Context data if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"vapi:context:{call_id}"
        context_json = await redis_client.get(key)

        if not context_json:
            return None

        return json.loads(context_json)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode context data for call {call_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to get conversation context for call {call_id}: {str(e)}")
        return None
