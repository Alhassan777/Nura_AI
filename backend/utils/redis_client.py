"""
Redis Client Utilities
Centralized Redis operations for caching, session management, and data storage.
Enhanced with authentication integration for secure user data access.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client = None


async def get_redis_client():
    """Get or create Redis client with authentication support."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_password = os.getenv("REDIS_PASSWORD")

        try:
            # Create Redis client with authentication if password is provided
            if redis_password:
                _redis_client = redis.from_url(
                    redis_url, password=redis_password, decode_responses=True
                )
            else:
                _redis_client = redis.from_url(redis_url, decode_responses=True)

            # Test connection
            await _redis_client.ping()
            logger.info(f"Initialized authenticated Redis client: {redis_url}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    return _redis_client


async def cache_set(
    key: str,
    value: Union[str, Dict, List],
    ttl_seconds: Optional[int] = None,
    user_context: Optional[str] = None,
) -> bool:
    """
    Set a value in Redis cache with optional user context for security.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized if not string)
        ttl_seconds: Time to live in seconds (optional)
        user_context: User ID for security context (optional)

    Returns:
        True if set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        # Serialize value if not string
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        if ttl_seconds:
            await redis_client.setex(key, ttl_seconds, value)
        else:
            await redis_client.set(key, value)

        logger.debug(
            f"Cached value for key: {key}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return True

    except Exception as e:
        logger.error(f"Failed to cache value for key {key}: {str(e)}")
        return False


async def cache_get(
    key: str, parse_json: bool = True, user_context: Optional[str] = None
) -> Optional[Union[str, Dict, List]]:
    """
    Get a value from Redis cache with optional user context for security.

    Args:
        key: Cache key
        parse_json: Whether to parse JSON strings back to objects
        user_context: User ID for security context (optional)

    Returns:
        Cached value if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        value = await redis_client.get(key)

        if value is None:
            return None

        # Decode bytes to string
        if isinstance(value, bytes):
            value = value.decode("utf-8")

        # Parse JSON if requested and value looks like JSON
        if parse_json and isinstance(value, str):
            try:
                if value.startswith(("{", "[")):
                    value = json.loads(value)
            except json.JSONDecodeError:
                # Not JSON, return as string
                pass

        logger.debug(
            f"Retrieved cached value for key: {key}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return value

    except Exception as e:
        logger.error(f"Failed to get cached value for key {key}: {str(e)}")
        return None


async def cache_delete(key: str, user_context: Optional[str] = None) -> bool:
    """
    Delete a value from Redis cache with optional user context for security.

    Args:
        key: Cache key
        user_context: User ID for security context (optional)

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        result = await redis_client.delete(key)

        if result > 0:
            logger.debug(
                f"Deleted cached value for key: {key}"
                + (f" (user: {user_context})" if user_context else "")
            )
            return True
        else:
            logger.debug(
                f"No cached value found for key: {key}"
                + (f" (user: {user_context})" if user_context else "")
            )
            return False

    except Exception as e:
        logger.error(f"Failed to delete cached value for key {key}: {str(e)}")
        return False


async def cache_exists(key: str, user_context: Optional[str] = None) -> bool:
    """
    Check if a key exists in Redis cache with optional user context.

    Args:
        key: Cache key
        user_context: User ID for security context (optional)

    Returns:
        True if key exists, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        result = await redis_client.exists(key)
        return result > 0

    except Exception as e:
        logger.error(f"Failed to check if key exists {key}: {str(e)}")
        return False


async def cache_expire(
    key: str, ttl_seconds: int, user_context: Optional[str] = None
) -> bool:
    """
    Set expiration time for a key with optional user context.

    Args:
        key: Cache key
        ttl_seconds: Time to live in seconds
        user_context: User ID for security context (optional)

    Returns:
        True if expiration set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        result = await redis_client.expire(key, ttl_seconds)

        if result:
            logger.debug(
                f"Set expiration for key {key}: {ttl_seconds}s"
                + (f" (user: {user_context})" if user_context else "")
            )
            return True
        else:
            logger.debug(
                f"Key not found for expiration: {key}"
                + (f" (user: {user_context})" if user_context else "")
            )
            return False

    except Exception as e:
        logger.error(f"Failed to set expiration for key {key}: {str(e)}")
        return False


async def cache_keys(pattern: str, user_context: Optional[str] = None) -> List[str]:
    """
    Get all keys matching a pattern with optional user context.

    Args:
        pattern: Key pattern (e.g., "user:*" or "*")
        user_context: User ID for security context (optional)

    Returns:
        List of matching keys
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to pattern if provided for security
        if user_context:
            pattern = f"user:{user_context}:{pattern}"

        keys = await redis_client.keys(pattern)

        # Decode bytes to strings
        result_keys = [
            key.decode("utf-8") if isinstance(key, bytes) else key for key in keys
        ]

        # Remove user context prefix from results if it was added
        if user_context:
            prefix = f"user:{user_context}:"
            result_keys = [
                key.replace(prefix, "") for key in result_keys if key.startswith(prefix)
            ]

        return result_keys

    except Exception as e:
        logger.error(f"Failed to get keys for pattern {pattern}: {str(e)}")
        return []


async def cache_increment(
    key: str, amount: int = 1, user_context: Optional[str] = None
) -> Optional[int]:
    """
    Increment a numeric value in cache with optional user context.

    Args:
        key: Cache key
        amount: Amount to increment by
        user_context: User ID for security context (optional)

    Returns:
        New value after increment, None if failed
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        result = await redis_client.incrby(key, amount)

        logger.debug(
            f"Incremented key {key} by {amount}, new value: {result}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return result

    except Exception as e:
        logger.error(f"Failed to increment key {key}: {str(e)}")
        return None


async def cache_decrement(
    key: str, amount: int = 1, user_context: Optional[str] = None
) -> Optional[int]:
    """
    Decrement a numeric value in cache with optional user context.

    Args:
        key: Cache key
        amount: Amount to decrement by
        user_context: User ID for security context (optional)

    Returns:
        New value after decrement, None if failed
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        result = await redis_client.decrby(key, amount)

        logger.debug(
            f"Decremented key {key} by {amount}, new value: {result}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return result

    except Exception as e:
        logger.error(f"Failed to decrement key {key}: {str(e)}")
        return None


async def cache_list_push(
    key: str,
    value: Union[str, Dict],
    max_length: Optional[int] = None,
    user_context: Optional[str] = None,
) -> bool:
    """
    Push a value to a Redis list with optional user context.

    Args:
        key: List key
        value: Value to push
        max_length: Maximum list length (will trim if exceeded)
        user_context: User ID for security context (optional)

    Returns:
        True if pushed successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        # Serialize value if not string
        if isinstance(value, dict):
            value = json.dumps(value)

        await redis_client.lpush(key, value)

        # Trim list if max_length specified
        if max_length:
            await redis_client.ltrim(key, 0, max_length - 1)

        logger.debug(
            f"Pushed value to list {key}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return True

    except Exception as e:
        logger.error(f"Failed to push to list {key}: {str(e)}")
        return False


async def cache_list_get(
    key: str,
    start: int = 0,
    end: int = -1,
    parse_json: bool = True,
    user_context: Optional[str] = None,
) -> List:
    """
    Get values from a Redis list with optional user context.

    Args:
        key: List key
        start: Start index
        end: End index (-1 for all)
        parse_json: Whether to parse JSON strings
        user_context: User ID for security context (optional)

    Returns:
        List of values
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        values = await redis_client.lrange(key, start, end)

        result = []
        for value in values:
            # Decode bytes to string
            if isinstance(value, bytes):
                value = value.decode("utf-8")

            # Parse JSON if requested
            if parse_json and isinstance(value, str):
                try:
                    if value.startswith(("{", "[")):
                        value = json.loads(value)
                except json.JSONDecodeError:
                    pass

            result.append(value)

        logger.debug(
            f"Retrieved {len(result)} values from list {key}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get list {key}: {str(e)}")
        return []


async def cache_hash_set(
    key: str, field: str, value: Union[str, Dict], user_context: Optional[str] = None
) -> bool:
    """
    Set a field in a Redis hash with optional user context.

    Args:
        key: Hash key
        field: Field name
        value: Field value
        user_context: User ID for security context (optional)

    Returns:
        True if set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        # Serialize value if not string
        if isinstance(value, dict):
            value = json.dumps(value)

        await redis_client.hset(key, field, value)

        logger.debug(
            f"Set hash field {key}:{field}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return True

    except Exception as e:
        logger.error(f"Failed to set hash field {key}:{field}: {str(e)}")
        return False


async def cache_hash_get(
    key: str, field: str, parse_json: bool = True, user_context: Optional[str] = None
) -> Optional[Union[str, Dict]]:
    """
    Get a field from a Redis hash with optional user context.

    Args:
        key: Hash key
        field: Field name
        parse_json: Whether to parse JSON strings
        user_context: User ID for security context (optional)

    Returns:
        Field value if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to key if provided for security
        if user_context:
            key = f"user:{user_context}:{key}"

        value = await redis_client.hget(key, field)

        if value is None:
            return None

        # Decode bytes to string
        if isinstance(value, bytes):
            value = value.decode("utf-8")

        # Parse JSON if requested
        if parse_json and isinstance(value, str):
            try:
                if value.startswith(("{", "[")):
                    value = json.loads(value)
            except json.JSONDecodeError:
                pass

        logger.debug(
            f"Retrieved hash field {key}:{field}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return value

    except Exception as e:
        logger.error(f"Failed to get hash field {key}:{field}: {str(e)}")
        return None


async def cache_cleanup_expired(
    pattern: str = "*", user_context: Optional[str] = None
) -> int:
    """
    Clean up expired keys matching a pattern with optional user context.

    Args:
        pattern: Key pattern to match
        user_context: User ID for security context (optional)

    Returns:
        Number of keys cleaned up
    """
    try:
        redis_client = await get_redis_client()

        # Add user context to pattern if provided for security
        if user_context:
            pattern = f"user:{user_context}:{pattern}"

        keys = await redis_client.keys(pattern)

        cleaned_count = 0
        for key in keys:
            ttl = await redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist (expired)
                cleaned_count += 1

        logger.info(
            f"Found {cleaned_count} expired keys matching pattern: {pattern}"
            + (f" (user: {user_context})" if user_context else "")
        )
        return cleaned_count

    except Exception as e:
        logger.error(f"Failed to cleanup expired keys: {str(e)}")
        return 0


async def get_user_redis_stats(user_id: str) -> Dict[str, Any]:
    """
    Get Redis statistics specific to a user.

    Args:
        user_id: User ID to get stats for

    Returns:
        Dictionary with user-specific Redis statistics
    """
    try:
        redis_client = await get_redis_client()

        # Get all user keys
        user_keys = await cache_keys("*", user_context=user_id)

        # Count different types of data
        memory_keys = [key for key in user_keys if "memories" in key]
        session_keys = [key for key in user_keys if "session" in key]
        cache_keys_count = len(user_keys)

        # Get total memory usage (approximate)
        total_size = 0
        for key in user_keys:
            try:
                # Get memory usage for each key
                memory_usage = await redis_client.memory_usage(f"user:{user_id}:{key}")
                if memory_usage:
                    total_size += memory_usage
            except Exception:
                # Memory usage command might not be available
                pass

        stats = {
            "user_id": user_id,
            "total_keys": cache_keys_count,
            "memory_keys": len(memory_keys),
            "session_keys": len(session_keys),
            "estimated_size_bytes": total_size,
            "last_checked": datetime.utcnow().isoformat(),
        }

        logger.debug(f"Retrieved Redis stats for user {user_id}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get Redis stats for user {user_id}: {str(e)}")
        return {}


async def cache_info() -> Dict[str, Any]:
    """
    Get Redis cache information.

    Returns:
        Dictionary with cache statistics
    """
    try:
        redis_client = await get_redis_client()
        info = await redis_client.info()

        return {
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "authentication_enabled": bool(os.getenv("REDIS_PASSWORD")),
        }

    except Exception as e:
        logger.error(f"Failed to get cache info: {str(e)}")
        return {}
