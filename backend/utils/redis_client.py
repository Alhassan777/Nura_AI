"""
Redis Client Utilities
Centralized Redis operations for caching, session management, and data storage.
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
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url)
        logger.info(f"Initialized Redis client: {redis_url}")
    return _redis_client


async def cache_set(
    key: str, value: Union[str, Dict, List], ttl_seconds: Optional[int] = None
) -> bool:
    """
    Set a value in Redis cache.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized if not string)
        ttl_seconds: Time to live in seconds (optional)

    Returns:
        True if set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Serialize value if not string
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        if ttl_seconds:
            await redis_client.setex(key, ttl_seconds, value)
        else:
            await redis_client.set(key, value)

        logger.debug(f"Cached value for key: {key}")
        return True

    except Exception as e:
        logger.error(f"Failed to cache value for key {key}: {str(e)}")
        return False


async def cache_get(
    key: str, parse_json: bool = True
) -> Optional[Union[str, Dict, List]]:
    """
    Get a value from Redis cache.

    Args:
        key: Cache key
        parse_json: Whether to parse JSON strings back to objects

    Returns:
        Cached value if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()
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

        logger.debug(f"Retrieved cached value for key: {key}")
        return value

    except Exception as e:
        logger.error(f"Failed to get cached value for key {key}: {str(e)}")
        return None


async def cache_delete(key: str) -> bool:
    """
    Delete a value from Redis cache.

    Args:
        key: Cache key

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        result = await redis_client.delete(key)

        if result > 0:
            logger.debug(f"Deleted cached value for key: {key}")
            return True
        else:
            logger.debug(f"No cached value found for key: {key}")
            return False

    except Exception as e:
        logger.error(f"Failed to delete cached value for key {key}: {str(e)}")
        return False


async def cache_exists(key: str) -> bool:
    """
    Check if a key exists in Redis cache.

    Args:
        key: Cache key

    Returns:
        True if key exists, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        result = await redis_client.exists(key)
        return result > 0

    except Exception as e:
        logger.error(f"Failed to check if key exists {key}: {str(e)}")
        return False


async def cache_expire(key: str, ttl_seconds: int) -> bool:
    """
    Set expiration time for a key.

    Args:
        key: Cache key
        ttl_seconds: Time to live in seconds

    Returns:
        True if expiration set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        result = await redis_client.expire(key, ttl_seconds)

        if result:
            logger.debug(f"Set expiration for key {key}: {ttl_seconds}s")
            return True
        else:
            logger.debug(f"Key not found for expiration: {key}")
            return False

    except Exception as e:
        logger.error(f"Failed to set expiration for key {key}: {str(e)}")
        return False


async def cache_keys(pattern: str) -> List[str]:
    """
    Get all keys matching a pattern.

    Args:
        pattern: Key pattern (e.g., "user:*")

    Returns:
        List of matching keys
    """
    try:
        redis_client = await get_redis_client()
        keys = await redis_client.keys(pattern)

        # Decode bytes to strings
        return [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]

    except Exception as e:
        logger.error(f"Failed to get keys for pattern {pattern}: {str(e)}")
        return []


async def cache_increment(key: str, amount: int = 1) -> Optional[int]:
    """
    Increment a numeric value in cache.

    Args:
        key: Cache key
        amount: Amount to increment by

    Returns:
        New value after increment, None if failed
    """
    try:
        redis_client = await get_redis_client()
        result = await redis_client.incrby(key, amount)

        logger.debug(f"Incremented key {key} by {amount}, new value: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to increment key {key}: {str(e)}")
        return None


async def cache_decrement(key: str, amount: int = 1) -> Optional[int]:
    """
    Decrement a numeric value in cache.

    Args:
        key: Cache key
        amount: Amount to decrement by

    Returns:
        New value after decrement, None if failed
    """
    try:
        redis_client = await get_redis_client()
        result = await redis_client.decrby(key, amount)

        logger.debug(f"Decremented key {key} by {amount}, new value: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to decrement key {key}: {str(e)}")
        return None


async def cache_list_push(
    key: str, value: Union[str, Dict], max_length: Optional[int] = None
) -> bool:
    """
    Push a value to a Redis list.

    Args:
        key: List key
        value: Value to push
        max_length: Maximum list length (will trim if exceeded)

    Returns:
        True if pushed successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Serialize value if not string
        if isinstance(value, dict):
            value = json.dumps(value)

        await redis_client.lpush(key, value)

        # Trim list if max_length specified
        if max_length:
            await redis_client.ltrim(key, 0, max_length - 1)

        logger.debug(f"Pushed value to list {key}")
        return True

    except Exception as e:
        logger.error(f"Failed to push to list {key}: {str(e)}")
        return False


async def cache_list_get(
    key: str, start: int = 0, end: int = -1, parse_json: bool = True
) -> List:
    """
    Get values from a Redis list.

    Args:
        key: List key
        start: Start index
        end: End index (-1 for all)
        parse_json: Whether to parse JSON strings

    Returns:
        List of values
    """
    try:
        redis_client = await get_redis_client()
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

        logger.debug(f"Retrieved {len(result)} values from list {key}")
        return result

    except Exception as e:
        logger.error(f"Failed to get list {key}: {str(e)}")
        return []


async def cache_hash_set(key: str, field: str, value: Union[str, Dict]) -> bool:
    """
    Set a field in a Redis hash.

    Args:
        key: Hash key
        field: Field name
        value: Field value

    Returns:
        True if set successfully, False otherwise
    """
    try:
        redis_client = await get_redis_client()

        # Serialize value if not string
        if isinstance(value, dict):
            value = json.dumps(value)

        await redis_client.hset(key, field, value)

        logger.debug(f"Set hash field {key}:{field}")
        return True

    except Exception as e:
        logger.error(f"Failed to set hash field {key}:{field}: {str(e)}")
        return False


async def cache_hash_get(
    key: str, field: str, parse_json: bool = True
) -> Optional[Union[str, Dict]]:
    """
    Get a field from a Redis hash.

    Args:
        key: Hash key
        field: Field name
        parse_json: Whether to parse JSON strings

    Returns:
        Field value if found, None otherwise
    """
    try:
        redis_client = await get_redis_client()
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

        logger.debug(f"Retrieved hash field {key}:{field}")
        return value

    except Exception as e:
        logger.error(f"Failed to get hash field {key}:{field}: {str(e)}")
        return None


async def cache_cleanup_expired(pattern: str = "*") -> int:
    """
    Clean up expired keys matching a pattern.

    Args:
        pattern: Key pattern to match

    Returns:
        Number of keys cleaned up
    """
    try:
        redis_client = await get_redis_client()
        keys = await redis_client.keys(pattern)

        cleaned_count = 0
        for key in keys:
            ttl = await redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist (expired)
                cleaned_count += 1

        logger.info(f"Found {cleaned_count} expired keys matching pattern: {pattern}")
        return cleaned_count

    except Exception as e:
        logger.error(f"Failed to cleanup expired keys: {str(e)}")
        return 0


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
        }

    except Exception as e:
        logger.error(f"Failed to get cache info: {str(e)}")
        return {}
