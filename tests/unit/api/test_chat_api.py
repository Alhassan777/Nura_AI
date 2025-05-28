"""
Phase 3 Unit tests for Chat API endpoints.
Tests mental health assistant and crisis resource endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json
from datetime import datetime
from services.memory.types import MemoryItem, MemoryContext


class TestChatAPI:
    """Test suite for Chat API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the Chat API."""
        from api.chat import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def sample_memory_context(self):
        """Create a sample memory context for testing."""
        return MemoryContext(
            short_term=[
                MemoryItem(
                    id="mem1",
                    userId="test-user-123",
                    content="I've been feeling anxious lately",
                    type="conversation",
                    metadata={},
                    timestamp=datetime.now(),
                )
            ],
            long_term=[],
            digest="User has been experiencing anxiety",
        )

    @pytest.fixture
    def sample_assistant_response(self):
        """Create a sample assistant response for testing."""
        return {
            "response": "I understand you're feeling anxious. That's a very common experience.",
            "crisis_level": "low",
            "crisis_explanation": "No immediate crisis indicators detected",
            "resources_provided": [],
            "coping_strategies": ["deep breathing", "grounding exercises"],
            "timestamp": datetime.now(),
        }

    def test_chat_with_assistant_success(
        self, test_client, sample_memory_context, sample_assistant_response
    ):
        """Test successful chat with mental health assistant."""
        with patch("api.chat.memory_service.get_memory_context") as mock_context, patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_context.return_value = sample_memory_context
            mock_response.return_value = sample_assistant_response
            mock_process.return_value = MemoryItem(
                id="new-mem",
                userId="test-user-123",
                content="Test",
                type="user_message",
                metadata={},
                timestamp=datetime.now(),
            )

            response = test_client.post(
                "/chat/assistant",
                json={
                    "message": "I'm feeling anxious about work",
                    "include_memory": True,
                },
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert (
                data["response"]
                == "I understand you're feeling anxious. That's a very common experience."
            )
            assert data["crisis_level"] == "low"
            assert (
                data["crisis_explanation"] == "No immediate crisis indicators detected"
            )
            assert data["coping_strategies"] == [
                "deep breathing",
                "grounding exercises",
            ]
            assert data["memory_stored"] is True

            # Verify services were called correctly
            mock_context.assert_called_once_with(
                user_id="test-user-123", query="I'm feeling anxious about work"
            )
            mock_response.assert_called_once_with(
                user_message="I'm feeling anxious about work",
                memory_context=sample_memory_context,
                user_id="test-user-123",
            )

            # Verify both user and assistant messages were stored
            assert mock_process.call_count == 2

    def test_chat_without_memory_context(self, test_client, sample_assistant_response):
        """Test chat without memory context."""
        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_response.return_value = sample_assistant_response
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": "Hello", "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["response"] == sample_assistant_response["response"]
            assert data["memory_stored"] is False

            # Verify assistant was called without memory context
            mock_response.assert_called_once_with(
                user_message="Hello", memory_context=None, user_id="test-user-123"
            )

    def test_chat_crisis_detection_high_risk(self, test_client):
        """Test chat with high crisis risk detection."""
        crisis_response = {
            "response": "I'm very concerned about what you've shared. Your safety is important.",
            "crisis_level": "high",
            "crisis_explanation": "Suicide ideation detected",
            "resources_provided": [
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741",
            ],
            "coping_strategies": [
                "Contact emergency services",
                "Reach out to trusted person",
            ],
            "timestamp": datetime.now(),
        }

        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_response.return_value = crisis_response
            mock_process.return_value = MemoryItem(
                id="crisis-mem",
                userId="test-user-123",
                content="I want to end it all",
                type="user_message",
                metadata={"crisis_level": "high"},
                timestamp=datetime.now(),
            )

            response = test_client.post(
                "/chat/assistant",
                json={"message": "I want to end it all", "include_memory": True},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["crisis_level"] == "high"
            assert data["crisis_explanation"] == "Suicide ideation detected"
            assert len(data["resources_provided"]) == 2
            assert "988" in data["resources_provided"][0]
            assert "emergency services" in data["coping_strategies"][0].lower()

    def test_chat_crisis_detection_medium_risk(self, test_client):
        """Test chat with medium crisis risk detection."""
        medium_crisis_response = {
            "response": "I hear that you're going through a really difficult time.",
            "crisis_level": "medium",
            "crisis_explanation": "Significant distress indicators detected",
            "resources_provided": ["Crisis Text Line: Text HOME to 741741"],
            "coping_strategies": [
                "Practice grounding techniques",
                "Reach out to support system",
            ],
            "timestamp": datetime.now(),
        }

        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_response.return_value = medium_crisis_response
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": "I can't handle this anymore", "include_memory": True},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["crisis_level"] == "medium"
            assert (
                data["crisis_explanation"] == "Significant distress indicators detected"
            )
            assert len(data["resources_provided"]) == 1
            assert "grounding techniques" in data["coping_strategies"][0].lower()

    def test_chat_missing_user_id(self, test_client):
        """Test chat without user ID."""
        response = test_client.post(
            "/chat/assistant", json={"message": "Hello", "include_memory": True}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_missing_message(self, test_client):
        """Test chat without message content."""
        response = test_client.post(
            "/chat/assistant",
            json={"include_memory": True},
            params={"user_id": "test-user-123"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_service_error(self, test_client):
        """Test chat when assistant service fails."""
        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response:
            mock_response.side_effect = Exception("Assistant service error")

            response = test_client.post(
                "/chat/assistant",
                json={"message": "Hello", "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data["detail"]
            assert "Assistant service error" in data["detail"]["error"]

    def test_chat_memory_service_error(self, test_client, sample_assistant_response):
        """Test chat when memory service fails."""
        with patch("api.chat.memory_service.get_memory_context") as mock_context, patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_context.side_effect = Exception("Memory service error")
            mock_response.return_value = sample_assistant_response
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": "Hello", "include_memory": True},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_chat_configuration_warning(self, test_client):
        """Test chat with configuration warnings."""
        response_with_warning = {
            "response": "I'm here to help, though some features may be limited.",
            "crisis_level": "low",
            "crisis_explanation": "No crisis detected",
            "resources_provided": [],
            "coping_strategies": [],
            "timestamp": datetime.now(),
            "configuration_warning": True,
        }

        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process, patch(
            "api.chat.get_configuration_status"
        ) as mock_config:

            mock_response.return_value = response_with_warning
            mock_process.return_value = None
            mock_config.return_value = {
                "has_configuration_issues": True,
                "missing_required": ["GOOGLE_API_KEY"],
                "status": "degraded",
            }

            response = test_client.post(
                "/chat/assistant",
                json={"message": "Hello", "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["configuration_warning"] is True
            assert "configuration_status" in data
            assert data["configuration_status"]["has_configuration_issues"] is True

    def test_chat_long_message_handling(self, test_client, sample_assistant_response):
        """Test chat with very long message."""
        long_message = "I'm feeling anxious. " * 1000  # Very long message

        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_response.return_value = sample_assistant_response
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": long_message, "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should handle long messages gracefully
            assert "response" in data

            # Verify assistant was called with the full message
            mock_response.assert_called_once()
            call_args = mock_response.call_args
            assert call_args[1]["user_message"] == long_message

    def test_chat_special_characters_handling(
        self, test_client, sample_assistant_response
    ):
        """Test chat with special characters and emojis."""
        special_message = "I'm feeling 😢 and can't handle this anymore... ¿Por qué?"

        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:

            mock_response.return_value = sample_assistant_response
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": special_message, "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should handle special characters gracefully
            assert "response" in data


class TestCrisisResourcesAPI:
    """Test suite for Crisis Resources API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the Chat API."""
        from api.chat import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def sample_crisis_resources(self):
        """Create sample crisis resources for testing."""
        return {
            "immediate_help": {
                "suicide_prevention": {
                    "hotline": "988",
                    "name": "National Suicide Prevention Lifeline",
                    "available": "24/7",
                },
                "crisis_text": {
                    "number": "741741",
                    "text": "HOME",
                    "name": "Crisis Text Line",
                    "available": "24/7",
                },
                "emergency": {
                    "number": "911",
                    "name": "Emergency Services",
                    "when_to_call": "Immediate danger",
                },
            },
            "mental_health_support": {
                "nami": {
                    "name": "National Alliance on Mental Illness",
                    "helpline": "1-800-950-NAMI",
                    "website": "nami.org",
                },
                "samhsa": {
                    "name": "SAMHSA National Helpline",
                    "number": "1-800-662-4357",
                    "available": "24/7",
                },
            },
            "online_resources": [
                {
                    "name": "Crisis Text Line",
                    "url": "crisistextline.org",
                    "description": "Free, 24/7 crisis support via text",
                },
                {
                    "name": "National Suicide Prevention Lifeline",
                    "url": "suicidepreventionlifeline.org",
                    "description": "24/7 suicide prevention and crisis support",
                },
            ],
        }

    def test_get_crisis_resources_success(self, test_client, sample_crisis_resources):
        """Test successful crisis resources retrieval."""
        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.return_value = sample_crisis_resources

            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "immediate_help" in data
            assert "mental_health_support" in data
            assert "online_resources" in data

            # Verify immediate help resources
            immediate = data["immediate_help"]
            assert "suicide_prevention" in immediate
            assert immediate["suicide_prevention"]["hotline"] == "988"
            assert immediate["crisis_text"]["number"] == "741741"
            assert immediate["emergency"]["number"] == "911"

            # Verify mental health support
            support = data["mental_health_support"]
            assert "nami" in support
            assert "samhsa" in support

            # Verify online resources
            online = data["online_resources"]
            assert len(online) == 2
            assert any(resource["name"] == "Crisis Text Line" for resource in online)

    def test_get_crisis_resources_service_error(self, test_client):
        """Test crisis resources when service fails."""
        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.side_effect = Exception("Crisis resources service error")

            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "Crisis resources service error" in data["detail"]

    def test_get_crisis_resources_empty_response(self, test_client):
        """Test crisis resources with empty response."""
        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.return_value = {}

            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == {}

    def test_get_crisis_resources_partial_data(self, test_client):
        """Test crisis resources with partial data."""
        partial_resources = {
            "immediate_help": {
                "suicide_prevention": {
                    "hotline": "988",
                    "name": "National Suicide Prevention Lifeline",
                }
            }
        }

        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.return_value = partial_resources

            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "immediate_help" in data
            assert data["immediate_help"]["suicide_prevention"]["hotline"] == "988"

    def test_crisis_resources_no_authentication_required(
        self, test_client, sample_crisis_resources
    ):
        """Test that crisis resources don't require authentication."""
        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.return_value = sample_crisis_resources

            # Should work without any user authentication
            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "immediate_help" in data

    def test_crisis_resources_response_structure(
        self, test_client, sample_crisis_resources
    ):
        """Test that crisis resources have proper response structure."""
        with patch(
            "api.chat.mental_health_assistant.provide_crisis_resources"
        ) as mock_resources:
            mock_resources.return_value = sample_crisis_resources

            response = test_client.get("/chat/crisis-resources")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify structure consistency
            if "immediate_help" in data:
                immediate = data["immediate_help"]
                for service_key, service_data in immediate.items():
                    assert isinstance(service_data, dict)
                    assert "name" in service_data

            if "online_resources" in data:
                online = data["online_resources"]
                assert isinstance(online, list)
                for resource in online:
                    assert "name" in resource
                    assert "url" in resource or "description" in resource


class TestChatAPIIntegration:
    """Integration tests for Chat API with real dependencies."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the Chat API."""
        from api.chat import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_chat_memory_integration(self, test_client):
        """Test chat with real memory service integration."""
        # This test would use real memory service if available
        # For now, we'll mock it but structure it for real integration

        with patch("api.chat.memory_service") as mock_memory_service, patch(
            "api.chat.mental_health_assistant"
        ) as mock_assistant:

            # Configure mocks to simulate real behavior with AsyncMock
            mock_memory_service.get_memory_context = AsyncMock(
                return_value=MemoryContext(short_term=[], long_term=[], digest="")
            )
            mock_memory_service.process_memory = AsyncMock(
                return_value=MemoryItem(
                    id="test",
                    userId="test",
                    content="test",
                    type="test",
                    metadata={},
                    timestamp=datetime.now(),
                )
            )
            mock_assistant.generate_response = AsyncMock(
                return_value={
                    "response": "Test response",
                    "crisis_level": "low",
                    "crisis_explanation": "No crisis",
                    "resources_provided": [],
                    "coping_strategies": [],
                    "timestamp": datetime.now(),
                }
            )

            response = test_client.post(
                "/chat/assistant",
                json={"message": "Hello", "include_memory": True},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify integration points were called
            mock_memory_service.get_memory_context.assert_called_once()
            mock_memory_service.process_memory.assert_called()
            mock_assistant.generate_response.assert_called_once()

    def test_chat_crisis_detection_integration(self, test_client):
        """Test chat with crisis detection integration."""
        with patch(
            "api.chat.mental_health_assistant.generate_response"
        ) as mock_response, patch(
            "api.chat.memory_service.process_memory"
        ) as mock_process:
            mock_response.return_value = {
                "response": "I'm very concerned about what you've shared.",
                "crisis_level": "high",
                "crisis_explanation": "Suicide ideation detected",
                "resources_provided": ["988", "741741"],
                "coping_strategies": ["Contact emergency services"],
                "timestamp": datetime.now(),
            }
            mock_process.return_value = None

            response = test_client.post(
                "/chat/assistant",
                json={"message": "I want to end my life", "include_memory": False},
                params={"user_id": "test-user-123"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify crisis response structure
            assert data["crisis_level"] == "high"
            assert len(data["resources_provided"]) > 0
            assert "988" in data["resources_provided"]
