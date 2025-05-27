import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ..storage.vector_store import VectorStore
from ..types import MemoryItem


@pytest.fixture
def vector_store():
    """Create a vector store instance for testing."""
    with patch("src.services.memory.storage.vector_store.Config") as mock_config:
        mock_config.GOOGLE_CLOUD_PROJECT = "test-project"
        mock_config.GOOGLE_API_KEY = "test-key"
        mock_config.USE_VERTEX_AI = False
        mock_config.CHROMA_PERSIST_DIR = "./chroma"
        mock_config.get_memory_config.return_value = {"long_term_size": 1000}

        store = VectorStore()
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
async def test_add_memory_chroma(vector_store, sample_memory):
    """Test adding a memory to Chroma."""
    # Mock dependencies
    vector_store.embeddings.embed_query = Mock(return_value=[0.1, 0.2, 0.3])
    vector_store.collection.add = Mock()

    # Add memory
    await vector_store.add_memory(sample_memory)

    # Verify calls
    vector_store.embeddings.embed_query.assert_called_once_with(sample_memory.content)
    vector_store.collection.add.assert_called_once()
    call_args = vector_store.collection.add.call_args[1]
    assert call_args["ids"] == [sample_memory.id]
    assert call_args["metadatas"] == [
        {
            "userId": sample_memory.userId,
            "type": sample_memory.type,
            "timestamp": sample_memory.metadata["timestamp"],
            "has_pii": sample_memory.metadata["has_pii"],
            "sensitive_types": sample_memory.metadata["sensitive_types"],
        }
    ]
    assert len(call_args["embeddings"]) == 1
    assert len(call_args["embeddings"][0]) == 3


@pytest.mark.asyncio
async def test_add_memory_vertex_ai(vector_store, sample_memory):
    """Test adding a memory to Vertex AI."""
    # Enable Vertex AI
    vector_store.use_vertex_ai = True

    # Mock dependencies
    vector_store.embeddings.embed_query = Mock(return_value=[0.1, 0.2, 0.3])
    vector_store.index.upsert = Mock()

    # Add memory
    await vector_store.add_memory(sample_memory)

    # Verify calls
    vector_store.embeddings.embed_query.assert_called_once_with(sample_memory.content)
    vector_store.index.upsert.assert_called_once()
    call_args = vector_store.index.upsert.call_args[1]
    assert call_args["ids"] == [sample_memory.id]
    assert call_args["vectors"] == [[0.1, 0.2, 0.3]]
    assert call_args["metadata"] == [
        {
            "userId": sample_memory.userId,
            "type": sample_memory.type,
            "timestamp": sample_memory.metadata["timestamp"],
            "has_pii": sample_memory.metadata["has_pii"],
            "sensitive_types": sample_memory.metadata["sensitive_types"],
        }
    ]


@pytest.mark.asyncio
async def test_get_similar_memories_chroma(vector_store):
    """Test getting similar memories from Chroma."""
    # Mock dependencies
    vector_store.embeddings.embed_query = Mock(return_value=[0.1, 0.2, 0.3])
    vector_store.collection.query = Mock(
        return_value={
            "ids": [["id-1", "id-2"]],
            "metadatas": [
                [
                    {
                        "userId": "test-user",
                        "type": "chat",
                        "timestamp": "2024-03-20T10:00:00Z",
                        "has_pii": False,
                        "sensitive_types": [],
                    },
                    {
                        "userId": "test-user",
                        "type": "chat",
                        "timestamp": "2024-03-20T11:00:00Z",
                        "has_pii": False,
                        "sensitive_types": [],
                    },
                ]
            ],
            "documents": [["Memory 1", "Memory 2"]],
        }
    )

    # Get similar memories
    memories = await vector_store.get_similar_memories(
        user_id="test-user", query="test query"
    )

    # Verify result
    assert len(memories) == 2
    assert memories[0].id == "id-1"
    assert memories[0].content == "Memory 1"
    assert memories[1].id == "id-2"
    assert memories[1].content == "Memory 2"

    # Verify calls
    vector_store.embeddings.embed_query.assert_called_once_with("test query")
    vector_store.collection.query.assert_called_once()
    call_args = vector_store.collection.query.call_args[1]
    assert call_args["query_embeddings"] == [[0.1, 0.2, 0.3]]
    assert call_args["where"] == {"userId": "test-user"}
    assert call_args["n_results"] == 5


@pytest.mark.asyncio
async def test_get_similar_memories_vertex_ai(vector_store):
    """Test getting similar memories from Vertex AI."""
    # Enable Vertex AI
    vector_store.use_vertex_ai = True

    # Mock dependencies
    vector_store.embeddings.embed_query = Mock(return_value=[0.1, 0.2, 0.3])
    vector_store.index.query = Mock(
        return_value={
            "matches": [
                {
                    "id": "id-1",
                    "metadata": {
                        "userId": "test-user",
                        "type": "chat",
                        "timestamp": "2024-03-20T10:00:00Z",
                        "has_pii": False,
                        "sensitive_types": [],
                    },
                    "document": "Memory 1",
                },
                {
                    "id": "id-2",
                    "metadata": {
                        "userId": "test-user",
                        "type": "chat",
                        "timestamp": "2024-03-20T11:00:00Z",
                        "has_pii": False,
                        "sensitive_types": [],
                    },
                    "document": "Memory 2",
                },
            ]
        }
    )

    # Get similar memories
    memories = await vector_store.get_similar_memories(
        user_id="test-user", query="test query"
    )

    # Verify result
    assert len(memories) == 2
    assert memories[0].id == "id-1"
    assert memories[0].content == "Memory 1"
    assert memories[1].id == "id-2"
    assert memories[1].content == "Memory 2"

    # Verify calls
    vector_store.embeddings.embed_query.assert_called_once_with("test query")
    vector_store.index.query.assert_called_once()
    call_args = vector_store.index.query.call_args[1]
    assert call_args["vector"] == [0.1, 0.2, 0.3]
    assert call_args["filter"] == {"userId": "test-user"}
    assert call_args["num_neighbors"] == 5


@pytest.mark.asyncio
async def test_delete_memory_chroma(vector_store):
    """Test deleting a memory from Chroma."""
    # Mock dependencies
    vector_store.collection.delete = Mock()

    # Delete memory
    result = await vector_store.delete_memory(user_id="test-user", memory_id="test-id")

    # Verify result
    assert result is True

    # Verify calls
    vector_store.collection.delete.assert_called_once_with(
        where={"userId": "test-user", "id": "test-id"}
    )


@pytest.mark.asyncio
async def test_delete_memory_vertex_ai(vector_store):
    """Test deleting a memory from Vertex AI."""
    # Enable Vertex AI
    vector_store.use_vertex_ai = True

    # Mock dependencies
    vector_store.index.delete = Mock()

    # Delete memory
    result = await vector_store.delete_memory(user_id="test-user", memory_id="test-id")

    # Verify result
    assert result is True

    # Verify calls
    vector_store.index.delete.assert_called_once_with(
        ids=["test-id"], filter={"userId": "test-user"}
    )


@pytest.mark.asyncio
async def test_clear_memories_chroma(vector_store):
    """Test clearing all memories from Chroma."""
    # Mock dependencies
    vector_store.collection.delete = Mock()

    # Clear memories
    await vector_store.clear_memories("test-user")

    # Verify calls
    vector_store.collection.delete.assert_called_once_with(
        where={"userId": "test-user"}
    )


@pytest.mark.asyncio
async def test_clear_memories_vertex_ai(vector_store):
    """Test clearing all memories from Vertex AI."""
    # Enable Vertex AI
    vector_store.use_vertex_ai = True

    # Mock dependencies
    vector_store.index.delete = Mock()

    # Clear memories
    await vector_store.clear_memories("test-user")

    # Verify calls
    vector_store.index.delete.assert_called_once_with(filter={"userId": "test-user"})


@pytest.mark.asyncio
async def test_embedding_error(vector_store, sample_memory):
    """Test handling embedding generation error."""
    # Mock dependencies to raise an exception
    vector_store.embeddings.embed_query = Mock(side_effect=Exception("Embedding error"))

    # Add memory
    with pytest.raises(Exception) as exc_info:
        await vector_store.add_memory(sample_memory)

    # Verify error
    assert str(exc_info.value) == "Embedding error"

    # Verify calls
    vector_store.embeddings.embed_query.assert_called_once()
