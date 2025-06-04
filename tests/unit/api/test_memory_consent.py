"""
Unit tests for Memory API consent management.
Tests PII consent workflows, granular consent options, and consent application.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
import json
from datetime import datetime, timedelta

from services.memory.types import MemoryItem


class TestConsentWorkflow:
    """Test suite for consent workflow implementation."""

    def test_consent_required_response(self, test_client):
        """Test API response when consent is required for PII."""
        user_id = "test-user-123"
        pii_content = {
            "content": "My name is John Smith and I live at 456 Oak Avenue, Springfield. Call me at (555) 987-6543.",
            "type": "chat",
            "metadata": {"source": "chat_interface"},
        }

        # Mock MemoryItem with PII detected
        mock_memory_with_pii = MemoryItem(
            id="mem_consent_123",
            userId=user_id,
            content=pii_content["content"],
            type=pii_content["type"],
            metadata={
                **pii_content["metadata"],
                "has_pii": True,
                "sensitive_types": ["PERSON", "ADDRESS", "PHONE_NUMBER"],
                "requires_consent": True,
            },
            timestamp=datetime.utcnow(),
        )

        with patch("api.memory.memory_service.process_memory") as mock_process:
            mock_process.return_value = mock_memory_with_pii

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=pii_content
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check MemoryResponse structure for PII detection
            assert "memory" in data
            assert "requires_consent" in data
            assert "sensitive_types" in data

            assert data["requires_consent"] is True
            assert data["sensitive_types"] == ["PERSON", "ADDRESS", "PHONE_NUMBER"]
            assert data["memory"]["id"] == "mem_consent_123"

    def test_granular_consent_application(self, test_client):
        """Test applying granular consent choices."""
        user_id = "test-user-123"
        consent_choices = {
            "content": "My name is John Smith and I live at 456 Oak Avenue.",
            "type": "chat",
            "metadata": {"source": "chat_interface"},
            "user_consent": {
                "pii_item_1": {
                    "text": "John Smith",
                    "type": "PERSON",
                    "action": "anonymize",
                },
                "pii_item_2": {
                    "text": "456 Oak Avenue",
                    "type": "ADDRESS",
                    "action": "remove",
                },
            },
        }

        # Create a MemoryItem object for the basic endpoint
        from datetime import datetime

        mock_memory_item = MemoryItem(
            id="mem_consent_123",
            userId=user_id,
            content="My name is [NAME] and I live .",
            type="chat",
            metadata={
                "source": "chat_interface",
                "has_pii": True,
                "sensitive_types": ["PERSON", "ADDRESS"],
                "consent_applied": True,
                "anonymized": True,
            },
            timestamp=datetime.utcnow(),
        )

        with patch("api.memory.memory_service.process_memory") as mock_process:
            mock_process.return_value = mock_memory_item

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=consent_choices
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["memory"]["id"] == "mem_consent_123"
            assert data["requires_consent"] is True
            assert "PERSON" in data["sensitive_types"]
            assert "ADDRESS" in data["sensitive_types"]

    def test_consent_denied_all_pii(self, test_client):
        """Test when user denies consent for all PII items."""
        user_id = "test-user-123"
        denial_request = {
            "content": "My phone is 555-123-4567 and email is john@example.com",
            "type": "chat",
            "user_consent": {
                "pii_item_1": {"action": "remove"},
                "pii_item_2": {"action": "remove"},
            },
        }

        # For denied consent, return None (no memory stored)
        with patch("api.memory.memory_service.process_memory") as mock_process:
            mock_process.return_value = None

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=denial_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["memory"] is None
            assert data["requires_consent"] is False
            assert data["sensitive_types"] == []


class TestConsentManagement:
    """Test suite for ongoing consent management."""

    def test_get_pending_consent_memories(self, test_client):
        """Test retrieving memories pending consent decisions."""
        user_id = "test-user-123"

        mock_pending_memories = {
            "pending_memories": [
                {
                    "memory_id": "mem_pending_1",
                    "content": "My therapist Dr. Johnson at 123 Main St helped me.",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "pii_detected": ["PERSON", "ADDRESS"],
                    "consent_deadline": "2024-01-22T10:30:00Z",
                    "requires_consent": True,
                    "risk_assessment": "medium",
                    "therapeutic_value": 0.85,
                },
                {
                    "memory_id": "mem_pending_2",
                    "content": "Call me at 555-0123 to schedule next session.",
                    "timestamp": "2024-01-16T14:15:00Z",
                    "pii_detected": ["PHONE_NUMBER"],
                    "consent_deadline": "2024-01-23T14:15:00Z",
                    "requires_consent": True,
                    "risk_assessment": "high",
                    "therapeutic_value": 0.45,
                },
            ],
            "total_pending": 2,
            "summary": {
                "high_risk_items": 1,
                "medium_risk_items": 1,
                "low_risk_items": 0,
                "average_therapeutic_value": 0.65,
                "oldest_pending": "2024-01-15T10:30:00Z",
            },
            "consent_options": {
                "bulk_actions": ["approve_all", "deny_all", "anonymize_all"],
                "individual_review": "recommended for items with high therapeutic value",
            },
        }

        with patch(
            "api.memory.memory_service.get_pending_consent_memories"
        ) as mock_pending:
            mock_pending.return_value = mock_pending_memories

            response = test_client.get(f"/api/memory/pending-consent?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "pending_memories" in data
            assert data["total_pending"] == 2
            assert len(data["pending_memories"]) == 2
            assert data["summary"]["high_risk_items"] == 1
            assert "bulk_actions" in data["consent_options"]

    def test_process_pending_consent_bulk(self, test_client):
        """Test bulk processing of pending consent memories."""
        user_id = "test-user-123"
        bulk_choices = {
            "memory_choices": {
                "mem_pending_1": {
                    "action": "approve",
                    "pii_handling": {
                        "pii_item_1": {"action": "anonymize"},
                        "pii_item_2": {"action": "remove"},
                    },
                },
                "mem_pending_2": {"action": "deny", "reason": "Low therapeutic value"},
                "mem_pending_3": {
                    "action": "approve",
                    "pii_handling": {"pii_item_1": {"action": "keep"}},
                },
            },
            "bulk_settings": {
                "apply_same_pii_choices": False,
                "notify_on_completion": True,
            },
        }

        mock_bulk_result = {
            "processed": 3,
            "approved": 2,
            "denied": 1,
            "errors": [],
            "results": [
                {
                    "memory_id": "mem_pending_1",
                    "status": "approved_with_modifications",
                    "stored": True,
                    "storage_type": "long_term",
                    "pii_modifications": "anonymized_and_removed",
                },
                {
                    "memory_id": "mem_pending_2",
                    "status": "denied",
                    "stored": False,
                    "reason": "User denied consent",
                },
                {
                    "memory_id": "mem_pending_3",
                    "status": "approved_as_is",
                    "stored": True,
                    "storage_type": "long_term",
                    "pii_modifications": "none",
                },
            ],
            "summary": {
                "total_memories_processed": 3,
                "memories_stored": 2,
                "memories_rejected": 1,
                "pii_items_processed": 4,
                "pii_items_anonymized": 1,
                "pii_items_removed": 1,
                "pii_items_kept": 1,
            },
        }

        with patch("api.memory.memory_service.process_pending_consent") as mock_process:
            mock_process.return_value = mock_bulk_result

            response = test_client.post(
                f"/api/memory/apply-privacy-choices?user_id={user_id}",
                json=bulk_choices,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["processed"] == 3
            assert data["approved"] == 2
            assert data["denied"] == 1
            assert len(data["results"]) == 3
            assert data["summary"]["memories_stored"] == 2

    def test_revoke_consent_after_storage(self, test_client):
        """Test revoking consent for already stored memories."""
        user_id = "test-user-123"
        revocation_request = {
            "memory_ids": ["mem_stored_1", "mem_stored_2"],
            "revocation_reason": "Changed my mind about data sharing",
            "requested_action": "anonymize_or_delete",
        }

        mock_revocation_result = {
            "processed": 2,
            "anonymized": 1,
            "failed": 1,
            "results": [
                {
                    "memory_id": "mem_stored_1",
                    "status": "anonymized",
                    "anonymized_content": "My therapist [THERAPIST] helped me understand [TOPIC].",
                },
                {
                    "memory_id": "mem_stored_2",
                    "status": "error",
                    "error": "Contained only PII with no therapeutic value",
                },
            ],
            "gdpr_compliance": {
                "right_exercised": "rectification_and_erasure",
            },
        }

        with patch("api.memory.memory_service.anonymize_memories") as mock_revoke:
            mock_revoke.return_value = mock_revocation_result

            response = test_client.post(
                f"/api/memory/revoke-consent?user_id={user_id}", json=revocation_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            print("Actual API response:", data)

            assert data["processed"] == 2
            assert data["modified"] == 1
            assert data["deleted"] == 1
            assert len(data["results"]) == 2
            assert (
                data["gdpr_compliance"]["right_exercised"]
                == "rectification_and_erasure"
            )


class TestConsentValidation:
    """Test suite for consent validation and error handling."""

    def test_invalid_consent_choices(self, test_client):
        """Test handling of invalid consent choices."""
        user_id = "test-user-123"
        invalid_request = {
            "content": "Test content",
            "type": "chat",
            "user_consent": {
                "invalid_pii_item": {
                    "action": "invalid_action"  # Should be keep/anonymize/remove
                }
            },
        }

        # Mock the service to raise a validation error for invalid consent
        with patch("api.memory.memory_service.process_memory") as mock_process:
            mock_process.side_effect = ValueError(
                "Invalid consent action: invalid_action. Must be one of: keep, anonymize, remove"
            )

            response = test_client.post(
                f"/api/memory/?user_id={user_id}", json=invalid_request
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Invalid consent action" in response.text

    def test_consent_timeout_handling(self, test_client):
        """Test handling of consent requests that timeout."""
        user_id = "test-user-123"

        mock_timeout_response = {
            "expired_consents": [
                {
                    "memory_id": "mem_expired_1",
                    "original_request_time": "2024-01-15T10:00:00Z",
                    "expiration_time": "2024-01-22T10:00:00Z",
                    "current_time": "2024-01-23T10:00:00Z",
                    "default_action": "deleted",
                    "reason": "No consent provided within 7 days",
                }
            ],
            "total_expired": 1,
            "policy": {
                "consent_timeout_days": 7,
                "default_action_on_timeout": "delete",
                "user_notification": "required",
            },
        }

        with patch(
            "api.memory.memory_service.get_expired_consent_requests"
        ) as mock_expired:
            mock_expired.return_value = mock_timeout_response

            response = test_client.get(
                f"/api/memory/expired-consents?user_id={user_id}"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "expired_consents" in data
            assert data["total_expired"] == 1
            assert data["policy"]["consent_timeout_days"] == 7

    def test_consent_audit_trail(self, test_client):
        """Test consent decision audit trail retrieval."""
        user_id = "test-user-123"

        mock_audit_trail = {
            "consent_history": [
                {
                    "timestamp": "2024-01-20T15:30:00Z",
                    "memory_id": "mem_123",
                    "action": "consent_granted",
                    "details": {
                        "pii_items": 2,
                        "anonymized": 1,
                        "removed": 0,
                        "kept": 1,
                    },
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.100",
                },
                {
                    "timestamp": "2024-01-21T09:15:00Z",
                    "memory_id": "mem_124",
                    "action": "consent_denied",
                    "details": {
                        "reason": "Too much PII",
                        "alternative_offered": "anonymized_version",
                    },
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.100",
                },
            ],
            "summary": {
                "total_consent_decisions": 2,
                "granted": 1,
                "denied": 1,
                "revoked": 0,
                "date_range": {
                    "earliest": "2024-01-20T15:30:00Z",
                    "latest": "2024-01-21T09:15:00Z",
                },
            },
            "gdpr_compliance": {
                "audit_retention_period": "7 years",
                "data_subject_access": "granted",
                "audit_integrity": "verified",
            },
        }

        with patch("api.memory.memory_service.get_consent_audit_trail") as mock_audit:
            mock_audit.return_value = mock_audit_trail

            response = test_client.get(f"/api/memory/consent-history?user_id={user_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "consent_history" in data
            assert len(data["consent_history"]) == 2
            assert data["summary"]["total_consent_decisions"] == 2
            assert data["gdpr_compliance"]["audit_retention_period"] == "7 years"


class TestConsentUISupport:
    """Test suite for supporting consent UI/UX."""

    def test_consent_preview_before_decision(self, test_client):
        """Test previewing how content will look with different consent choices."""
        user_id = "test-user-123"
        preview_request = {
            "content": "My therapist Dr. Sarah at 123 Main St helped me with anxiety about my job at TechCorp.",
            "preview_options": {
                "option_1": {
                    "Dr. Sarah": "anonymize",
                    "123 Main St": "remove",
                    "TechCorp": "keep",
                },
                "option_2": {
                    "Dr. Sarah": "remove",
                    "123 Main St": "remove",
                    "TechCorp": "anonymize",
                },
                "option_3": {
                    "Dr. Sarah": "keep",
                    "123 Main St": "keep",
                    "TechCorp": "keep",
                },
            },
        }

        mock_preview_result = {
            "previews": {
                "option_1": {
                    "content": "My therapist [THERAPIST] helped me with anxiety about my job at TechCorp.",
                    "therapeutic_value_impact": 0.85,
                    "privacy_score": 0.75,
                    "recommendation": "balanced_approach",
                },
                "option_2": {
                    "content": "My therapist helped me with anxiety about my job at [COMPANY].",
                    "therapeutic_value_impact": 0.70,
                    "privacy_score": 0.95,
                    "recommendation": "privacy_focused",
                },
                "option_3": {
                    "content": "My therapist Dr. Sarah at 123 Main St helped me with anxiety about my job at TechCorp.",
                    "therapeutic_value_impact": 0.95,
                    "privacy_score": 0.30,
                    "recommendation": "therapeutic_focused",
                },
            },
            "analysis": {
                "pii_items_detected": 3,
                "therapeutic_terms": ["therapist", "anxiety", "job"],
                "privacy_considerations": "Address has high risk, name has medium risk",
                "recommendation": "option_1 provides best balance",
            },
        }

        with patch("api.memory.memory_service.preview_consent_choices") as mock_preview:
            mock_preview.return_value = mock_preview_result

            response = test_client.post(
                f"/api/memory/consent-preview?user_id={user_id}", json=preview_request
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "previews" in data
            assert len(data["previews"]) == 3
            assert data["previews"]["option_1"]["recommendation"] == "balanced_approach"
            assert data["analysis"]["pii_items_detected"] == 3

    def test_consent_recommendations(self, test_client):
        """Test simplified consent recommendations based on privacy level only."""
        user_id = "test-user-123"
        recommendation_request = {
            "content": "Dr. Jane Smith at Psychology Associates (555-0123) prescribed new medication.",
            "user_preferences": {
                "privacy_level": "medium",
                "therapeutic_priority": "high",
            },
        }

        mock_recommendations = {
            "recommended_choices": {
                "Dr. Jane Smith": {
                    "action": "anonymize",
                    "confidence": 0.80,
                    "reasoning": "Medium privacy + high risk: anonymizing person",
                },
                "Psychology Associates": {
                    "action": "keep",
                    "confidence": 0.80,
                    "reasoning": "Medium privacy + lower risk: keeping organization",
                },
                "(555-0123)": {
                    "action": "anonymize",
                    "confidence": 0.80,
                    "reasoning": "Medium privacy + high risk: anonymizing phone number",
                },
            },
            "overall_assessment": {
                "privacy_score": 0.70,
                "therapeutic_value_retention": 0.80,
                "recommendation_confidence": "medium",
            },
            "alternative_suggestion": {
                "description": "Adjust your privacy level in settings for different default recommendations",
                "impact": "Higher privacy = more anonymization, Lower privacy = more context retention",
            },
        }

        with patch(
            "api.memory.memory_service.get_consent_recommendations"
        ) as mock_recommend:
            mock_recommend.return_value = mock_recommendations

            response = test_client.post(
                f"/api/memory/consent-recommendations?user_id={user_id}",
                json=recommendation_request,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "recommended_choices" in data
            assert "Dr. Jane Smith" in data["recommended_choices"]
            assert (
                data["recommended_choices"]["Dr. Jane Smith"]["action"] == "anonymize"
            )
            assert data["overall_assessment"]["recommendation_confidence"] == "medium"
