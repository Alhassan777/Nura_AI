import json
import logging
from typing import List, Optional
from datetime import datetime

# Import centralized Redis utilities
from utils.redis_client import (
    get_redis_client,
    cache_list_push,
    cache_list_get,
    cache_delete,
)

from ..types import MemoryItem

# Set up logging
logger = logging.getLogger(__name__)


class RedisStore:
    def __init__(self, redis_url: str, max_size: int = 10):
        # We don't need to store redis_url since we use centralized client
        self.max_size = max_size
        logger.info(f"Initialized RedisStore with max_size={max_size}")

    async def add_memory(self, user_id: str, memory: MemoryItem) -> None:
        """Add a memory to the user's short-term store."""
        key = f"user:{user_id}:memories"

        try:
            # Convert memory to JSON
            memory_dict = {
                "id": memory.id,
                "userId": memory.userId,
                "content": memory.content,
                "type": memory.type,
                "metadata": {
                    **memory.metadata,
                    "timestamp": memory.timestamp.isoformat(),
                },
            }

            # Use centralized Redis utility for list operations
            redis_client = await get_redis_client()

            # Add to Redis list
            await redis_client.lpush(key, json.dumps(memory_dict))

            # Trim list to max size
            await redis_client.ltrim(key, 0, self.max_size - 1)

            logger.info(f"Added memory {memory.id} for user {user_id} to Redis")

        except Exception as e:
            logger.error(
                f"Failed to add memory {memory.id} for user {user_id}: {str(e)}"
            )
            raise

    async def get_memories(self, user_id: str) -> List[MemoryItem]:
        """Get all memories for a user."""
        key = f"user:{user_id}:memories"

        try:
            # Use centralized Redis utility
            redis_client = await get_redis_client()

            # Get all memories from Redis
            memory_jsons = await redis_client.lrange(key, 0, -1)

            memories = []
            for memory_json in memory_jsons:
                # Decode bytes to string if needed
                if isinstance(memory_json, bytes):
                    memory_json = memory_json.decode("utf-8")

                memory_dict = json.loads(memory_json)

                # Convert timestamp back to datetime
                timestamp_str = memory_dict["metadata"]["timestamp"]
                memory_dict["timestamp"] = datetime.fromisoformat(timestamp_str)

                # Remove timestamp from metadata since it's now in the main dict
                metadata = memory_dict["metadata"].copy()
                del metadata["timestamp"]
                memory_dict["metadata"] = metadata

                memories.append(MemoryItem(**memory_dict))

            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {str(e)}")
            return []

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        key = f"user:{user_id}:memories"

        try:
            # Use centralized Redis utility
            redis_client = await get_redis_client()

            # Get all memories
            memory_jsons = await redis_client.lrange(key, 0, -1)

            # Find and remove the target memory
            for i, memory_json in enumerate(memory_jsons):
                # Decode bytes to string if needed
                if isinstance(memory_json, bytes):
                    memory_json = memory_json.decode("utf-8")

                memory_dict = json.loads(memory_json)
                if memory_dict["id"] == memory_id:
                    # Remove the memory
                    await redis_client.lrem(key, 1, memory_json)
                    logger.info(f"Deleted memory {memory_id} for user {user_id}")
                    return True

            logger.warning(f"Memory {memory_id} not found for user {user_id}")
            return False

        except Exception as e:
            logger.error(
                f"Failed to delete memory {memory_id} for user {user_id}: {str(e)}"
            )
            return False

    async def update_memory(self, user_id: str, memory: MemoryItem) -> bool:
        """Update an existing memory or add it if it doesn't exist."""
        try:
            # First, try to delete the existing memory
            await self.delete_memory(user_id, memory.id)

            # Then add the updated memory
            await self.add_memory(user_id, memory)

            logger.info(f"Updated memory {memory.id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update memory {memory.id} for user {user_id}: {str(e)}"
            )
            return False

    async def clear_memories(self, user_id: str) -> None:
        """Clear all memories for a user."""
        key = f"user:{user_id}:memories"

        try:
            # Use centralized Redis utility
            redis_client = await get_redis_client()

            count = await redis_client.llen(key)
            await redis_client.delete(key)
            logger.info(f"Cleared {count} memories for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to clear memories for user {user_id}: {str(e)}")
            raise

    async def get_memory_count(self, user_id: str) -> int:
        """Get the number of memories for a user."""
        key = f"user:{user_id}:memories"

        try:
            # Use centralized Redis utility
            redis_client = await get_redis_client()

            count = await redis_client.llen(key)
            logger.debug(f"User {user_id} has {count} memories in Redis")
            return count

        except Exception as e:
            logger.error(f"Failed to get memory count for user {user_id}: {str(e)}")
            return 0
