"""
Authentication Utilities
Handles password hashing, session tokens, and user authentication for the localStorage-based system.
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

# Redis client for session management
_redis_client = None


async def get_redis_client():
    """Get or create Redis client for session management."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url)
    return _redis_client


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.

    Args:
        password: Plain text password

    Returns:
        Hashed password with salt
    """
    # Generate a random salt
    salt = secrets.token_hex(16)

    # Hash the password with salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    # Return salt + hash
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed_password: Stored hash (salt:hash format)

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, stored_hash = hashed_password.split(":", 1)

        # Hash the provided password with the stored salt
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        # Compare hashes
        return password_hash == stored_hash

    except ValueError:
        # Invalid hash format
        logger.error("Invalid password hash format")
        return False
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


def create_session_token() -> str:
    """
    Create a secure session token.

    Returns:
        Random session token
    """
    return secrets.token_urlsafe(32)


async def store_session(
    user_id: str, session_token: str, user_data: Dict[str, Any], ttl_minutes: int = 60
) -> bool:
    """
    Store user session in Redis.

    Args:
        user_id: User identifier
        session_token: Session token
        user_data: User data to store in session
        ttl_minutes: Session timeout in minutes

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"session:{session_token}"

        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": str(datetime.utcnow()),
            "expires_at": str(datetime.utcnow() + timedelta(minutes=ttl_minutes)),
        }

        await redis_client.setex(key, int(ttl_minutes * 60), json.dumps(session_data))

        logger.info(f"Stored session for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to store session: {str(e)}")
        return False


async def get_session(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Get user session from Redis.

    Args:
        session_token: Session token

    Returns:
        Session data if valid, None otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"session:{session_token}"
        session_json = await redis_client.get(key)

        if not session_json:
            return None

        session_data = json.loads(session_json)

        # Check if session has expired
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.utcnow() > expires_at:
            await delete_session(session_token)
            return None

        return session_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode session data: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        return None


async def delete_session(session_token: str) -> bool:
    """
    Delete user session from Redis.

    Args:
        session_token: Session token

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        key = f"session:{session_token}"
        result = await redis_client.delete(key)

        if result > 0:
            logger.info(f"Deleted session: {session_token}")
            return True
        else:
            logger.warning(f"No session found to delete: {session_token}")
            return False

    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        return False


async def refresh_session(session_token: str, ttl_minutes: int = 60) -> bool:
    """
    Refresh session expiration time.

    Args:
        session_token: Session token
        ttl_minutes: New timeout in minutes

    Returns:
        True if refreshed successfully, False otherwise
    """
    try:
        # Get current session data
        session_data = await get_session(session_token)
        if not session_data:
            return False

        # Update expiration time
        session_data["expires_at"] = str(
            datetime.utcnow() + timedelta(minutes=ttl_minutes)
        )

        # Store updated session
        redis_client = await get_redis_client()
        key = f"session:{session_token}"

        await redis_client.setex(key, int(ttl_minutes * 60), json.dumps(session_data))

        logger.info(f"Refreshed session: {session_token}")
        return True

    except Exception as e:
        logger.error(f"Failed to refresh session: {str(e)}")
        return False


def create_session_token() -> str:
    """
    Create a secure session token.

    Returns:
        Random session token
    """
    return secrets.token_urlsafe(32)


def verify_session_token(token: str) -> bool:
    """
    Basic validation of session token format.

    Args:
        token: Session token to validate

    Returns:
        True if token format is valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # Check if token is the right length (32 bytes = 43 chars in base64)
    if len(token) != 43:
        return False

    # Check if token contains only valid base64 characters
    import string

    valid_chars = string.ascii_letters + string.digits + "-_"
    return all(c in valid_chars for c in token)


async def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions from Redis.

    Returns:
        Number of sessions cleaned up
    """
    try:
        redis_client = await get_redis_client()

        # Get all session keys
        session_keys = await redis_client.keys("session:*")

        cleaned_count = 0
        for key in session_keys:
            session_json = await redis_client.get(key)
            if session_json:
                try:
                    session_data = json.loads(session_json)
                    expires_at = datetime.fromisoformat(session_data["expires_at"])

                    if datetime.utcnow() > expires_at:
                        await redis_client.delete(key)
                        cleaned_count += 1

                except (json.JSONDecodeError, KeyError, ValueError):
                    # Invalid session data, delete it
                    await redis_client.delete(key)
                    cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired sessions")

        return cleaned_count

    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")
        return 0
