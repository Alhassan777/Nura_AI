"""
Redis Storage Layer for Short-term Memory Management.

Handles temporary storage of conversation elements before they are processed
for long-term storage. Provides rapid access for real-time conversation flow.

SECURE: Works with validated user_id from JWT session tokens.
"""

import redis
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict

# Import centralized Redis utilities
from utils.redis_client import (
    get_redis_client,
    cache_list_push,
    cache_list_get,
    cache_delete,
    get_user_redis_stats,
)

from ..types import MemoryItem

# Set up logging
logger = logging.getLogger(__name__)


class RedisStore:
    """
    SIMPLIFIED Redis Store for secure short-term memory storage.
    All operations are secure by default since user_id comes from validated JWT.
    """

    def __init__(self):
        self.client = None
        self.redis_available = True
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure Redis connection is initialized (lazy initialization)."""
        if not self._initialized:
            try:
                self.client = await get_redis_client()
                await self.client.ping()
                self._initialized = True
                self.redis_available = True
                logger.info("Redis store initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis store: {e}")
                self.redis_available = False
                self.client = None
                # Don't raise here - let individual operations handle gracefully

    async def initialize(self):
        """Initialize Redis connection (public method for explicit initialization)."""
        return await self._ensure_initialized()

    def _get_user_key(self, user_id: str, suffix: str = "") -> str:
        """
        Generate user-specific Redis key with proper namespacing.

        Args:
            user_id: Validated user ID from JWT
            suffix: Optional key suffix

        Returns:
            Namespaced Redis key
        """
        base_key = f"user:{user_id}:memories"
        return f"{base_key}:{suffix}" if suffix else base_key

    def _get_conversation_key(self, conversation_id: str, suffix: str = "") -> str:
        """
        Generate conversation-specific Redis key for short-term memory.

        Args:
            conversation_id: Conversation ID
            suffix: Optional key suffix

        Returns:
            Namespaced Redis key for conversation memory
        """
        base_key = f"conversation:{conversation_id}:memories"
        return f"{base_key}:{suffix}" if suffix else base_key

    async def store_memory(self, user_id: str, memory: MemoryItem) -> bool:
        """
        Store a memory in Redis with conversation isolation.

        Args:
            user_id: Validated user ID from JWT
            memory: Memory item to store

        Returns:
            Success status
        """
        try:
            await self._ensure_initialized()

            if not self.redis_available or not self.client:
                logger.warning("Redis not available for memory storage")
                return False

            # Extract conversation_id from metadata
            conversation_id = memory.metadata.get("conversation_id")

            if conversation_id:
                # Use conversation-scoped storage for chat memories
                memory_key = self._get_conversation_key(
                    conversation_id, f"memory:{memory.id}"
                )
                list_key = self._get_conversation_key(conversation_id, "list")
                ttl_hours = 4  # Shorter TTL for conversation memory
            else:
                # Fallback to user-scoped for non-chat memories
                memory_key = self._get_user_key(user_id, f"memory:{memory.id}")
                list_key = self._get_user_key(user_id, "list")
                ttl_hours = 24

            memory_data = {
                "id": memory.id,
                "content": memory.content,
                "type": memory.type,
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata,
                "user_id": user_id,  # Ensure user ownership
                "conversation_id": conversation_id,  # Track conversation
            }

            # Store individual memory
            await self.client.setex(
                memory_key,
                timedelta(hours=ttl_hours),
                json.dumps(memory_data),
            )

            # Add to conversation's memory list
            await self.client.lpush(list_key, memory.id)
            await self.client.expire(list_key, timedelta(hours=ttl_hours))

            logger.debug(
                f"Stored memory {memory.id} for {'conversation ' + conversation_id if conversation_id else 'user ' + user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store memory for user {user_id}: {e}")
            return False

    async def get_conversation_memories(
        self, conversation_id: str, limit: int = 50
    ) -> List[MemoryItem]:
        """
        Get recent memories for a specific conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of memories to retrieve

        Returns:
            List of conversation's memories
        """
        try:
            await self._ensure_initialized()

            if not self.redis_available or not self.client:
                logger.warning("Redis not available for memory retrieval")
                return []

            # Get conversation's memory IDs
            list_key = self._get_conversation_key(conversation_id, "list")
            memory_ids = await self.client.lrange(list_key, 0, limit - 1)

            memories = []
            for memory_id in memory_ids:
                memory_id = (
                    memory_id.decode() if isinstance(memory_id, bytes) else memory_id
                )
                memory_key = self._get_conversation_key(
                    conversation_id, f"memory:{memory_id}"
                )

                memory_data = await self.client.get(memory_key)
                if memory_data:
                    try:
                        data = json.loads(memory_data)
                        memory = MemoryItem(
                            id=data["id"],
                            content=data["content"],
                            type=data["type"],
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            metadata=data.get("metadata", {}),
                        )
                        memories.append(memory)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid memory data for {memory_id}: {e}")

            logger.debug(
                f"Retrieved {len(memories)} memories for conversation {conversation_id}"
            )
            return memories

        except Exception as e:
            logger.error(
                f"Failed to get memories for conversation {conversation_id}: {e}"
            )
            return []

    async def get_user_memories(
        self, user_id: str, limit: int = 50
    ) -> List[MemoryItem]:
        """
        Get recent memories for a specific user (legacy method, now returns empty for chat memories).

        Args:
            user_id: Validated user ID from JWT
            limit: Maximum number of memories to retrieve

        Returns:
            List of user's non-conversation memories
        """
        try:
            await self._ensure_initialized()

            if not self.redis_available or not self.client:
                logger.warning("Redis not available for memory retrieval")
                return []

            # Get user's memory IDs (non-conversation memories only)
            user_list_key = self._get_user_key(user_id, "list")
            memory_ids = await self.client.lrange(user_list_key, 0, limit - 1)

            memories = []
            for memory_id in memory_ids:
                memory_id = (
                    memory_id.decode() if isinstance(memory_id, bytes) else memory_id
                )
                memory_key = self._get_user_key(user_id, f"memory:{memory_id}")

                memory_data = await self.client.get(memory_key)
                if memory_data:
                    try:
                        data = json.loads(memory_data)
                        # Verify memory belongs to user (security check)
                        if data.get("user_id") == user_id:
                            memory = MemoryItem(
                                id=data["id"],
                                content=data["content"],
                                type=data["type"],
                                timestamp=datetime.fromisoformat(data["timestamp"]),
                                metadata=data.get("metadata", {}),
                            )
                            memories.append(memory)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid memory data for {memory_id}: {e}")

            logger.debug(f"Retrieved {len(memories)} user memories for user {user_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {e}")
            return []

    async def get_memory(self, user_id: str, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory for a user.

        Args:
            user_id: Validated user ID from JWT
            memory_id: Memory ID to retrieve

        Returns:
            Memory item if found and owned by user
        """
        try:
            if not self.redis_available or not self.client:
                return None

            memory_key = self._get_user_key(user_id, f"memory:{memory_id}")
            memory_data = await self.client.get(memory_key)

            if memory_data:
                data = json.loads(memory_data)
                # Verify ownership
                if data.get("user_id") == user_id:
                    return MemoryItem(
                        id=data["id"],
                        content=data["content"],
                        type=data["type"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        metadata=data.get("metadata", {}),
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to get memory {memory_id} for user {user_id}: {e}")
            return None

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a specific memory for a user.

        Args:
            user_id: Validated user ID from JWT
            memory_id: Memory ID to delete

        Returns:
            Success status
        """
        try:
            if not self.redis_available or not self.client:
                return False

            # Remove from user's memory list
            user_list_key = self._get_user_key(user_id, "list")
            await self.client.lrem(user_list_key, 0, memory_id)

            # Delete individual memory
            memory_key = self._get_user_key(user_id, f"memory:{memory_id}")
            deleted = await self.client.delete(memory_key)

            logger.debug(f"Deleted memory {memory_id} for user {user_id}")
            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id} for user {user_id}: {e}")
            return False

    async def clear_conversation_memories(self, conversation_id: str) -> bool:
        """
        Clear all memories for a specific conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Success status
        """
        try:
            if not self.redis_available or not self.client:
                return False

            # Get all conversation memory IDs
            list_key = self._get_conversation_key(conversation_id, "list")
            memory_ids = await self.client.lrange(list_key, 0, -1)

            # Delete individual memories
            deleted_count = 0
            for memory_id in memory_ids:
                memory_id = (
                    memory_id.decode() if isinstance(memory_id, bytes) else memory_id
                )
                memory_key = self._get_conversation_key(
                    conversation_id, f"memory:{memory_id}"
                )
                if await self.client.delete(memory_key):
                    deleted_count += 1

            # Delete the list
            await self.client.delete(list_key)

            logger.info(
                f"Cleared {deleted_count} memories for conversation {conversation_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to clear memories for conversation {conversation_id}: {e}"
            )
            return False

    async def end_conversation_session(
        self, conversation_id: str, user_id: str, promote_important: bool = True
    ) -> Dict[str, Any]:
        """
        End a conversation session, optionally promoting important memories to long-term storage.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for security)
            promote_important: Whether to identify and return important memories for promotion

        Returns:
            Dictionary with session end results and memories to promote
        """
        try:
            result = {
                "conversation_id": conversation_id,
                "memories_cleared": 0,
                "memories_to_promote": [],
                "session_ended": False,
            }

            if not self.redis_available or not self.client:
                return result

            # Get conversation memories before clearing
            memories = await self.get_conversation_memories(conversation_id)
            result["memories_cleared"] = len(memories)

            # Identify important memories for promotion if requested
            if promote_important and memories:
                important_memories = []
                for memory in memories:
                    # Check if memory should be promoted based on metadata
                    metadata = memory.metadata or {}
                    should_promote = (
                        metadata.get("should_store_long_term", False)
                        or metadata.get("emotional_resonance")
                        in ["profound", "meaningful"]
                        or metadata.get("significance_level") in ["critical", "high"]
                        or metadata.get("memory_nature") == "emotional_anchor"
                    )

                    if should_promote:
                        important_memories.append(
                            {
                                "memory": memory,
                                "reason": "identified_as_important_during_conversation",
                            }
                        )

                result["memories_to_promote"] = important_memories

            # Clear conversation memories
            cleared = await self.clear_conversation_memories(conversation_id)
            result["session_ended"] = cleared

            logger.info(
                f"Ended conversation session {conversation_id}: cleared {result['memories_cleared']} memories, {len(result['memories_to_promote'])} marked for promotion"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to end conversation session {conversation_id}: {e}")
            return {"error": str(e), "session_ended": False}

    async def clear_user_memories(self, user_id: str) -> bool:
        """
        Clear all memories for a specific user.

        Args:
            user_id: Validated user ID from JWT

        Returns:
            Success status
        """
        try:
            if not self.redis_available or not self.client:
                return False

            # Get all user memory keys
            pattern = self._get_user_key(user_id, "*")
            keys = await self.client.keys(pattern)

            if keys:
                await self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} Redis keys for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to clear memories for user {user_id}: {e}")
            return False

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get Redis storage statistics for a user.

        Args:
            user_id: Validated user ID from JWT

        Returns:
            User's Redis statistics
        """
        try:
            if not self.redis_available or not self.client:
                return {"error": "Redis not available"}

            # Use the centralized stats function
            stats = await get_user_redis_stats(self.client, user_id)
            return stats

        except Exception as e:
            logger.error(f"Failed to get Redis stats for user {user_id}: {e}")
            return {"error": str(e)}

    async def search_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[MemoryItem]:
        """
        Simple text search in user's Redis memories.

        Args:
            user_id: Validated user ID from JWT
            query: Search query
            limit: Maximum results

        Returns:
            Matching memories
        """
        try:
            memories = await self.get_user_memories(user_id, limit=100)
            query_lower = query.lower()

            # Simple text search
            matching_memories = [
                memory for memory in memories if query_lower in memory.content.lower()
            ]

            return matching_memories[:limit]

        except Exception as e:
            logger.error(f"Failed to search memories for user {user_id}: {e}")
            return []

    async def store_pending_consent(
        self, user_id: str, memory_data: Dict[str, Any]
    ) -> str:
        """
        Store memory pending consent decision.

        Args:
            user_id: Validated user ID from JWT
            memory_data: Memory data awaiting consent

        Returns:
            Consent request ID
        """
        try:
            if not self.redis_available or not self.client:
                return ""

            consent_id = f"consent_{datetime.now().timestamp()}"
            consent_key = self._get_user_key(user_id, f"pending_consent:{consent_id}")

            consent_data = {
                **memory_data,
                "user_id": user_id,
                "consent_id": consent_id,
                "created_at": datetime.now().isoformat(),
            }

            # Store with 7-day expiration for consent
            await self.client.setex(
                consent_key, timedelta(days=7), json.dumps(consent_data)
            )

            # Add to pending consent list
            pending_list_key = self._get_user_key(user_id, "pending_consent_list")
            await self.client.lpush(pending_list_key, consent_id)
            await self.client.expire(pending_list_key, timedelta(days=7))

            logger.debug(f"Stored pending consent {consent_id} for user {user_id}")
            return consent_id

        except Exception as e:
            logger.error(f"Failed to store pending consent for user {user_id}: {e}")
            return ""

    async def get_pending_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all pending consent requests for a user.

        Args:
            user_id: Validated user ID from JWT

        Returns:
            List of pending consent requests
        """
        try:
            if not self.redis_available or not self.client:
                return []

            pending_list_key = self._get_user_key(user_id, "pending_consent_list")
            consent_ids = await self.client.lrange(pending_list_key, 0, -1)

            pending_consents = []
            for consent_id in consent_ids:
                consent_id = (
                    consent_id.decode() if isinstance(consent_id, bytes) else consent_id
                )
                consent_key = self._get_user_key(
                    user_id, f"pending_consent:{consent_id}"
                )

                consent_data = await self.client.get(consent_key)
                if consent_data:
                    try:
                        data = json.loads(consent_data)
                        # Verify ownership
                        if data.get("user_id") == user_id:
                            pending_consents.append(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid consent data for {consent_id}: {e}")

            return pending_consents

        except Exception as e:
            logger.error(f"Failed to get pending consents for user {user_id}: {e}")
            return []

    async def resolve_consent(self, user_id: str, consent_id: str) -> bool:
        """
        Remove resolved consent request.

        Args:
            user_id: Validated user ID from JWT
            consent_id: Consent request ID to resolve

        Returns:
            Success status
        """
        try:
            if not self.redis_available or not self.client:
                return False

            # Remove from pending list
            pending_list_key = self._get_user_key(user_id, "pending_consent_list")
            await self.client.lrem(pending_list_key, 0, consent_id)

            # Delete consent data
            consent_key = self._get_user_key(user_id, f"pending_consent:{consent_id}")
            deleted = await self.client.delete(consent_key)

            logger.debug(f"Resolved consent {consent_id} for user {user_id}")
            return deleted > 0

        except Exception as e:
            logger.error(
                f"Failed to resolve consent {consent_id} for user {user_id}: {e}"
            )
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health.

        Returns:
            Health status information
        """
        try:
            if not self.client:
                return {"status": "disconnected", "available": False}

            # Test connection
            await self.client.ping()

            # Get basic info
            info = await self.client.info("memory")

            return {
                "status": "healthy",
                "available": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "available": False, "error": str(e)}


# Create global instance
redis_store = RedisStore()


# Convenience functions for external use
async def get_redis_store() -> RedisStore:
    """Get initialized Redis store instance."""
    if not redis_store.client:
        await redis_store.initialize()
    return redis_store


# All operations now require validated user_id from JWT - no more token complexity
