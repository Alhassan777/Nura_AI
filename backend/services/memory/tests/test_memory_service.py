import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ..memoryService import MemoryService
from ..types import MemoryItem, MemoryScore


@pytest.fixture
def memory_service():
    """Create a memory service instance for testing."""
    with patch("src.services.memory.memoryService.Config") as mock_config:
        mock_config.REDIS_URL = "redis://localhost:6379"
        mock_config.CHROMA_PERSIST_DIR = "./chroma"
        mock_config.GOOGLE_CLOUD_PROJECT = "test-project"
        mock_config.GOOGLE_API_KEY = "test-key"
        mock_config.USE_VERTEX_AI = False
        mock_config.JWT_SECRET_KEY = "test-secret"
        mock_config.get_memory_config.return_value = {
            "short_term_size": 100,
            "long_term_size": 1000,
            "relevance_threshold": 0.6,
            "stability_threshold": 0.7,
            "explicitness_threshold": 0.5,
        }

        service = MemoryService()
        return service


@pytest.fixture
def sample_memory():
    """Create a sample memory item for testing."""
    return MemoryItem(
        id="test-id",
        userId="test-user",
        content="I've been feeling anxious lately",
        type="chat",
        metadata={
            "timestamp": datetime.utcnow(),
            "has_pii": False,
            "sensitive_types": [],
        },
    )


@pytest.mark.asyncio
async def test_process_memory(memory_service, sample_memory):
    """Test processing a new memory."""
    # Mock dependencies
    memory_service.pii_detector.detect_pii = Mock(
        return_value={"has_pii": False, "entities": {}}
    )

    memory_service.scorer.score_memory = Mock(
        return_value=MemoryScore(
            relevance=0.8,
            stability=0.9,
            explicitness=0.7,
            sensitivity=False,
            sensitive_types=[],
        )
    )

    memory_service.scorer.should_store_memory = Mock(return_value=True)

    memory_service.redis_store.add_memory = Mock()
    memory_service.vector_store.add_memory = Mock()
    memory_service.audit_logger.log_memory_created = Mock()

    # Process memory
    result = await memory_service.process_memory(
        user_id="test-user", content="I've been feeling anxious lately", type="chat"
    )

    # Verify result
    assert result is not None
    assert result.content == "I've been feeling anxious lately"
    assert result.type == "chat"
    assert not result.metadata["has_pii"]

    # Verify calls
    memory_service.pii_detector.detect_pii.assert_called_once()
    memory_service.scorer.score_memory.assert_called_once()
    memory_service.scorer.should_store_memory.assert_called_once()
    memory_service.vector_store.add_memory.assert_called_once()
    memory_service.audit_logger.log_memory_created.assert_called_once()


@pytest.mark.asyncio
async def test_process_memory_with_pii(memory_service, sample_memory):
    """Test processing a memory with PII."""
    # Mock dependencies
    memory_service.pii_detector.detect_pii = Mock(
        return_value={
            "has_pii": True,
            "entities": {
                "PERSON": [{"text": "John", "start": 0, "end": 4, "score": 0.9}]
            },
        }
    )

    memory_service.pii_detector.requires_consent = Mock(return_value=True)
    memory_service.pii_detector.anonymize_content = Mock(
        return_value="[PERSON] has been feeling anxious lately"
    )

    memory_service.scorer.score_memory = Mock(
        return_value=MemoryScore(
            relevance=0.8,
            stability=0.9,
            explicitness=0.7,
            sensitivity=True,
            sensitive_types=["PERSON"],
        )
    )

    memory_service.scorer.should_store_memory = Mock(return_value=True)

    memory_service.redis_store.add_memory = Mock()
    memory_service.vector_store.add_memory = Mock()
    memory_service.audit_logger.log_memory_created = Mock()
    memory_service.audit_logger.log_pii_detected = Mock()

    # Process memory
    result = await memory_service.process_memory(
        user_id="test-user", content="John has been feeling anxious lately", type="chat"
    )

    # Verify result
    assert result is not None
    assert result.content == "[PERSON] has been feeling anxious lately"
    assert result.metadata["has_pii"]
    assert "PERSON" in result.metadata["sensitive_types"]
    assert result.metadata["anonymized"]

    # Verify calls
    memory_service.pii_detector.detect_pii.assert_called_once()
    memory_service.pii_detector.requires_consent.assert_called_once()
    memory_service.pii_detector.anonymize_content.assert_called_once()
    memory_service.scorer.score_memory.assert_called_once()
    memory_service.scorer.should_store_memory.assert_called_once()
    memory_service.vector_store.add_memory.assert_called_once()
    memory_service.audit_logger.log_memory_created.assert_called_once()
    memory_service.audit_logger.log_pii_detected.assert_called_once()


@pytest.mark.asyncio
async def test_get_memory_context(memory_service):
    """Test getting memory context."""
    # Mock dependencies
    memory_service.redis_store.get_memories = Mock(
        return_value=[
            MemoryItem(id="st1", userId="test-user", content="Short term 1"),
            MemoryItem(id="st2", userId="test-user", content="Short term 2"),
        ]
    )

    memory_service.vector_store.get_similar_memories = Mock(
        return_value=[
            MemoryItem(id="lt1", userId="test-user", content="Long term 1"),
            MemoryItem(id="lt2", userId="test-user", content="Long term 2"),
        ]
    )

    memory_service.audit_logger.log_memory_accessed = Mock()

    # Get context
    context = await memory_service.get_memory_context(
        user_id="test-user", query="test query"
    )

    # Verify result
    assert len(context.short_term) == 2
    assert len(context.long_term) == 2
    assert context.short_term[0].content == "Short term 1"
    assert context.long_term[0].content == "Long term 1"

    # Verify calls
    memory_service.redis_store.get_memories.assert_called_once_with("test-user")
    memory_service.vector_store.get_similar_memories.assert_called_once_with(
        user_id="test-user", query="test query"
    )
    assert memory_service.audit_logger.log_memory_accessed.call_count == 2


@pytest.mark.asyncio
async def test_delete_memory(memory_service):
    """Test deleting a memory."""
    # Mock dependencies
    memory_service.redis_store.delete_memory = Mock(return_value=False)
    memory_service.vector_store.delete_memory = Mock(return_value=True)
    memory_service.audit_logger.log_memory_deleted = Mock()

    # Delete memory
    result = await memory_service.delete_memory(
        user_id="test-user", memory_id="test-id"
    )

    # Verify result
    assert result is True

    # Verify calls
    memory_service.redis_store.delete_memory.assert_called_once_with(
        user_id="test-user", memory_id="test-id"
    )
    memory_service.vector_store.delete_memory.assert_called_once_with(
        user_id="test-user", memory_id="test-id"
    )
    memory_service.audit_logger.log_memory_deleted.assert_called_once()


@pytest.mark.asyncio
async def test_clear_memories(memory_service):
    """Test clearing all memories."""
    # Mock dependencies
    memory_service.redis_store.clear_memories = Mock()
    memory_service.vector_store.clear_memories = Mock()
    memory_service.get_memory_stats = Mock(
        return_value=MemoryStats(total=10, short_term=5, long_term=5, sensitive=2)
    )
    memory_service.audit_logger.log_memory_cleared = Mock()

    # Clear memories
    await memory_service.clear_memories(user_id="test-user")

    # Verify calls
    memory_service.redis_store.clear_memories.assert_called_once_with("test-user")
    memory_service.vector_store.clear_memories.assert_called_once_with("test-user")
    memory_service.get_memory_stats.assert_called_once_with("test-user")
    memory_service.audit_logger.log_memory_cleared.assert_called_once_with(
        user_id="test-user", count=10
    )
