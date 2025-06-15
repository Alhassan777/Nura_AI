"""
Multi-Layered Cache Manager for Chat Service.
Implements three-layer caching strategy for optimal performance.
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import asdict

from utils.redis_client import (
    cache_get,
    cache_set,
    cache_delete,
    cache_exists,
    get_redis_client,
)
from ..memory.types import MemoryItem, MemoryContext

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-layered cache manager for chat service optimization."""

    def __init__(self):
        self.ttl_strategy = {
            # Layer 1: Raw Data Cache
            "conversation_messages": 14400,  # 4 hours - matches conversation TTL
            "semantic_search_results": 300,  # 5 minutes - Pinecone data stable
            "user_profile": 3600,  # 1 hour - slow changing data
            # Layer 2: Processed Results Cache
            "processed_conversation": 240,  # 4 minutes
            "processed_longterm": 300,  # 5 minutes
            "crisis_assessment": 120,  # 2 minutes
            # Layer 3: Combined Context Cache
            "enriched_context": 180,  # 3 minutes - most dynamic
            "mode_context": 180,  # 3 minutes
            "action_plans": 600,  # 10 minutes
            "image_prompts": 600,  # 10 minutes
        }

        # Query normalization patterns
        self.normalization_patterns = {
            r"\b(i\'m|i am|im)\s+": "",
            r"\bfeeling\s+": "feeling ",
            r"\b(anxious|worried|nervous|stressed)\b": "anxious",
            r"\b(sad|depressed|down|low)\b": "sad",
            r"\b(happy|good|great|wonderful)\b": "happy",
            r"\b(how do i|what should i|help me)\b": "help",
            r"\b(cope|coping|deal with|handle)\b": "cope",
        }

    def _generate_cache_key(self, cache_type: str, **kwargs) -> str:
        """Generate consistent cache keys."""
        key_parts = [cache_type]

        # Add required components based on cache type
        if "user_id" in kwargs:
            key_parts.append(f"user:{kwargs['user_id']}")
        if "conversation_id" in kwargs:
            key_parts.append(f"conv:{kwargs['conversation_id']}")
        if "query_hash" in kwargs:
            key_parts.append(f"query:{kwargs['query_hash']}")
        if "mode" in kwargs:
            key_parts.append(f"mode:{kwargs['mode']}")
        if "context_hash" in kwargs:
            key_parts.append(f"ctx:{kwargs['context_hash']}")

        return ":".join(key_parts)

    def _generate_query_hash(self, query: str, user_id: str) -> str:
        """Generate hash for query similarity matching."""
        # Normalize query for better cache hits
        normalized = self._normalize_query(query)

        # Include user context for personalization
        combined = f"{user_id}:{normalized}"

        # Generate short hash for cache key
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _normalize_query(self, query: str) -> str:
        """Normalize queries for better cache hits."""
        if not query:
            return ""

        # Convert to lowercase
        normalized = query.lower().strip()

        # Apply normalization patterns
        for pattern, replacement in self.normalization_patterns.items():
            normalized = re.sub(pattern, replacement, normalized)

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _generate_context_hash(self, **context_components) -> str:
        """Generate hash for context combination."""
        # Create deterministic hash from context components
        context_str = json.dumps(context_components, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]

    async def generate_context_hash(self, user_id: str, message: str) -> str:
        """Generate context hash for caching purposes."""
        return self._generate_context_hash(user_id=user_id, message=message)

    async def get_with_fallback(
        self,
        cache_keys: List[str],
        fallback_func: Callable,
        user_id: str,
        cache_type: str = "default",
    ) -> Any:
        """Try cache layers in order, fallback to function."""

        # Try each cache key in priority order
        for cache_key in cache_keys:
            try:
                cached_data = await cache_get(cache_key, user_context=user_id)
                if cached_data and self._is_cache_fresh(cached_data):
                    logger.debug(f"Cache hit for {cache_key}")
                    return self._deserialize_cached_data(cached_data)
            except Exception as e:
                logger.warning(f"Cache retrieval failed for {cache_key}: {e}")
                continue

        # Cache miss - execute fallback function
        logger.debug(f"Cache miss for {cache_keys}, executing fallback")
        try:
            result = await fallback_func()

            # Cache the result in the primary cache key
            if cache_keys and result is not None:
                await self._cache_result(cache_keys[0], result, user_id, cache_type)

            return result

        except Exception as e:
            logger.error(f"Fallback function failed: {e}")
            return None

    async def _cache_result(
        self, cache_key: str, result: Any, user_id: str, cache_type: str
    ) -> bool:
        """Cache result with appropriate TTL."""
        try:
            # Get TTL for this cache type
            ttl = self.ttl_strategy.get(cache_type, 300)  # Default 5 minutes

            # Serialize result
            serialized_data = self._serialize_data_for_cache(result)

            # Add metadata
            cache_data = {
                "data": serialized_data,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_type": cache_type,
                "ttl": ttl,
            }

            # Store in cache
            success = await cache_set(
                cache_key, cache_data, ttl_seconds=ttl, user_context=user_id
            )

            if success:
                logger.debug(f"Cached result for {cache_key} with TTL {ttl}s")
            else:
                logger.warning(f"Failed to cache result for {cache_key}")

            return success

        except Exception as e:
            logger.error(f"Failed to cache result for {cache_key}: {e}")
            return False

    def _is_cache_fresh(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still fresh."""
        try:
            if not isinstance(cached_data, dict):
                return False

            cached_at_str = cached_data.get("cached_at")
            ttl = cached_data.get("ttl", 300)

            if not cached_at_str:
                return False

            cached_at = datetime.fromisoformat(cached_at_str)
            expiry_time = cached_at + timedelta(seconds=ttl)

            return datetime.utcnow() < expiry_time

        except Exception as e:
            logger.warning(f"Error checking cache freshness: {e}")
            return False

    def _serialize_data_for_cache(self, data: Any) -> Any:
        """Serialize data for caching."""
        if isinstance(data, (dict, list, str, int, float, bool)):
            return data
        elif hasattr(data, "__dict__"):
            # Convert dataclass or object to dict
            try:
                return asdict(data)
            except:
                return data.__dict__
        elif isinstance(data, MemoryContext):
            return {
                "short_term": [asdict(item) for item in data.short_term],
                "long_term": [asdict(item) for item in data.long_term],
                "digest": data.digest,
            }
        elif isinstance(data, list) and data and isinstance(data[0], MemoryItem):
            return [asdict(item) for item in data]
        else:
            # Fallback to string representation
            return str(data)

    def _deserialize_cached_data(self, cached_data: Dict[str, Any]) -> Any:
        """Deserialize cached data."""
        try:
            return cached_data.get("data")
        except Exception as e:
            logger.warning(f"Error deserializing cached data: {e}")
            return None

    # Layer 1: Raw Data Cache Methods
    async def get_conversation_messages_cached(
        self, conversation_id: str, fallback_func: Callable
    ) -> List[MemoryItem]:
        """Get cached conversation messages."""
        cache_key = self._generate_cache_key(
            "conversation_messages", conversation_id=conversation_id
        )

        return await self.get_with_fallback(
            [cache_key],
            fallback_func,
            user_id="system",  # Conversation cache is not user-specific
            cache_type="conversation_messages",
        )

    async def get_semantic_search_cached(
        self, user_id: str, query: str, fallback_func: Callable
    ) -> List[MemoryItem]:
        """Get cached semantic search results."""
        query_hash = self._generate_query_hash(query, user_id)
        cache_key = self._generate_cache_key(
            "semantic_search_results", user_id=user_id, query_hash=query_hash
        )

        return await self.get_with_fallback(
            [cache_key],
            fallback_func,
            user_id=user_id,
            cache_type="semantic_search_results",
        )

    async def get_user_profile_cached(
        self, user_id: str, fallback_func: Callable
    ) -> Dict[str, Any]:
        """Get cached user profile."""
        cache_key = self._generate_cache_key("user_profile", user_id=user_id)

        return await self.get_with_fallback(
            [cache_key], fallback_func, user_id=user_id, cache_type="user_profile"
        )

    # Layer 2: Processed Results Cache Methods
    async def get_processed_conversation_cached(
        self, conversation_id: str, fallback_func: Callable
    ) -> str:
        """Get cached processed conversation context."""
        cache_key = self._generate_cache_key(
            "processed_conversation", conversation_id=conversation_id
        )

        return await self.get_with_fallback(
            [cache_key],
            fallback_func,
            user_id="system",
            cache_type="processed_conversation",
        )

    async def get_processed_longterm_cached(
        self, user_id: str, query: str, fallback_func: Callable
    ) -> str:
        """Get cached processed long-term context."""
        query_hash = self._generate_query_hash(query, user_id)
        cache_key = self._generate_cache_key(
            "processed_longterm", user_id=user_id, query_hash=query_hash
        )

        return await self.get_with_fallback(
            [cache_key], fallback_func, user_id=user_id, cache_type="processed_longterm"
        )

    async def get_crisis_assessment_cached(
        self, message: str, fallback_func: Callable
    ) -> Dict[str, Any]:
        """Get cached crisis assessment."""
        message_hash = hashlib.sha256(message.encode()).hexdigest()[:16]
        cache_key = self._generate_cache_key(
            "crisis_assessment", message_hash=message_hash
        )

        return await self.get_with_fallback(
            [cache_key], fallback_func, user_id="system", cache_type="crisis_assessment"
        )

    # Layer 3: Combined Context Cache Methods
    async def get_enriched_context_cached(
        self, user_id: str, query: str, conversation_id: str, fallback_func: Callable
    ) -> MemoryContext:
        """Get cached enriched context."""
        context_hash = self._generate_context_hash(
            user_id=user_id,
            query=self._normalize_query(query),
            conversation_id=conversation_id,
        )

        cache_key = self._generate_cache_key(
            "enriched_context", user_id=user_id, context_hash=context_hash
        )

        return await self.get_with_fallback(
            [cache_key], fallback_func, user_id=user_id, cache_type="enriched_context"
        )

    async def get_mode_context_cached(
        self,
        mode: str,
        user_id: str,
        query: str,
        conversation_id: str,
        fallback_func: Callable,
    ) -> str:
        """Get cached mode-specific context."""
        context_hash = self._generate_context_hash(
            mode=mode,
            user_id=user_id,
            query=self._normalize_query(query),
            conversation_id=conversation_id,
        )

        cache_key = self._generate_cache_key(
            "mode_context", mode=mode, user_id=user_id, context_hash=context_hash
        )

        return await self.get_with_fallback(
            [cache_key], fallback_func, user_id=user_id, cache_type="mode_context"
        )

    # Cache Invalidation Methods
    async def invalidate_user_cache(self, user_id: str, patterns: List[str] = None):
        """Invalidate cache entries for a user."""
        if patterns is None:
            patterns = ["*"]

        try:
            redis_client = await get_redis_client()

            for pattern in patterns:
                # Create user-specific pattern
                user_pattern = f"user:{user_id}:*{pattern}*"

                # Get matching keys
                keys = await redis_client.keys(user_pattern)

                if keys:
                    # Delete keys
                    await redis_client.delete(*keys)
                    logger.info(
                        f"Invalidated {len(keys)} cache entries for user {user_id} with pattern {pattern}"
                    )

        except Exception as e:
            logger.error(f"Failed to invalidate user cache for {user_id}: {e}")

    async def invalidate_conversation_cache(self, conversation_id: str):
        """Invalidate cache entries for a conversation."""
        try:
            patterns = [
                f"conversation_messages:conv:{conversation_id}",
                f"processed_conversation:conv:{conversation_id}",
                f"enriched_context:*:ctx:*{conversation_id}*",
                f"mode_context:*:ctx:*{conversation_id}*",
            ]

            redis_client = await get_redis_client()

            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    logger.info(
                        f"Invalidated {len(keys)} cache entries for conversation {conversation_id}"
                    )

        except Exception as e:
            logger.error(
                f"Failed to invalidate conversation cache for {conversation_id}: {e}"
            )

    async def get_cache_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis_client = await get_redis_client()

            stats = {"total_keys": 0, "by_type": {}, "memory_usage": "unknown"}

            # Get pattern based on user_id
            pattern = f"user:{user_id}:*" if user_id else "*"
            keys = await redis_client.keys(pattern)

            stats["total_keys"] = len(keys)

            # Count by cache type
            for key in keys:
                key_parts = key.split(":")
                if len(key_parts) >= 3:
                    cache_type = key_parts[2] if user_id else key_parts[0]
                    stats["by_type"][cache_type] = (
                        stats["by_type"].get(cache_type, 0) + 1
                    )

            return stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    # Additional methods for multi-modal chat integration
    async def get_enriched_context(
        self, user_id: str, context_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get enriched context from cache."""
        cache_key = self._generate_cache_key(
            "enriched_context", user_id=user_id, context_hash=context_hash
        )
        try:
            cached_data = await cache_get(cache_key, user_context=user_id)
            if cached_data and self._is_cache_fresh(cached_data):
                return self._deserialize_cached_data(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting enriched context: {e}")
            return None

    async def get_conversation_messages(
        self, conversation_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get conversation messages from cache."""
        cache_key = self._generate_cache_key(
            "conversation_messages", conversation_id=conversation_id
        )
        try:
            cached_data = await cache_get(cache_key, user_context="system")
            if cached_data and self._is_cache_fresh(cached_data):
                return self._deserialize_cached_data(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return None

    async def cache_background_results(
        self, task_id: str, results: Dict[str, Any]
    ) -> bool:
        """Cache background processing results."""
        cache_key = f"background_results:{task_id}"
        try:
            # Cache for 1 hour
            cache_data = {
                "data": results,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_type": "background_results",
                "ttl": 3600,
            }

            success = await cache_set(
                cache_key, cache_data, ttl_seconds=3600, user_context="system"
            )
            if success:
                logger.debug(f"Cached background results for task {task_id}")
            return success
        except Exception as e:
            logger.error(f"Error caching background results for {task_id}: {e}")
            return False

    async def get_background_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get background processing results from cache."""
        cache_key = f"background_results:{task_id}"
        try:
            cached_data = await cache_get(cache_key, user_context="system")
            if cached_data and self._is_cache_fresh(cached_data):
                return self._deserialize_cached_data(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting background results for {task_id}: {e}")
            return None

    async def clear_conversation_cache(self, conversation_id: str) -> bool:
        """Clear conversation-specific cache entries."""
        try:
            await self.invalidate_conversation_cache(conversation_id)
            return True
        except Exception as e:
            logger.error(
                f"Error clearing conversation cache for {conversation_id}: {e}"
            )
            return False

    async def clear_user_cache(self, user_id: str) -> int:
        """Clear user-specific cache entries and return count."""
        try:
            redis_client = await get_redis_client()
            pattern = f"*user:{user_id}*"
            keys = await redis_client.keys(pattern)

            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries for user {user_id}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing user cache for {user_id}: {e}")
            return 0

    async def warm_user_cache(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        priority: str = "normal",
    ) -> bool:
        """Warm cache for user (placeholder for future implementation)."""
        try:
            logger.info(
                f"Cache warming initiated for user {user_id} with priority {priority}"
            )
            # This would implement cache warming logic
            return True
        except Exception as e:
            logger.error(f"Error warming cache for user {user_id}: {e}")
            return False

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        try:
            redis_client = await get_redis_client()
            info = await redis_client.info()

            return {
                "redis_memory_used": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "redis_total_commands_processed": info.get(
                    "total_commands_processed", 0
                ),
                "cache_hit_rate": "unknown",  # Would need to track this
                "average_response_time": "unknown",  # Would need to track this
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

    async def get_user_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific cache statistics."""
        return await self.get_cache_stats(user_id)

    async def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()

            return {
                "status": "healthy",
                "redis_connected": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def cache_enriched_context(
        self, user_id: str, context_hash: str, context_data: Dict[str, Any]
    ) -> bool:
        """Cache enriched context data."""
        cache_key = self._generate_cache_key(
            "enriched_context", user_id=user_id, context_hash=context_hash
        )
        try:
            return await self._cache_result(
                cache_key, context_data, user_id, "enriched_context"
            )
        except Exception as e:
            logger.error(f"Error caching enriched context: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()
