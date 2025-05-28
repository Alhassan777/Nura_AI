"""
Unit tests for Privacy Management API.
Tests privacy review, data export, deletion, and GDPR compliance.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json
from datetime import datetime, timedelta


class TestPrivacyReviewAPI:
    """Test suite for privacy review endpoints."""

    def test_get_privacy_review_success(self, test_client, sample_memory_content):
        """Test successful privacy review retrieval."""
        user_id = "test-user-123"

        # Mock memory service to return content with PII
        mock_memories = [
            {
                "id": "mem1",
                "content": "My name is John Doe and I feel anxious.",
                "timestamp": "2024-01-01T10:00:00Z",
                "pii_detected": True,
                "risk_level": "high",
            },
            {
                "id": "mem2",
                "content": "I had a good therapy session today.",
                "timestamp": "2024-01-01T11:00:00Z",
                "pii_detected": False,
                "risk_level": "low",
            },
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.return_value = mock_memories

            response = test_client.get(f"/api/memory/privacy-review/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "user_id" in data
            assert data["user_id"] == user_id
            assert "total_memories" in data
            assert data["total_memories"] == 2
            assert "memories_with_pii" in data
            assert data["memories_with_pii"] == 1
            assert "risk_breakdown" in data
            assert "memories" in data
            assert len(data["memories"]) == 2

    def test_get_privacy_review_user_not_found(self, test_client):
        """Test privacy review for non-existent user."""
        user_id = "nonexistent-user"

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.return_value = []

            response = test_client.get(f"/api/memory/privacy-review/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["total_memories"] == 0
            assert data["memories_with_pii"] == 0
            assert len(data["memories"]) == 0

    def test_get_privacy_review_with_date_filter(self, test_client):
        """Test privacy review with date range filtering."""
        user_id = "test-user-123"
        start_date = "2024-01-01"
        end_date = "2024-01-31"

        mock_memories = [
            {
                "id": "mem1",
                "content": "Recent memory with PII: john@example.com",
                "timestamp": "2024-01-15T10:00:00Z",
                "pii_detected": True,
                "risk_level": "high",
            }
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.return_value = mock_memories

            response = test_client.get(
                f"/api/memory/privacy-review/{user_id}?start_date={start_date}&end_date={end_date}"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should call with date filters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert user_id in call_args[0] or user_id in call_args[1].values()

    def test_get_privacy_review_risk_level_breakdown(self, test_client):
        """Test that privacy review includes proper risk level breakdown."""
        user_id = "test-user-123"

        mock_memories = [
            {
                "id": "1",
                "content": "High risk",
                "pii_detected": True,
                "risk_level": "high",
            },
            {
                "id": "2",
                "content": "Medium risk",
                "pii_detected": True,
                "risk_level": "medium",
            },
            {
                "id": "3",
                "content": "Low risk",
                "pii_detected": False,
                "risk_level": "low",
            },
            {
                "id": "4",
                "content": "Another high",
                "pii_detected": True,
                "risk_level": "high",
            },
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.return_value = mock_memories

            response = test_client.get(f"/api/memory/privacy-review/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            risk_breakdown = data["risk_breakdown"]
            assert risk_breakdown["high"] == 2
            assert risk_breakdown["medium"] == 1
            assert risk_breakdown["low"] == 1

    def test_get_privacy_review_pii_details(self, test_client):
        """Test that privacy review includes PII detection details."""
        user_id = "test-user-123"

        mock_memories = [
            {
                "id": "mem1",
                "content": "My name is John Doe",
                "pii_detected": True,
                "risk_level": "high",
                "pii_items": [
                    {
                        "entity_type": "PERSON",
                        "text": "John Doe",
                        "confidence": 0.95,
                        "start": 11,
                        "end": 19,
                    }
                ],
            }
        ]

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.return_value = mock_memories

            response = test_client.get(f"/api/memory/privacy-review/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            memory = data["memories"][0]
            assert "pii_items" in memory
            assert len(memory["pii_items"]) == 1
            assert memory["pii_items"][0]["entity_type"] == "PERSON"

    def test_get_privacy_review_service_error(self, test_client):
        """Test privacy review when memory service fails."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.get_user_memories"
        ) as mock_get:
            mock_get.side_effect = Exception("Memory service error")

            response = test_client.get(f"/api/memory/privacy-review/{user_id}")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "Memory service error" in data["detail"]["error"]


class TestPrivacyChoicesAPI:
    """Test suite for privacy choices application."""

    def test_apply_privacy_choices_anonymize(self, test_client):
        """Test applying privacy choices to anonymize PII."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "anonymize",
            "memory_ids": ["mem1", "mem2"],
            "pii_types": ["PERSON", "EMAIL_ADDRESS"],
            "reason": "User requested anonymization",
        }

        with patch(
            "services.memory.memoryService.MemoryService.anonymize_memories"
        ) as mock_anon:
            mock_anon.return_value = {"processed": 2, "anonymized": 2, "failed": 0}

            response = test_client.post(
                f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "success"
            assert data["processed"] == 2
            assert data["anonymized"] == 2
            assert data["failed"] == 0

            # Verify service was called correctly
            mock_anon.assert_called_once_with(
                user_id, ["mem1", "mem2"], ["PERSON", "EMAIL_ADDRESS"]
            )

    def test_apply_privacy_choices_delete(self, test_client):
        """Test applying privacy choices to delete memories."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "delete",
            "memory_ids": ["mem1", "mem2"],
            "reason": "User requested deletion",
        }

        with patch(
            "services.memory.memoryService.MemoryService.delete_memories"
        ) as mock_delete:
            mock_delete.return_value = {"processed": 2, "deleted": 2, "failed": 0}

            response = test_client.post(
                f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "success"
            assert data["processed"] == 2
            assert data["deleted"] == 2

            # Verify service was called correctly
            mock_delete.assert_called_once_with(user_id, ["mem1", "mem2"])

    def test_apply_privacy_choices_export(self, test_client):
        """Test applying privacy choices to export data."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "export",
            "format": "json",
            "include_metadata": True,
            "reason": "GDPR data export request",
        }

        mock_export_data = {
            "user_id": user_id,
            "export_date": "2024-01-01T10:00:00Z",
            "memories": [
                {
                    "id": "mem1",
                    "content": "Test memory",
                    "timestamp": "2024-01-01T09:00:00Z",
                }
            ],
            "metadata": {"total_memories": 1, "export_format": "json"},
        }

        with patch(
            "services.memory.memoryService.MemoryService.export_user_data"
        ) as mock_export:
            mock_export.return_value = mock_export_data

            response = test_client.post(
                f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "success"
            assert "export_data" in data
            assert data["export_data"]["user_id"] == user_id

    def test_apply_privacy_choices_invalid_action(self, test_client):
        """Test privacy choices with invalid action."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "invalid_action",
            "memory_ids": ["mem1"],
            "reason": "Test",
        }

        response = test_client.post(
            f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "invalid action" in data["detail"].lower()

    def test_apply_privacy_choices_missing_memory_ids(self, test_client):
        """Test privacy choices without memory IDs for actions that require them."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "anonymize",
            "reason": "Test",
            # Missing memory_ids
        }

        response = test_client.post(
            f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    def test_apply_privacy_choices_service_error(self, test_client):
        """Test privacy choices when service operation fails."""
        user_id = "test-user-123"
        privacy_request = {"action": "delete", "memory_ids": ["mem1"], "reason": "Test"}

        with patch(
            "services.memory.memoryService.MemoryService.delete_memories"
        ) as mock_delete:
            mock_delete.side_effect = Exception("Service error")

            response = test_client.post(
                f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]

    def test_apply_privacy_choices_partial_failure(self, test_client):
        """Test privacy choices with partial operation failure."""
        user_id = "test-user-123"
        privacy_request = {
            "action": "anonymize",
            "memory_ids": ["mem1", "mem2", "mem3"],
            "pii_types": ["PERSON"],
            "reason": "Test",
        }

        with patch(
            "services.memory.memoryService.MemoryService.anonymize_memories"
        ) as mock_anon:
            mock_anon.return_value = {
                "processed": 3,
                "anonymized": 2,
                "failed": 1,
                "errors": ["Failed to anonymize mem3: Memory not found"],
            }

            response = test_client.post(
                f"/api/memory/apply-privacy-choices/{user_id}", json=privacy_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "partial_success"
            assert data["processed"] == 3
            assert data["anonymized"] == 2
            assert data["failed"] == 1
            assert "errors" in data


class TestGDPRComplianceAPI:
    """Test suite for GDPR compliance features."""

    def test_gdpr_data_export_request(self, test_client):
        """Test GDPR-compliant data export."""
        user_id = "test-user-123"

        mock_export_data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "data_categories": {
                "memories": 150,
                "chat_sessions": 25,
                "voice_interactions": 10,
            },
            "memories": [
                {
                    "id": "mem1",
                    "content": "Test memory content",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "pii_detected": False,
                }
            ],
            "metadata": {
                "export_format": "json",
                "privacy_compliant": True,
                "retention_period": "7 years",
            },
        }

        with patch(
            "services.memory.memoryService.MemoryService.export_user_data"
        ) as mock_export:
            mock_export.return_value = mock_export_data

            response = test_client.get(f"/api/memory/gdpr/export/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["user_id"] == user_id
            assert "export_date" in data
            assert "data_categories" in data
            assert data["metadata"]["privacy_compliant"] is True

    def test_gdpr_right_to_be_forgotten(self, test_client):
        """Test GDPR right to be forgotten (complete data deletion)."""
        user_id = "test-user-123"

        deletion_request = {
            "confirmation": "I understand this action is irreversible",
            "reason": "GDPR Article 17 - Right to erasure",
        }

        with patch(
            "services.memory.memoryService.MemoryService.delete_all_user_data"
        ) as mock_delete:
            mock_delete.return_value = {
                "user_id": user_id,
                "deletion_date": datetime.utcnow().isoformat(),
                "deleted_items": {
                    "memories": 150,
                    "chat_sessions": 25,
                    "voice_interactions": 10,
                    "user_profile": 1,
                },
                "status": "completed",
            }

            response = test_client.request(
                "DELETE",
                f"/api/memory/gdpr/delete-all/{user_id}",
                json=deletion_request,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "completed"
            assert data["user_id"] == user_id
            assert "deletion_date" in data
            assert data["deleted_items"]["memories"] == 150

    def test_gdpr_data_portability(self, test_client):
        """Test GDPR data portability in machine-readable format."""
        user_id = "test-user-123"

        with patch(
            "services.memory.memoryService.MemoryService.export_portable_data"
        ) as mock_export:
            mock_export.return_value = {
                "format": "json",
                "schema_version": "1.0",
                "export_date": datetime.utcnow().isoformat(),
                "user_data": {"memories": [], "preferences": {}, "interactions": []},
            }

            response = test_client.get(f"/api/memory/gdpr/portable/{user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["format"] == "json"
            assert "schema_version" in data
            assert "user_data" in data

    def test_gdpr_consent_management(self, test_client):
        """Test GDPR consent management."""
        user_id = "test-user-123"

        consent_update = {
            "data_processing": True,
            "analytics": False,
            "marketing": False,
            "third_party_sharing": False,
            "consent_date": datetime.utcnow().isoformat(),
        }

        with patch(
            "services.memory.memoryService.MemoryService.update_consent"
        ) as mock_consent:
            mock_consent.return_value = {
                "user_id": user_id,
                "consent_updated": True,
                "effective_date": consent_update["consent_date"],
            }

            response = test_client.post(
                f"/api/memory/gdpr/consent/{user_id}", json=consent_update
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["consent_updated"] is True
            assert data["user_id"] == user_id

    def test_gdpr_data_retention_policy(self, test_client):
        """Test GDPR data retention policy information."""
        response = test_client.get("/api/memory/gdpr/retention-policy")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "retention_periods" in data
        assert "legal_basis" in data
        assert "contact_info" in data

        # Should specify retention periods for different data types
        retention = data["retention_periods"]
        assert "short_term_memories" in retention
        assert "long_term_memories" in retention
        assert "pii_data" in retention
