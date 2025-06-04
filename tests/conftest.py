"""
Pytest configuration and shared fixtures for Nura backend tests.

This file provides shared fixtures and configuration for all test types:
- Unit tests: Fast, isolated component tests
- Integration tests: Service interaction tests
- Functional tests: End-to-end workflow tests
- System tests: Performance and load tests
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use test database
os.environ["HF_TOKEN"] = "test-hf-token"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"


# ============================================================================
# Session and Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Service Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.lrange = AsyncMock(return_value=[])
    mock_redis.lpush = AsyncMock(return_value=1)
    mock_redis.lrem = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.hgetall = AsyncMock(return_value={})
    mock_redis.hset = AsyncMock(return_value=1)
    mock_redis.hdel = AsyncMock(return_value=1)
    return mock_redis


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock_store = Mock()
    mock_store.add_memory = AsyncMock(return_value="test-memory-id")
    mock_store.get_user_memories = AsyncMock(return_value=[])
    mock_store.similarity_search = AsyncMock(return_value=[])
    mock_store.delete_memory = AsyncMock(return_value=True)
    mock_store.clear_user_memories = AsyncMock(return_value=True)
    mock_store.get_user_stats = AsyncMock(return_value={"vector_count": 0})
    mock_store.health_check = AsyncMock(return_value={"status": "healthy"})
    return mock_store


@pytest.fixture
def mock_memory_service():
    """Mock memory service for testing."""
    mock_service = Mock()
    mock_service.process_memory = AsyncMock(
        return_value={
            "success": True,
            "memory_id": "test-memory-id",
            "message": "Memory processed successfully",
            "storage_type": "short_term",
            "needs_consent": False,
        }
    )
    mock_service.get_memory_context = AsyncMock(
        return_value={
            "short_term": [],
            "long_term": [],
            "digest": "No previous context available",
        }
    )
    mock_service.get_memory_stats = AsyncMock(
        return_value={"total": 0, "short_term": 0, "long_term": 0, "sensitive": 0}
    )
    return mock_service


@pytest.fixture
def mock_image_generator():
    """Mock image generator for testing."""
    mock_generator = Mock()
    mock_generator.generate_image_from_prompt = AsyncMock(
        return_value={
            "success": True,
            "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "image_format": "png",
            "prompt_used": "Test prompt",
            "model": "FLUX.1-dev",
        }
    )
    mock_generator.get_recommended_params_for_emotion = Mock(
        return_value={
            "guidance_scale": 7.5,
            "num_inference_steps": 50,
            "width": 1024,
            "height": 1024,
        }
    )
    return mock_generator


@pytest.fixture
def mock_emotion_visualizer():
    """Mock emotion visualizer for testing."""
    mock_visualizer = Mock()
    mock_visualizer.create_emotional_image = AsyncMock(
        return_value={
            "success": True,
            "image_data": "test-base64-data",
            "visual_prompt": "Test visual prompt",
            "emotion_type": "calm",
            "created_at": "2024-01-01T12:00:00",
        }
    )
    return mock_visualizer


@pytest.fixture
def mock_mental_health_assistant():
    """Mock mental health assistant for testing."""
    mock_assistant = Mock()
    mock_assistant.generate_response = AsyncMock(
        return_value={
            "response": "This is a test response from the mental health assistant.",
            "crisis_level": "SUPPORT",
            "session_id": "test-session",
            "memory_stored": True,
            "configuration_warnings": [],
            "response_metadata": {"processing_time": 1.5, "memory_context_used": False},
        }
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
    mock_detector.detect_pii = AsyncMock(
        return_value={
            "has_pii": False,
            "detected_items": [],
            "risk_level": "low",
            "confidence_score": 0.1,
        }
    )
    mock_detector.get_granular_consent_options = Mock(
        return_value={"consent_items": [], "recommendations": {}, "default_choices": {}}
    )
    mock_detector.apply_granular_consent = AsyncMock(return_value="Test content")
    return mock_detector


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_user_id():
    """Standard test user ID."""
    return "test-user-123"


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        "user_id": "test-user-123",
        "content": "I had a great therapy session today and learned some coping strategies.",
        "type": "user_message",
        "metadata": {
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "chat_interface",
            "session_id": "test-session-456",
        },
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
def sample_image_generation_request():
    """Sample image generation request for testing."""
    return {
        "user_id": "test-user-123",
        "user_input": "I'm feeling calm and peaceful, like a serene lake at sunset",
        "include_long_term": True,
        "identified_emotion": "calm",
        "name": "Peaceful Lake",
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
def crisis_message():
    """Sample crisis message for testing."""
    return "I don't want to live anymore and I'm thinking about ending it all."


@pytest.fixture
def pii_message():
    """Sample message with PII for testing."""
    return "My name is John Doe and my email is john@email.com. I live at 123 Main St."


@pytest.fixture
def sample_memory_content():
    """Sample memory content with various scenarios."""
    return {
        "normal": "I had a good day at work today.",
        "emotional": "I'm feeling really overwhelmed with everything going on.",
        "crisis": "I can't take this anymore and want to hurt myself.",
        "pii": "My therapist Dr. Smith said I should take my medication.",
        "long": "This is a very long memory content that goes on and on..." * 100,
        "empty": "",
        "special_chars": "Testing émojis 😊 and special chars: @#$%^&*()",
    }


# ============================================================================
# API Test Client Fixtures
# ============================================================================


@pytest.fixture
def test_client():
    """FastAPI test client."""
    with patch.dict(
        os.environ,
        {
            "TESTING": "true",
            "GOOGLE_API_KEY": "test-api-key",
            "REDIS_URL": "redis://localhost:6379/1",
            "HF_TOKEN": "test-hf-token",
        },
    ):
        try:
            from services.memory.api import app

            return TestClient(app)
        except ImportError:
            # Fallback for when app is not available
            return Mock()


# ============================================================================
# Environment and Configuration Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables and mocks."""
    # Set test environment variables
    test_env_vars = {
        "TESTING": "true",
        "GOOGLE_API_KEY": "test-api-key",
        "REDIS_URL": "redis://localhost:6379/1",
        "HF_TOKEN": "test-hf-token",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
        "USE_PINECONE": "false",
        "CHROMA_PERSIST_DIR": "./test_chroma",
    }

    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "google_api_key": "test-api-key",
        "redis_url": "redis://localhost:6379/1",
        "vector_db_type": "chroma",
        "environment": "test",
        "hf_token": "test-hf-token",
        "use_pinecone": False,
        "chroma_persist_dir": "./test_chroma",
    }


# ============================================================================
# Async and Mock Utilities
# ============================================================================


@pytest.fixture
def async_mock():
    """Create async mock function."""

    def _async_mock(*args, **kwargs):
        m = AsyncMock(*args, **kwargs)
        return m

    return _async_mock


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup logic here if needed
    # For example, clearing test Redis DB, removing test files, etc.


# ============================================================================
# Complex Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_memory_item():
    """Sample MemoryItem for testing."""
    from datetime import datetime
    from services.memory.types import MemoryItem

    return MemoryItem(
        id="test-memory-123",
        content="I had a productive therapy session today.",
        type="user_message",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "chat_interface",
            "session_id": "test-session-456",
            "processing_time": 0.5,
        },
    )


@pytest.fixture
def sample_memory_context():
    """Sample memory context for testing."""
    return {
        "short_term": [],
        "long_term": [],
        "digest": "No previous memories available for context.",
    }


@pytest.fixture
def sample_memory_stats():
    """Sample memory statistics for testing."""
    return {"total": 5, "short_term": 3, "long_term": 2, "sensitive": 1}


# ============================================================================
# Test Markers and Categories
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (moderate speed, real services)"
    )
    config.addinivalue_line(
        "markers", "functional: Functional tests (slow, end-to-end)"
    )
    config.addinivalue_line(
        "markers", "system: System tests (very slow, load/performance)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Get the relative path of the test file
        rel_path = item.fspath.relto(config.rootdir)

        # Mark tests based on directory structure
        if "unit/" in rel_path:
            item.add_marker(pytest.mark.unit)
        elif "integration/" in rel_path:
            item.add_marker(pytest.mark.integration)
        elif "functional/" in rel_path:
            item.add_marker(pytest.mark.functional)
        elif "system/" in rel_path:
            item.add_marker(pytest.mark.system)

        # Mark tests by feature area
        if "crisis" in rel_path:
            item.add_marker(pytest.mark.crisis)
        elif "image_generation" in rel_path:
            item.add_marker(pytest.mark.image_generation)
        elif "memory" in rel_path:
            item.add_marker(pytest.mark.memory)
        elif "privacy" in rel_path:
            item.add_marker(pytest.mark.privacy)
        elif "voice" in rel_path:
            item.add_marker(pytest.mark.voice)
        elif "safety" in rel_path:
            item.add_marker(pytest.mark.safety)
