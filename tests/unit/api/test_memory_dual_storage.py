"""
Unit tests for Memory API dual storage strategy.
Tests short-term and long-term storage decisions, PII handling, and storage transitions.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json
from datetime import datetime, timedelta

from services.memory.types import MemoryItem, MemoryScore, MemoryContext, MemoryStats


class TestDualStorageStrategy:
    """Test suite for dual storage strategy implementation."""

    def test_short_term_storage_immediate(self, test_client):
        """Test immediate short-term storage for chat messages."""
        user_id = "test-user-123"
        chat_request = {
            "content": "I'm feeling anxious about my job interview tomorrow.",
            "type": "chat",
            "metadata": {"source": "chat_interface", "session_id": "sess_123"},
        }

        mock_result = {
            "needs_consent": False,
            "stored": True,
            "total_components": 1,
            "stored_components": 1,
            "components": [
                {
                    "component_content": "I'm feeling anxious about my job interview tomorrow.",
                    "memory_type": "emotional_concern",
                    "storage_recommendation": "short_term",
                    "stored": True,
                    "score": {
                        "relevance": 0.75,
                        "stability": 0.60,
                        "explicitness": 0.80,
                    },
                    "storage_details": {
                        "storage_type": "short_term",
                        "storage_location": "redis_store",
                        "reason": "Chat message - immediate storage",
                    },
                    "component_memory": {
                        "id": "mem_123",
                        "content": "I'm feeling anxious about my job interview tomorrow.",
                        "type": "chat",
                    },
                }
            ],
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_result

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=chat_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check DualStorageMemoryResponse structure
            assert "needs_consent" in data
            assert "stored" in data
            assert "components" in data

            assert data["needs_consent"] is False
            assert data["stored"] is True
            assert (
                data["components"][0]["storage_details"]["storage_type"] == "short_term"
            )
            assert (
                data["components"][0]["storage_details"]["storage_location"]
                == "redis_store"
            )

    def test_long_term_storage_high_score(self, test_client):
        """Test long-term storage for high-scoring therapeutic content."""
        user_id = "test-user-123"
        reflection_request = {
            "content": "I had a major breakthrough in therapy today. I finally understand why I have trust issues - it stems from my childhood. This insight feels life-changing.",
            "type": "reflection",
            "metadata": {"source": "journal_entry", "therapeutic_value": "high"},
        }

        mock_result = {
            "needs_consent": False,
            "stored": True,
            "total_components": 2,
            "stored_components": 2,
            "components": [
                {
                    "component_content": "Major breakthrough understanding trust issues from childhood",
                    "memory_type": "therapeutic_insight",
                    "storage_recommendation": "long_term",
                    "stored": True,
                    "score": {
                        "relevance": 0.95,
                        "stability": 0.90,
                        "explicitness": 0.85,
                    },
                    "storage_details": {
                        "storage_type": "long_term",
                        "storage_location": "vector_store",
                        "reason": "High therapeutic value - stable insight",
                    },
                },
                {
                    "component_content": "Therapy breakthrough about childhood experiences",
                    "memory_type": "emotional_anchor",
                    "storage_recommendation": "long_term",
                    "stored": True,
                    "score": {
                        "relevance": 0.92,
                        "stability": 0.88,
                        "explicitness": 0.80,
                    },
                    "storage_details": {
                        "storage_type": "long_term",
                        "storage_location": "vector_store",
                        "reason": "Emotional anchor - lasting significance",
                    },
                },
            ],
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_result

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=reflection_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["stored"] is True
            assert data["stored_components"] == 2
            assert all(
                comp["storage_details"]["storage_type"] == "long_term"
                for comp in data["components"]
            )

    def test_dual_storage_with_pii_detected(self, test_client):
        """Test dual storage behavior when PII is detected."""
        user_id = "test-user-123"
        pii_request = {
            "content": "My therapist Dr. Sarah Johnson at 123 Main Street helped me work through my anxiety. My phone is 555-123-4567.",
            "type": "chat",
            "metadata": {"source": "chat_interface"},
        }

        mock_consent_needed = {
            "needs_consent": True,
            "stored": False,
            "memory_id": "mem_456",
            "consent_options": {
                "pii_item_1": {
                    "text": "Dr. Sarah Johnson",
                    "type": "PERSON",
                    "options": ["keep", "anonymize", "remove"],
                },
                "pii_item_2": {
                    "text": "123 Main Street",
                    "type": "ADDRESS",
                    "options": ["keep", "anonymize", "remove"],
                },
                "pii_item_3": {
                    "text": "555-123-4567",
                    "type": "PHONE_NUMBER",
                    "options": ["keep", "anonymize", "remove"],
                },
            },
            "pii_summary": {
                "has_pii": True,
                "detected_items": [
                    {
                        "text": "Dr. Sarah Johnson",
                        "type": "PERSON",
                        "risk_level": "medium",
                    },
                    {
                        "text": "123 Main Street",
                        "type": "ADDRESS",
                        "risk_level": "high",
                    },
                    {
                        "text": "555-123-4567",
                        "type": "PHONE_NUMBER",
                        "risk_level": "high",
                    },
                ],
            },
            "storage_details": {
                "short_term_stored": True,
                "long_term_pending": True,
                "reason": "PII detected - consent required for long-term storage",
            },
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_consent_needed

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=pii_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["needs_consent"] is True
            assert "consent_options" in data
            assert len(data["consent_options"]) == 3
            assert data["pii_summary"]["has_pii"] is True
            assert "storage_details" in data

    def test_dual_storage_with_user_consent(self, test_client):
        """Test dual storage after user provides consent."""
        user_id = "test-user-123"
        consent_request = {
            "content": "My therapist Dr. Sarah Johnson helped me with anxiety.",
            "type": "chat",
            "metadata": {"source": "chat_interface"},
            "user_consent": {
                "pii_item_1": {
                    "action": "anonymize"
                },  # Dr. Sarah Johnson -> [THERAPIST]
                "pii_item_2": {"action": "keep"},  # Keep other content
            },
        }

        mock_result_with_consent = {
            "needs_consent": False,
            "stored": True,
            "total_components": 1,
            "stored_components": 1,
            "components": [
                {
                    "component_content": "My therapist [THERAPIST] helped me with anxiety.",
                    "memory_type": "therapeutic_support",
                    "storage_recommendation": "long_term",
                    "stored": True,
                    "score": {
                        "relevance": 0.85,
                        "stability": 0.75,
                        "explicitness": 0.70,
                    },
                    "storage_details": {
                        "storage_type": "long_term",
                        "storage_location": "vector_store",
                        "reason": "Consent provided - PII anonymized",
                        "anonymization_applied": True,
                    },
                    "pii_handling": {
                        "original_pii_count": 1,
                        "anonymized_count": 1,
                        "consent_status": "granted_with_anonymization",
                    },
                }
            ],
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_result_with_consent

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=consent_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["stored"] is True
            component = data["components"][0]
            assert "[THERAPIST]" in component["component_content"]
            assert component["storage_details"]["anonymization_applied"] is True
            assert (
                component["pii_handling"]["consent_status"]
                == "granted_with_anonymization"
            )

    def test_storage_transition_criteria(self, test_client):
        """Test criteria for transitioning from short-term to long-term storage."""
        user_id = "test-user-123"

        # Test various scenarios with different scores
        test_cases = [
            {
                "content": "Just had a quick chat about the weather",
                "expected_storage": "short_term",
                "scores": {"relevance": 0.3, "stability": 0.2, "explicitness": 0.4},
            },
            {
                "content": "Discovered a new coping strategy that really works for my anxiety",
                "expected_storage": "long_term",
                "scores": {"relevance": 0.9, "stability": 0.8, "explicitness": 0.7},
            },
            {
                "content": "The weather is nice today",
                "expected_storage": "short_term",
                "scores": {"relevance": 0.1, "stability": 0.1, "explicitness": 0.2},
            },
        ]

        for i, case in enumerate(test_cases):
            mock_result = {
                "needs_consent": False,
                "stored": True,
                "total_components": 1,
                "stored_components": 1,
                "components": [
                    {
                        "component_content": case["content"],
                        "memory_type": "general_content",
                        "storage_recommendation": case["expected_storage"],
                        "stored": True,
                        "score": case["scores"],
                        "storage_details": {
                            "storage_type": case["expected_storage"],
                            "storage_location": (
                                "vector_store"
                                if case["expected_storage"] == "long_term"
                                else "redis_store"
                            ),
                            "decision_criteria": f"Score-based decision: {case['expected_storage']}",
                        },
                    }
                ],
            }

            with patch(
                "services.memory.memoryService.MemoryService.process_memory"
            ) as mock_process:
                mock_process.return_value = mock_result

                response = test_client.post(
                    f"/api/memory/dual-storage?user_id={user_id}",
                    json={"content": case["content"], "type": "chat"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                storage_type = data["components"][0]["storage_details"]["storage_type"]
                assert (
                    storage_type == case["expected_storage"]
                ), f"Case {i}: Expected {case['expected_storage']}, got {storage_type}"


class TestStorageRetrieval:
    """Test suite for retrieving memories from dual storage."""

    def test_retrieve_mixed_storage_context(self, test_client):
        """Test context retrieval combining short-term and long-term memories."""
        user_id = "test-user-123"

        # Mock MemoryContext with the correct structure
        mock_context = MemoryContext(
            short_term=[
                "Recent chat about work stress (short-term)",
                "Today's mood check-in (short-term)",
                "Discussion about coping strategies (short-term)",
                "Anxiety episode last week (short-term)",
            ],
            long_term=[
                "Core insight about anxiety triggers (long-term)",
                "First therapy breakthrough (long-term)",
            ],
            digest="Combining recent concerns with established therapeutic insights",
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_context"
        ) as mock_context_method:
            mock_context_method.return_value = mock_context

            response = test_client.post(
                f"/api/memory/context?user_id={user_id}",
                json={"query": "How am I handling stress?"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "context" in data
            context = data["context"]
            assert len(context["short_term"]) == 4
            assert len(context["long_term"]) == 2
            assert "therapeutic insights" in context["digest"]

    def test_retrieve_long_term_only(self, test_client):
        """Test retrieval of only long-term memories."""
        user_id = "test-user-123"

        # Mock MemoryItem objects for long-term memories
        from services.memory.types import MemoryItem
        from datetime import datetime

        mock_long_term_memories = [
            MemoryItem(
                id="lt_mem_1",
                userId=user_id,
                content="Core therapeutic insight about self-worth",
                type="insight",
                metadata={"therapeutic_value": "high", "anchor_weight": 0.9},
                timestamp=datetime.fromisoformat("2024-01-15T10:00:00"),
            ),
            MemoryItem(
                id="lt_mem_2",
                userId=user_id,
                content="Breakthrough moment understanding family dynamics",
                type="emotional_anchor",
                metadata={"therapeutic_value": "very_high", "anchor_weight": 0.95},
                timestamp=datetime.fromisoformat("2024-01-10T14:30:00"),
            ),
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_regular_memories"
        ) as mock_memories:
            mock_memories.return_value = mock_long_term_memories

            response = test_client.get(f"/api/memory/all-long-term?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "regular_memories" in data
            assert len(data["regular_memories"]) == 2
            assert data["regular_memories"][0]["type"] == "insight"
            assert data["regular_memories"][1]["type"] == "emotional_anchor"

    def test_retrieve_emotional_anchors_only(self, test_client):
        """Test retrieval of emotional anchors specifically."""
        user_id = "test-user-123"

        # Mock MemoryItem objects for emotional anchors
        from services.memory.types import MemoryItem
        from datetime import datetime

        mock_anchors = [
            MemoryItem(
                id="anchor_1",
                userId=user_id,
                content="First time I felt truly understood in therapy",
                type="emotional_anchor",
                metadata={
                    "emotional_weight": 0.95,
                    "anchor_strength": "very_strong",
                    "therapeutic_significance": "breakthrough_moment",
                },
                timestamp=datetime.fromisoformat("2024-01-20T11:15:00"),
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

            assert "emotional_anchors" in data
            assert len(data["emotional_anchors"]) == 1
            anchor = data["emotional_anchors"][0]
            assert anchor["type"] == "emotional_anchor"
            assert anchor["metadata"]["emotional_weight"] == 0.95


class TestStorageManagement:
    """Test suite for storage management operations."""

    def test_delete_from_both_storages(self, test_client):
        """Test deleting a memory that might exist in both storages."""
        user_id = "test-user-123"
        memory_id = "mem_duplicate"

        with patch(
            "services.memory.memoryService.MemoryService.delete_memory"
        ) as mock_delete:
            mock_delete.return_value = True  # Found and deleted

            response = test_client.delete(f"/api/memory/{memory_id}?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "message" in data
            assert "deleted successfully" in data["message"]

            mock_delete.assert_called_once_with(user_id, memory_id)

    def test_clear_both_storages(self, test_client):
        """Test clearing memories from both short-term and long-term storage."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.clear_memories"
        ) as mock_clear:
            mock_clear.return_value = None

            response = test_client.post(f"/api/memory/forget?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "message" in data
            assert "cleared successfully" in data["message"]

            mock_clear.assert_called_once_with(user_id)

    def test_storage_statistics_breakdown(self, test_client):
        """Test memory statistics showing storage breakdown."""
        user_id = "test-user-123"

        # Mock MemoryStats with the correct structure
        mock_stats = MemoryStats(
            total=100,
            short_term=30,
            long_term=70,
            sensitive=15,
        )

        with patch(
            "services.memory.memoryService.MemoryService.get_memory_stats"
        ) as mock_stats_method:
            mock_stats_method.return_value = mock_stats

            response = test_client.get(f"/api/memory/stats?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "stats" in data
            stats = data["stats"]
            assert stats["total"] == 100
            assert stats["short_term"] == 30
            assert stats["long_term"] == 70
            assert stats["sensitive"] == 15


class TestDualStorageErrorHandling:
    """Test suite for error handling in dual storage scenarios."""

    def test_storage_failure_graceful_degradation(self, test_client):
        """Test graceful handling when one storage system fails."""
        user_id = "test-user-123"
        memory_request = {"content": "Test content for storage failure", "type": "chat"}

        # Simulate partial storage failure
        mock_result = {
            "needs_consent": False,
            "stored": True,
            "total_components": 1,
            "stored_components": 1,
            "components": [
                {
                    "component_content": "Test content for storage failure",
                    "memory_type": "general_content",
                    "storage_recommendation": "short_term",
                    "stored": True,
                    "score": {"relevance": 0.5, "stability": 0.4, "explicitness": 0.6},
                    "storage_details": {
                        "storage_type": "short_term",
                        "storage_location": "redis_store",
                        "reason": "Fallback to short-term due to long-term storage error",
                    },
                    "warnings": ["Long-term storage temporarily unavailable"],
                }
            ],
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_result

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=memory_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["stored"] is True
            component = data["components"][0]
            assert component["storage_details"]["storage_type"] == "short_term"
            assert "warnings" in component

    def test_pii_detection_failure_safe_storage(self, test_client):
        """Test safe storage behavior when PII detection fails."""
        user_id = "test-user-123"
        memory_request = {
            "content": "Content that might have PII but detection failed",
            "type": "chat",
        }

        mock_result = {
            "needs_consent": False,
            "stored": True,
            "total_components": 1,
            "stored_components": 1,
            "components": [
                {
                    "component_content": "Content that might have PII but detection failed",
                    "memory_type": "general_content",
                    "storage_recommendation": "short_term",
                    "stored": True,
                    "score": {"relevance": 0.6, "stability": 0.5, "explicitness": 0.7},
                    "storage_details": {
                        "storage_type": "short_term",
                        "storage_location": "redis_store",
                        "reason": "PII detection failed - defaulting to short-term storage",
                    },
                    "pii_handling": {
                        "detection_status": "failed",
                        "safety_mode": "enabled",
                        "recommendation": "Manual review recommended",
                    },
                }
            ],
        }

        with patch(
            "services.memory.memoryService.MemoryService.process_memory"
        ) as mock_process:
            mock_process.return_value = mock_result

            response = test_client.post(
                f"/api/memory/dual-storage?user_id={user_id}", json=memory_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["stored"] is True
            component = data["components"][0]
            assert component["pii_handling"]["detection_status"] == "failed"
            assert component["pii_handling"]["safety_mode"] == "enabled"

    def test_concurrent_access_handling(self, test_client):
        """Test handling of concurrent access to storage systems."""
        user_id = "test-user-123"

        # Simulate multiple rapid requests
        memory_requests = [
            {"content": f"Concurrent message {i}", "type": "chat"} for i in range(3)
        ]

        for i, req in enumerate(memory_requests):
            mock_result = {
                "needs_consent": False,
                "stored": True,
                "total_components": 1,
                "stored_components": 1,
                "components": [
                    {
                        "component_content": req["content"],
                        "memory_type": "general_content",
                        "storage_recommendation": "short_term",
                        "stored": True,
                        "score": {
                            "relevance": 0.5,
                            "stability": 0.4,
                            "explicitness": 0.6,
                        },
                        "storage_details": {
                            "storage_type": "short_term",
                            "storage_location": "redis_store",
                            "concurrent_id": f"req_{i}",
                            "processing_order": i + 1,
                        },
                    }
                ],
            }

            with patch(
                "services.memory.memoryService.MemoryService.process_memory"
            ) as mock_process:
                mock_process.return_value = mock_result

                response = test_client.post(
                    f"/api/memory/dual-storage?user_id={user_id}", json=req
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["stored"] is True
                component = data["components"][0]
                assert component["storage_details"]["concurrent_id"] == f"req_{i}"
                assert component["storage_details"]["processing_order"] == i + 1
