import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from ..api import app
from ..types import MemoryItem, MemoryContext, MemoryStats


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_memory_service():
    """Create a mock memory service."""
    with patch("src.services.memory.api.memory_service") as mock:
        yield mock


def test_process_chat(client, mock_memory_service):
    """Test processing a chat message."""
    # Mock memory service
    mock_memory_service.process_memory.return_value = MemoryItem(
        id="test-id",
        userId="test-user",
        content="Test message",
        type="chat",
        metadata={
            "timestamp": datetime.utcnow(),
            "has_pii": False,
            "sensitive_types": [],
        },
    )

    # Send request
    response = client.post(
        "/chat?user_id=test-user",
        json={"content": "Test message", "type": "chat"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["memory"]["id"] == "test-id"
    assert data["memory"]["content"] == "Test message"
    assert data["memory"]["type"] == "chat"

    # Verify calls
    mock_memory_service.process_memory.assert_called_once_with(
        user_id="test-user", content="Test message", type="chat", metadata=None
    )


def test_process_chat_with_pii(client, mock_memory_service):
    """Test processing a chat message with PII."""
    # Mock memory service
    mock_memory_service.process_memory.return_value = MemoryItem(
        id="test-id",
        userId="test-user",
        content="[PERSON]'s email is [EMAIL]",
        type="chat",
        metadata={
            "timestamp": datetime.utcnow(),
            "has_pii": True,
            "sensitive_types": ["PERSON", "EMAIL"],
            "anonymized": True,
        },
    )

    # Send request
    response = client.post(
        "/chat?user_id=test-user",
        json={"content": "John's email is john@example.com", "type": "chat"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["memory"]["id"] == "test-id"
    assert data["memory"]["content"] == "[PERSON]'s email is [EMAIL]"
    assert data["memory"]["type"] == "chat"
    assert data["memory"]["metadata"]["has_pii"] is True
    assert data["memory"]["metadata"]["anonymized"] is True
    assert "PERSON" in data["memory"]["metadata"]["sensitive_types"]
    assert "EMAIL" in data["memory"]["metadata"]["sensitive_types"]

    # Verify calls
    mock_memory_service.process_memory.assert_called_once_with(
        user_id="test-user",
        content="John's email is john@example.com",
        type="chat",
        metadata=None,
    )


def test_get_memory_context(client, mock_memory_service):
    """Test getting memory context."""
    # Mock memory service
    mock_memory_service.get_memory_context.return_value = MemoryContext(
        short_term=[
            MemoryItem(
                id="st1",
                userId="test-user",
                content="Short term 1",
                type="chat",
                metadata={
                    "timestamp": datetime.utcnow(),
                    "has_pii": False,
                    "sensitive_types": [],
                },
            )
        ],
        long_term=[
            MemoryItem(
                id="lt1",
                userId="test-user",
                content="Long term 1",
                type="chat",
                metadata={
                    "timestamp": datetime.utcnow(),
                    "has_pii": False,
                    "sensitive_types": [],
                },
            )
        ],
        digest="Test digest",
    )

    # Send request
    response = client.post(
        "/memory/context?user_id=test-user", json={"query": "test query"}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data["context"]["short_term"]) == 1
    assert len(data["context"]["long_term"]) == 1
    assert data["context"]["digest"] == "Test digest"

    # Verify calls
    mock_memory_service.get_memory_context.assert_called_once_with(
        user_id="test-user", query="test query"
    )


def test_get_memory_stats(client, mock_memory_service):
    """Test getting memory statistics."""
    # Mock memory service
    mock_memory_service.get_memory_stats.return_value = MemoryStats(
        total=10, short_term=5, long_term=5, sensitive=2
    )

    # Send request
    response = client.get("/memory/stats?user_id=test-user")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total"] == 10
    assert data["stats"]["short_term"] == 5
    assert data["stats"]["long_term"] == 5
    assert data["stats"]["sensitive"] == 2

    # Verify calls
    mock_memory_service.get_memory_stats.assert_called_once_with("test-user")


def test_delete_memory(client, mock_memory_service):
    """Test deleting a memory."""
    # Mock memory service
    mock_memory_service.delete_memory.return_value = True

    # Send request
    response = client.delete("/memory/test-id?user_id=test-user")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "Memory deleted successfully" in data["message"]

    # Verify calls
    mock_memory_service.delete_memory.assert_called_once_with(
        user_id="test-user", memory_id="test-id"
    )


def test_delete_memory_not_found(client, mock_memory_service):
    """Test deleting a non-existent memory."""
    # Mock memory service
    mock_memory_service.delete_memory.return_value = False

    # Send request
    response = client.delete("/memory/test-id?user_id=test-user")

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Memory not found"

    # Verify calls
    mock_memory_service.delete_memory.assert_called_once_with(
        user_id="test-user", memory_id="test-id"
    )


def test_clear_memories(client, mock_memory_service):
    """Test clearing all memories."""
    # Mock memory service
    mock_memory_service.clear_memories = Mock()

    # Send request
    response = client.post("/memory/forget?user_id=test-user")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "All memories cleared successfully" in data["message"]

    # Verify calls
    mock_memory_service.clear_memories.assert_called_once_with("test-user")


def test_export_memories(client, mock_memory_service):
    """Test exporting memories."""
    # Mock memory service
    mock_memory_service.get_memory_context.return_value = MemoryContext(
        short_term=[
            MemoryItem(
                id="st1",
                userId="test-user",
                content="Short term 1",
                type="chat",
                metadata={
                    "timestamp": datetime.utcnow(),
                    "has_pii": False,
                    "sensitive_types": [],
                },
            )
        ],
        long_term=[
            MemoryItem(
                id="lt1",
                userId="test-user",
                content="Long term 1",
                type="chat",
                metadata={
                    "timestamp": datetime.utcnow(),
                    "has_pii": False,
                    "sensitive_types": [],
                },
            )
        ],
        digest="Test digest",
    )

    # Send request
    response = client.post("/memory/export?user_id=test-user")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data["short_term"]) == 1
    assert len(data["long_term"]) == 1

    # Verify calls
    mock_memory_service.get_memory_context.assert_called_once_with(
        user_id="test-user", query=None
    )


def test_missing_user_id(client):
    """Test missing user_id parameter."""
    # Send request without user_id
    response = client.post("/chat", json={"content": "Test message", "type": "chat"})

    # Verify response
    assert response.status_code == 422  # Validation error


def test_invalid_request_data(client):
    """Test invalid request data."""
    # Send request with missing content
    response = client.post("/chat?user_id=test-user", json={"type": "chat"})

    # Verify response
    assert response.status_code == 422  # Validation error
