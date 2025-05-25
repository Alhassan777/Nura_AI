import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ..storage.redis_store import RedisStore
from ..types import MemoryItem


@pytest.fixture
def redis_store():
    """Create a Redis store instance for testing."""
    with patch("src.services.memory.storage.redis_store.Config") as mock_config:
        mock_config.REDIS_URL = "redis://localhost:6379"
        mock_config.get_memory_config.return_value = {"short_term_size": 100}

        store = RedisStore()
        return store


@pytest.fixture
def sample_memory():
    """Create a sample memory item for testing."""
    return MemoryItem(
        id="test-id",
        userId="test-user",
        content="Test memory content",
        type="chat",
        metadata={
            "timestamp": datetime.utcnow(),
            "has_pii": False,
            "sensitive_types": [],
        },
    )


@pytest.mark.asyncio
async def test_add_memory(redis_store, sample_memory):
    """Test adding a memory."""
    # Mock Redis client
    redis_store.redis.lpush = Mock()
    redis_store.redis.ltrim = Mock()

    # Add memory
    await redis_store.add_memory(sample_memory)

    # Verify calls
    redis_store.redis.lpush.assert_called_once_with(
        f"memories:{sample_memory.userId}", sample_memory.json()
    )
    redis_store.redis.ltrim.assert_called_once_with(
        f"memories:{sample_memory.userId}", 0, 99  # short_term_size - 1
    )


@pytest.mark.asyncio
async def test_get_memories(redis_store):
    """Test getting memories."""
    # Mock Redis client
    mock_memories = [
        MemoryItem(
            id=f"id-{i}",
            userId="test-user",
            content=f"Memory {i}",
            type="chat",
            metadata={
                "timestamp": datetime.utcnow(),
                "has_pii": False,
                "sensitive_types": [],
            },
        ).json()
        for i in range(3)
    ]
    redis_store.redis.lrange = Mock(return_value=mock_memories)

    # Get memories
    memories = await redis_store.get_memories("test-user")

    # Verify result
    assert len(memories) == 3
    assert memories[0].id == "id-0"
    assert memories[1].id == "id-1"
    assert memories[2].id == "id-2"

    # Verify calls
    redis_store.redis.lrange.assert_called_once_with("memories:test-user", 0, -1)


@pytest.mark.asyncio
async def test_get_memories_empty(redis_store):
    """Test getting memories when none exist."""
    # Mock Redis client
    redis_store.redis.lrange = Mock(return_value=[])

    # Get memories
    memories = await redis_store.get_memories("test-user")

    # Verify result
    assert len(memories) == 0

    # Verify calls
    redis_store.redis.lrange.assert_called_once_with("memories:test-user", 0, -1)


@pytest.mark.asyncio
async def test_delete_memory(redis_store):
    """Test deleting a memory."""
    # Mock Redis client
    redis_store.redis.lrem = Mock(return_value=1)

    # Delete memory
    result = await redis_store.delete_memory(user_id="test-user", memory_id="test-id")

    # Verify result
    assert result is True

    # Verify calls
    redis_store.redis.lrem.assert_called_once()


@pytest.mark.asyncio
async def test_delete_memory_not_found(redis_store):
    """Test deleting a non-existent memory."""
    # Mock Redis client
    redis_store.redis.lrem = Mock(return_value=0)

    # Delete memory
    result = await redis_store.delete_memory(user_id="test-user", memory_id="test-id")

    # Verify result
    assert result is False

    # Verify calls
    redis_store.redis.lrem.assert_called_once()


@pytest.mark.asyncio
async def test_clear_memories(redis_store):
    """Test clearing all memories."""
    # Mock Redis client
    redis_store.redis.delete = Mock()

    # Clear memories
    await redis_store.clear_memories("test-user")

    # Verify calls
    redis_store.redis.delete.assert_called_once_with("memories:test-user")


@pytest.mark.asyncio
async def test_connection_error(redis_store, sample_memory):
    """Test handling Redis connection error."""
    # Mock Redis client to raise an exception
    redis_store.redis.lpush = Mock(side_effect=Exception("Connection error"))

    # Add memory
    with pytest.raises(Exception) as exc_info:
        await redis_store.add_memory(sample_memory)

    # Verify error
    assert str(exc_info.value) == "Connection error"

    # Verify calls
    redis_store.redis.lpush.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_json(redis_store):
    """Test handling invalid JSON in Redis."""
    # Mock Redis client to return invalid JSON
    redis_store.redis.lrange = Mock(return_value=["invalid json"])

    # Get memories
    with pytest.raises(Exception) as exc_info:
        await redis_store.get_memories("test-user")

    # Verify error
    assert "Invalid JSON" in str(exc_info.value)

    # Verify calls
    redis_store.redis.lrange.assert_called_once()
