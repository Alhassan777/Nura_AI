"""
Unit tests for Memory API endpoints.
Tests all memory-related endpoints including process, context, stats, and management operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json
from datetime import datetime, timedelta

from services.memory.types import MemoryItem, MemoryContext, MemoryStats


class TestMemoryProcessingAPI:
    """Test suite for memory processing endpoints."""

    def test_process_memory_success(self, test_client):
        """Test successful memory processing."""
        user_id = "test-user-123"
        memory_request = {
            "content": "I had a great therapy session today and feel much better.",
            "type": "chat",
            "metadata": {"source": "chat_interface", "session_id": "sess_123"},
        }

        # Mock MemoryItem that the service would return
        mock_memory = MemoryItem(
            id="test-memory-id",
            userId=user_id,
            content=memory_request["content"],
            type=memory_request["type"],
            metadata=memory_request["metadata"],
            timestamp=datetime.utcnow(),
        )

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_memory

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=memory_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual MemoryResponse structure
            assert "memory" in data
            assert "requires_consent" in data
            assert "sensitive_types" in data
            assert "configuration_status" in data

            assert data["memory"]["id"] == "test-memory-id"
            assert data["memory"]["content"] == memory_request["content"]
            assert data["requires_consent"] is False
            assert data["sensitive_types"] == []

            # Verify service was called correctly
            mock_process.assert_called_once_with(
                user_id=user_id,
                content=memory_request["content"],
                type=memory_request["type"],
                metadata=memory_request["metadata"],
            )

    def test_process_memory_with_consent(self, test_client):
        """Test memory processing with user consent for PII."""
        user_id = "test-user-123"
        memory_request = {
            "content": "My name is John Doe and I live in New York.",
            "type": "chat",
            "metadata": {"source": "chat_interface"},
        }

        # Mock MemoryItem with PII detected
        mock_memory_with_pii = MemoryItem(
            id="mem_123",
            userId=user_id,
            content=memory_request["content"],
            type=memory_request["type"],
            metadata={
                **memory_request["metadata"],
                "has_pii": True,
                "sensitive_types": ["PERSON", "LOCATION"],
                "requires_consent": True,
            },
            timestamp=datetime.utcnow(),
        )

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_memory_with_pii

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=memory_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual MemoryResponse structure for PII
            assert "memory" in data
            assert "requires_consent" in data
            assert "sensitive_types" in data

            assert data["memory"]["id"] == "mem_123"
            assert data["requires_consent"] is True
            assert data["sensitive_types"] == ["PERSON", "LOCATION"]

    def test_process_memory_invalid_request(self, test_client):
        """Test memory processing with invalid request data."""
        user_id = "test-user-123"

        # Missing required content field
        invalid_request = {"type": "chat", "metadata": {}}

        response = test_client.post(
            f"/api/memory/?user_id={user_id}", json=invalid_request
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_process_memory_service_error(self, test_client):
        """Test memory processing when service fails."""
        user_id = "test-user-123"
        memory_request = {"content": "Test content", "type": "chat"}

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.side_effect = Exception("Service error")

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=memory_request
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_process_memory_missing_user_id(self, test_client):
        """Test memory processing without user ID."""
        memory_request = {"content": "Test content", "type": "chat"}

        response = test_client.post("/api/memory/", json=memory_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMemoryContextAPI:
    """Test suite for memory context endpoints."""

    def test_get_memory_context_success(self, test_client):
        """Test successful memory context retrieval."""
        user_id = "test-user-123"

        # Mock MemoryContext that matches the actual structure
        from services.memory.types import MemoryContext

        mock_context = MemoryContext(
            short_term=[
                "Memory about therapy progress",
                "Discussion about coping strategies",
            ],
            long_term=["First breakthrough moment"],
            digest="User shows positive therapeutic progress with good coping strategies",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.return_value = mock_context

            response = test_client.post(
                f"/api/memory/context?user_id={user_id}",
                json={"query": "How am I doing with therapy?"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual MemoryContextResponse structure
            assert "context" in data
            assert "configuration_status" in data

            context = data["context"]
            assert "short_term" in context
            assert "long_term" in context
            assert "digest" in context

            assert len(context["short_term"]) == 2
            assert len(context["long_term"]) == 1
            assert "progress" in context["digest"].lower()

    def test_get_memory_context_no_query(self, test_client):
        """Test memory context retrieval without specific query."""
        user_id = "test-user-123"

        # Mock empty MemoryContext
        from services.memory.types import MemoryContext

        mock_context = MemoryContext(
            short_term=[],
            long_term=[],
            digest="User has no significant memory history",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.return_value = mock_context

            response = test_client.post(
                f"/api/memory/context?user_id={user_id}", json={}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "context" in data
            context = data["context"]
            assert len(context["short_term"]) == 0
            assert len(context["long_term"]) == 0

    def test_get_memory_context_service_error(self, test_client):
        """Test memory context when service fails."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.side_effect = Exception("Context service error")

            response = test_client.post(
                f"/api/memory/context?user_id={user_id}", json={"query": "test"}
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestMemoryStatsAPI:
    """Test suite for memory statistics endpoints."""

    def test_get_memory_stats_success(self, test_client):
        """Test successful memory statistics retrieval."""
        user_id = "test-user-123"

        # Mock MemoryStats that matches the actual structure
        from services.memory.types import MemoryStats

        mock_stats = MemoryStats(
            total=150,
            short_term=25,
            long_term=125,
            sensitive=15,
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_stats"
        ) as mock_stats_method:
            mock_stats_method.return_value = mock_stats

            response = test_client.get(f"/api/memory/stats?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual MemoryStatsResponse structure
            assert "stats" in data
            assert "configuration_status" in data

            stats = data["stats"]
            assert stats["total"] == 150
            assert stats["short_term"] == 25
            assert stats["long_term"] == 125
            assert stats["sensitive"] == 15

    def test_get_memory_stats_empty_user(self, test_client):
        """Test memory statistics for user with no memories."""
        user_id = "empty-user"

        # Mock empty MemoryStats
        from services.memory.types import MemoryStats

        mock_stats = MemoryStats(
            total=0,
            short_term=0,
            long_term=0,
            sensitive=0,
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_stats"
        ) as mock_stats_method:
            mock_stats_method.return_value = mock_stats

            response = test_client.get(f"/api/memory/stats?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["stats"]["total"] == 0


class TestMemoryManagementAPI:
    """Test suite for memory management endpoints (delete, clear, etc.)."""

    def test_delete_memory_success(self, test_client):
        """Test successful memory deletion."""
        user_id = "test-user-123"
        memory_id = "mem_123"

        with patch(
            "services.memory.memoryService.MemoryService.delete_memory"
        ) as mock_delete:
            mock_delete.return_value = True

            response = test_client.delete(f"/api/memory/{memory_id}?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual delete response structure
            assert "message" in data
            assert "deleted successfully" in data["message"]

            mock_delete.assert_called_once_with(user_id, memory_id)

    def test_delete_memory_not_found(self, test_client):
        """Test deletion of non-existent memory."""
        user_id = "test-user-123"
        memory_id = "nonexistent_mem"

        with patch(
            "services.memory.memoryService.MemoryService.delete_memory"
        ) as mock_delete:
            mock_delete.return_value = False

            response = test_client.delete(f"/api/memory/{memory_id}?user_id={user_id}")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()

            assert "not found" in data["detail"].lower()

    def test_clear_memories_success(self, test_client):
        """Test successful memory clearing."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.clear_memories"
        ) as mock_clear:
            mock_clear.return_value = None

            response = test_client.post(f"/api/memory/forget?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual clear response structure
            assert "message" in data
            assert "cleared successfully" in data["message"]

            mock_clear.assert_called_once_with(user_id)

    def test_export_memories_success(self, test_client):
        """Test successful memory export."""
        user_id = "test-user-123"

        # Mock MemoryContext that the export endpoint expects
        from services.memory.types import MemoryContext, MemoryItem
        from datetime import datetime

        mock_context = MemoryContext(
            short_term=[
                MemoryItem(
                    id="st_1",
                    userId=user_id,
                    content="Short term memory",
                    type="chat",
                    metadata={},
                    timestamp=datetime.utcnow(),
                )
            ],
            long_term=[
                MemoryItem(
                    id="lt_1",
                    userId=user_id,
                    content="Long term memory",
                    type="insight",
                    metadata={},
                    timestamp=datetime.utcnow(),
                )
            ],
            digest="Export test context",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.return_value = mock_context

            response = test_client.post(f"/api/memory/export?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual export response structure
            assert "short_term" in data
            assert "long_term" in data
            assert len(data["short_term"]) == 1
            assert len(data["long_term"]) == 1
            assert data["short_term"][0]["content"] == "Short term memory"
            assert data["long_term"][0]["content"] == "Long term memory"


class TestMemoryRetrievalAPI:
    """Test suite for memory retrieval endpoints."""

    def test_get_emotional_anchors_success(self, test_client):
        """Test successful emotional anchors retrieval."""
        user_id = "test-user-123"

        # Mock MemoryItem for emotional anchor
        from services.memory.types import MemoryItem
        from datetime import datetime

        mock_anchors = [
            MemoryItem(
                id="anchor_1",
                userId=user_id,
                content="First breakthrough in therapy",
                type="emotional_anchor",
                metadata={"significance": "high", "emotional_weight": 0.9},
                timestamp=datetime.utcnow(),
            )
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_emotional_anchors"
        ) as mock_anchors_method:
            mock_anchors_method.return_value = mock_anchors

            response = test_client.get(
                f"/api/memory/emotional-anchors?user_id={user_id}"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual emotional anchors response structure
            assert "emotional_anchors" in data
            assert "count" in data
            assert "configuration_status" in data

            assert data["count"] == 1
            assert len(data["emotional_anchors"]) == 1

            anchor = data["emotional_anchors"][0]
            assert anchor["type"] == "emotional_anchor"
            assert anchor["metadata"]["significance"] == "high"

    def test_get_regular_memories_success(self, test_client):
        """Test successful regular memories retrieval."""
        user_id = "test-user-123"
        search_query = "therapy progress"

        # Mock MemoryItem for regular memory
        from services.memory.types import MemoryItem
        from datetime import datetime

        mock_memories = [
            MemoryItem(
                id="mem_1",
                userId=user_id,
                content="Made progress in therapy session",
                type="reflection",
                metadata={"category": "progress"},
                timestamp=datetime.utcnow(),
            )
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_regular_memories"
        ) as mock_memories_method:
            mock_memories_method.return_value = mock_memories

            response = test_client.get(
                f"/api/memory/regular-memories?user_id={user_id}&query={search_query}"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual regular memories response structure
            assert "regular_memories" in data
            assert "count" in data
            assert "query" in data
            assert "configuration_status" in data

            assert data["count"] == 1
            assert data["query"] == search_query
            assert len(data["regular_memories"]) == 1
            assert data["regular_memories"][0]["type"] == "reflection"

            mock_memories_method.assert_called_once_with(user_id, search_query)

    def test_get_all_long_term_memories_success(self, test_client):
        """Test successful long-term memories retrieval."""
        user_id = "test-user-123"

        # Mock MemoryItems for both types
        from services.memory.types import MemoryItem
        from datetime import datetime

        mock_emotional_anchors = [
            MemoryItem(
                id="anchor_1",
                userId=user_id,
                content="First therapy breakthrough",
                type="emotional_anchor",
                metadata={"emotional_weight": 0.9},
                timestamp=datetime.utcnow(),
            )
        ]

        mock_regular_memories = [
            MemoryItem(
                id="reg_1",
                userId=user_id,
                content="Long-term therapeutic insight",
                type="insight",
                metadata={"storage_type": "long_term"},
                timestamp=datetime.utcnow(),
            )
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_emotional_anchors"
        ) as mock_anchors, patch(
            "services.memory.memoryService.MemoryService.get_regular_memories"
        ) as mock_memories:
            mock_anchors.return_value = mock_emotional_anchors
            mock_memories.return_value = mock_regular_memories

            response = test_client.get(f"/api/memory/all-long-term?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual all long-term response structure
            assert "emotional_anchors" in data
            assert "regular_memories" in data
            assert "counts" in data
            assert "configuration_status" in data

            assert len(data["emotional_anchors"]) == 1
            assert len(data["regular_memories"]) == 1
            assert data["counts"]["emotional_anchors"] == 1
            assert data["counts"]["regular_memories"] == 1
            assert data["counts"]["total"] == 2


class TestMemoryConsentAPI:
    """Test suite for memory consent management endpoints."""

    def test_handle_consent_grant(self, test_client):
        """Test granting consent for memory storage."""
        user_id = "test-user-123"
        consent_request = {"memory_id": "mem_123", "grant_consent": True}

        # Mock MemoryContext with the memory we're granting consent for
        from services.memory.types import MemoryContext, MemoryItem
        from datetime import datetime

        mock_memory = MemoryItem(
            id="mem_123",
            userId=user_id,
            content="Test memory content",
            type="chat",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        mock_context = MemoryContext(
            short_term=[mock_memory],
            long_term=[],
            digest="Test context",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.return_value = mock_context

            response = test_client.post(
                f"/api/memory/consent?user_id={user_id}", json=consent_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual ConsentResponse structure
            assert "success" in data
            assert "message" in data
            assert "configuration_status" in data

            assert data["success"] is True
            assert "granted successfully" in data["message"].lower()

    def test_handle_consent_deny(self, test_client):
        """Test denying consent for memory storage."""
        user_id = "test-user-123"
        consent_request = {"memory_id": "mem_123", "grant_consent": False}

        # Mock MemoryContext with the memory we're denying consent for
        from services.memory.types import MemoryContext, MemoryItem
        from datetime import datetime

        mock_memory = MemoryItem(
            id="mem_123",
            userId=user_id,
            content="Test memory content",
            type="chat",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        mock_context = MemoryContext(
            short_term=[mock_memory],
            long_term=[],
            digest="Test context",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method, patch(
            "services.memory.memoryService.MemoryService.delete_memory"
        ) as mock_delete:
            mock_context_method.return_value = mock_context
            mock_delete.return_value = True

            response = test_client.post(
                f"/api/memory/consent?user_id={user_id}", json=consent_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check the actual ConsentResponse structure
            assert "success" in data
            assert "message" in data

            assert data["success"] is True
            assert "deleted" in data["message"].lower()

            # Verify delete was called
            mock_delete.assert_called_once_with(user_id, "mem_123")

    def test_get_pending_consent_memories_success(self, test_client):
        """Test retrieval of memories pending consent."""
        user_id = "test-user-123"

        mock_pending = {
            "pending_memories": [
                {
                    "memory_id": "mem_123",
                    "content": "Content with PII",
                    "pii_detected": ["PERSON", "EMAIL"],
                    "requires_consent": True,
                }
            ],
            "total_pending": 1,
        }

        with patch(
            "services.memory.memoryService.MemoryService.get_pending_consent_memories"
        ) as mock_pending_method:
            mock_pending_method.return_value = mock_pending

            response = test_client.get(f"/api/memory/pending-consent?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "pending_memories" in data
            assert data["total_pending"] == 1
            assert len(data["pending_memories"]) == 1


class TestMemoryAPIErrorHandling:
    """Test suite for API error handling scenarios."""

    def test_missing_required_parameters(self, test_client):
        """Test API calls missing required parameters."""
        # Test memory processing without user_id
        response = test_client.post(
            "/api/memory/", json={"content": "test", "type": "chat"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_malformed_json_request(self, test_client):
        """Test API with malformed JSON."""
        user_id = "test-user-123"

        response = test_client.post(
            f"/api/memory/?user_id={user_id}", data="invalid json"
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_service_unavailable_error(self, test_client):
        """Test API when underlying service is unavailable."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_stats"
        ) as mock_stats:
            mock_stats.side_effect = ConnectionError("Service unavailable")

            response = test_client.get(f"/api/memory/stats?user_id={user_id}")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
