"""
Pytest configuration and shared fixtures for Nura backend tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import pytest
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use test database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.ping = Mock(return_value=True)
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=False)
    mock_redis.keys = Mock(return_value=[])
    mock_redis.hgetall = Mock(return_value={})
    mock_redis.hset = Mock(return_value=1)
    mock_redis.hdel = Mock(return_value=1)
    mock_redis.expire = Mock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock_store = Mock()
    mock_store.add_memory = AsyncMock(return_value="test-memory-id")
    mock_store.get_memories = AsyncMock(return_value=[])
    mock_store.get_similar_memories = AsyncMock(return_value=[])
    mock_store.delete_memory = AsyncMock(return_value=True)
    mock_store.clear_memories = AsyncMock(return_value=True)
    mock_store.get_memory_count = AsyncMock(return_value=0)
    return mock_store


@pytest.fixture
def mock_memory_service():
    """Mock memory service for testing."""
    from services.memory.models import MemoryResponse, MemoryStatsResponse

    mock_service = Mock()
    mock_service.process_memory = AsyncMock(
        return_value=MemoryResponse(
            id="test-memory-id",
            message="Memory processed successfully",
            storage_type="short_term",
            requires_consent=False,
        )
    )
    mock_service.get_memory_context = AsyncMock(
        return_value={
            "short_term_memories": [],
            "long_term_memories": [],
            "context": "No previous context available",
        }
    )
    mock_service.get_memory_stats = AsyncMock(
        return_value=MemoryStatsResponse(
            total_memories=0, short_term_count=0, long_term_count=0, sensitive_count=0
        )
    )
    return mock_service


@pytest.fixture
def mock_mental_health_assistant():
    """Mock mental health assistant for testing."""
    from services.chat.models import ChatResponse

    mock_assistant = Mock()
    mock_assistant.generate_response = AsyncMock(
        return_value=ChatResponse(
            response="This is a test response from the mental health assistant.",
            crisis_level="SUPPORT",
            session_id="test-session",
            memory_stored=True,
            configuration_warnings=[],
        )
    )
    mock_assistant.provide_crisis_resources = Mock(
        return_value={
            "hotlines": ["988 - Suicide & Crisis Lifeline"],
            "text_lines": ["Text HOME to 741741"],
            "emergency": "If in immediate danger, call 911",
        }
    )
    return mock_assistant


@pytest.fixture
def mock_pii_detector():
    """Mock PII detector for testing."""
    mock_detector = Mock()
    mock_detector.detect_pii = Mock(
        return_value={"has_pii": False, "pii_items": [], "risk_level": "low"}
    )
    mock_detector.get_granular_consent_options = Mock(
        return_value={"items": [], "recommendations": {}}
    )
    mock_detector.apply_granular_consent = Mock(return_value="Test content")
    return mock_detector


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        "user_id": "test-user-123",
        "content": "I had a great therapy session today and learned some coping strategies.",
        "memory_type": "user_message",
        "metadata": {"timestamp": "2024-01-01T12:00:00Z", "source": "chat"},
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "user_id": "test-user-123",
        "message": "I'm feeling anxious about my upcoming presentation.",
        "include_memory_context": True,
        "session_id": "test-session-456",
    }


@pytest.fixture
def sample_voice_event():
    """Sample voice webhook event for testing."""
    return {
        "type": "conversation-update",
        "call": {"id": "test-call-123", "status": "in-progress"},
        "message": {"role": "user", "content": "Hello, I need someone to talk to."},
        "timestamp": "2024-01-01T12:00:00Z",
    }


@pytest.fixture
def test_client():
    """FastAPI test client."""
    from main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables and mocks."""
    # Set test environment variables
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")

    # Mock external dependencies
    monkeypatch.setattr("utils.redis_client.get_redis_client", lambda: Mock())


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "google_api_key": "test-api-key",
        "redis_url": "redis://localhost:6379/1",
        "vector_db_type": "chroma",
        "environment": "test",
    }


# Test data fixtures
@pytest.fixture
def crisis_message():
    """Sample crisis message for testing."""
    return "I don't want to live anymore and I'm thinking about ending it all."


@pytest.fixture
def normal_message():
    """Sample normal message for testing."""
    return "I had a good day today and feel grateful for my support system."


@pytest.fixture
def pii_message():
    """Sample message with PII for testing."""
    return "My name is John Doe and my email is john.doe@example.com. I live at 123 Main St."


@pytest.fixture
def sample_memory_content():
    """Sample memory content for privacy testing."""
    return {
        "id": "mem1",
        "content": "My name is John Doe and I feel anxious.",
        "timestamp": "2024-01-01T10:00:00Z",
        "pii_detected": True,
        "risk_level": "high",
    }


# Async test helpers
@pytest.fixture
def async_mock():
    """Helper to create async mocks."""

    def _async_mock(*args, **kwargs):
        return AsyncMock(*args, **kwargs)

    return _async_mock


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Add cleanup logic here if needed
    pass


# API Testing fixtures
@pytest.fixture
def sample_memory_item():
    """Sample MemoryItem for API testing."""
    from services.memory.types import MemoryItem
    from datetime import datetime

    return MemoryItem(
        id="test-mem-123",
        userId="test-user-123",
        content="Test memory content",
        type="chat",
        metadata={"source": "test"},
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def sample_memory_context():
    """Sample MemoryContext for API testing."""
    from services.memory.types import MemoryContext

    return MemoryContext(
        short_term=["Recent conversation about stress"],
        long_term=["Core insight about anxiety patterns"],
        digest="User shows progress in managing anxiety with established coping strategies",
    )


@pytest.fixture
def sample_memory_stats():
    """Sample MemoryStats for API testing."""
    from services.memory.types import MemoryStats

    return MemoryStats(total=100, short_term=30, long_term=70, sensitive=15)
