"""
Tests for Vapi memory search endpoints in memory API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app

client = TestClient(app)


class TestMemorySearchEndpoints:
    """Test the Vapi memory search integration endpoints."""

    @patch("services.memory.memoryService.MemoryService")
    def test_memory_search_success(self, mock_memory_service):
        """Test successful memory search."""
        # Mock the vector store search
        mock_instance = MagicMock()
        mock_memory_service.return_value = mock_instance

        mock_instance.vector_store.similarity_search.return_value = [
            {"content": "User mentioned feeling anxious about finals", "score": 0.9},
            {"content": "User prefers morning meditation", "score": 0.7},
            {"content": "User's dog helps with stress relief", "score": 0.6},
        ]

        # Test the search endpoint
        response = client.post(
            "/api/memory/search",
            json={
                "user_id": "test_user_123",
                "query": "anxiety management",
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "chunks" in data
        assert len(data["chunks"]) == 3
        assert (
            data["chunks"][0]["text"] == "User mentioned feeling anxious about finals"
        )
        assert data["chunks"][0]["score"] == 0.9

    @patch("services.memory.memoryService.MemoryService")
    def test_memory_search_service_error(self, mock_memory_service):
        """Test memory search with service error returns 502."""
        mock_instance = MagicMock()
        mock_memory_service.return_value = mock_instance

        # Mock service error
        mock_instance.vector_store.similarity_search.side_effect = Exception(
            "Vector store connection failed"
        )

        response = client.post(
            "/api/memory/search",
            json={"user_id": "test_user_123", "query": "test query", "top_k": 5},
        )

        assert response.status_code == 502
        assert "temporarily unavailable" in response.json()["detail"]

    @patch("services.memory.memoryService.MemoryService")
    def test_push_memory_success(self, mock_memory_service):
        """Test successful memory storage."""
        mock_instance = MagicMock()
        mock_memory_service.return_value = mock_instance

        # Mock successful storage
        mock_instance.process_memory.return_value = {
            "stored": True,
            "components": [{"component_memory": {"id": "memory_123"}}],
        }

        response = client.post(
            "/api/memory/push",
            json={
                "user_id": "test_user_123",
                "content": "User had a breakthrough about managing stress",
                "type": "breakthrough",
                "metadata": {"emotion": "hopeful", "importance": "high"},
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["memory_id"] == "memory_123"
        assert "successfully" in data["message"]

    @patch("services.memory.memoryService.MemoryService")
    def test_push_memory_needs_consent(self, mock_memory_service):
        """Test memory storage that requires consent."""
        mock_instance = MagicMock()
        mock_memory_service.return_value = mock_instance

        # Mock consent required
        mock_instance.process_memory.return_value = {
            "needs_consent": True,
            "memory_id": "temp_memory_456",
        }

        response = client.post(
            "/api/memory/push",
            json={
                "user_id": "test_user_123",
                "content": "User mentioned their therapist Dr. Smith helped them",
                "type": "voice_interaction",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["memory_id"] == "temp_memory_456"
        assert "consent required" in data["message"]

    def test_vapi_tools_endpoint(self):
        """Test the Vapi tool definitions endpoint."""
        response = client.get("/api/memory/vapi-tools")

        assert response.status_code == 200
        data = response.json()

        assert "tools" in data
        assert len(data["tools"]) == 2

        # Check search tool
        search_tool = data["tools"][0]
        assert search_tool["function"]["name"] == "search_user_memories"
        assert "user_id" in search_tool["function"]["parameters"]["properties"]
        assert "query" in search_tool["function"]["parameters"]["properties"]

        # Check store tool
        store_tool = data["tools"][1]
        assert store_tool["function"]["name"] == "store_conversation_memory"
        assert "content" in store_tool["function"]["parameters"]["properties"]

    def test_memory_search_validation(self):
        """Test request validation for memory search."""
        # Test missing required fields
        response = client.post(
            "/api/memory/search",
            json={
                "user_id": "test_user_123"
                # Missing query
            },
        )
        assert response.status_code == 422

        # Test invalid top_k
        response = client.post(
            "/api/memory/search",
            json={"user_id": "test_user_123", "query": "test", "top_k": 25},  # Too high
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
