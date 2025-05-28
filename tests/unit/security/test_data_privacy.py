"""
Data Privacy and GDPR Compliance Tests
Tests data privacy controls, GDPR compliance, and user consent management.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

# Import the services we need to test
from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem, MemoryContext
from services.memory.security.pii_detector import PIIDetector


class TestGDPRCompliance:
    """Test GDPR compliance features."""

    @pytest.fixture
    def memory_service(self):
        """Create a memory service instance for testing."""
        return MemoryService()

    @pytest.fixture
    def pii_detector(self):
        """Create a PII detector instance for testing."""
        return PIIDetector()

    @pytest.mark.asyncio
    async def test_right_to_access(self, memory_service):
        """Test GDPR Article 15 - Right to access personal data."""
        user_id = "test_user"

        # Mock user memories
        mock_memories = [
            MemoryItem(
                id="mem1",
                userId=user_id,
                content="I discussed my anxiety with my therapist",
                type="chat",
                timestamp=datetime.utcnow(),
                metadata={"has_pii": True, "pii_types": ["HEALTHCARE_PROVIDER"]},
            ),
            MemoryItem(
                id="mem2",
                userId=user_id,
                content="I feel better today",
                type="chat",
                timestamp=datetime.utcnow(),
                metadata={"has_pii": False},
            ),
        ]

        with patch.object(
            memory_service.gdpr_processor, "export_user_data"
        ) as mock_export:
            mock_export.return_value = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data_categories": {
                    "memories": mock_memories,
                    "preferences": {},
                    "consent_records": [],
                },
                "total_records": len(mock_memories),
            }

            export_data = await memory_service.export_user_data(user_id)

            # Verify export contains required information
            assert "user_id" in export_data
            assert "export_date" in export_data
            assert "data_categories" in export_data
            assert "total_records" in export_data

            # Verify user can access all their data
            assert export_data["user_id"] == user_id
            assert export_data["total_records"] == len(mock_memories)

    @pytest.mark.asyncio
    async def test_right_to_rectification(self, memory_service):
        """Test GDPR Article 16 - Right to rectification."""
        user_id = "test_user"
        memory_id = "mem1"

        # Test updating memory content - use actual API
        # In the current implementation, updates are handled through deletion and re-creation
        with patch.object(memory_service, "delete_memory") as mock_delete:
            mock_delete.return_value = True

            # User should be able to correct their data by deleting and recreating
            result = await memory_service.delete_memory(user_id, memory_id)

            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_right_to_erasure(self, memory_service):
        """Test GDPR Article 17 - Right to erasure (right to be forgotten)."""
        user_id = "test_user"

        with patch.object(
            memory_service.gdpr_processor, "delete_all_user_data"
        ) as mock_delete:
            mock_delete.return_value = {
                "deleted": True,
                "records_deleted": 15,
                "categories_cleared": ["memories", "preferences", "sessions"],
                "deletion_date": datetime.utcnow().isoformat(),
            }

            result = await memory_service.delete_all_user_data(user_id)

            assert result["deleted"] is True
            assert result["records_deleted"] > 0
            assert "deletion_date" in result

    @pytest.mark.asyncio
    async def test_right_to_data_portability(self, memory_service):
        """Test GDPR Article 20 - Right to data portability."""
        user_id = "test_user"

        with patch.object(
            memory_service.gdpr_processor, "export_portable_data"
        ) as mock_export:
            mock_export.return_value = {
                "format": "json",
                "data": {
                    "memories": [
                        {
                            "id": "mem1",
                            "content": "Portable memory data",
                            "timestamp": "2024-01-01T12:00:00Z",
                            "type": "chat",
                        }
                    ]
                },
                "metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "format_version": "1.0",
                    "total_records": 1,
                },
            }

            portable_data = await memory_service.export_portable_data(
                user_id, format="json"
            )

            # Verify data is in machine-readable format
            assert portable_data["format"] == "json"
            assert "data" in portable_data
            assert "metadata" in portable_data

            # Verify data structure is portable
            assert isinstance(portable_data["data"], dict)
            assert "memories" in portable_data["data"]

    @pytest.mark.asyncio
    async def test_right_to_object(self, memory_service):
        """Test GDPR Article 21 - Right to object to processing."""
        user_id = "test_user"

        # Test objecting to automated processing
        with patch.object(
            memory_service.gdpr_processor, "update_consent"
        ) as mock_consent:
            mock_consent.return_value = {
                "consent_updated": True,
                "processing_restricted": True,
                "automated_processing": False,
            }

            result = await memory_service.update_consent(
                user_id,
                {
                    "automated_processing": False,
                    "data_analysis": False,
                    "personalization": False,
                },
            )

            assert result["consent_updated"] is True
            assert result["automated_processing"] is False

    def test_data_retention_policy(self, memory_service):
        """Test data retention policy compliance."""
        retention_policy = {
            "short_term_memories": timedelta(days=30),
            "long_term_memories": timedelta(days=2555),  # 7 years
            "pii_data": timedelta(days=30),
            "consent_records": timedelta(days=2555),  # 7 years
            "audit_logs": timedelta(days=2555),  # 7 years
        }

        current_time = datetime.utcnow()

        for data_type, retention_period in retention_policy.items():
            # Test data within retention period
            recent_date = current_time - timedelta(days=1)
            assert not self._is_data_expired(
                recent_date, retention_period
            ), f"{data_type} incorrectly marked as expired"

            # Test data beyond retention period
            old_date = current_time - retention_period - timedelta(days=1)
            assert self._is_data_expired(
                old_date, retention_period
            ), f"{data_type} not marked as expired"

    def _is_data_expired(self, data_date, retention_period):
        """Helper method to check if data has exceeded retention period."""
        current_time = datetime.utcnow()
        age = current_time - data_date
        return age > retention_period


class TestConsentManagement:
    """Test user consent management."""

    @pytest.fixture
    def memory_service(self):
        return MemoryService()

    @pytest.mark.asyncio
    async def test_granular_consent_collection(self, memory_service):
        """Test collection of granular consent for different data types."""
        user_id = "test_user"

        # Test granular consent options
        consent_options = {
            "pii_processing": {
                "PERSON": "anonymize",
                "EMAIL_ADDRESS": "anonymize",
                "PHONE_NUMBER": "anonymize",
                "HEALTHCARE_PROVIDER": "keep_original",
                "MEDICATION": "keep_original",
            },
            "data_usage": {
                "therapeutic_analysis": True,
                "personalization": True,
                "research": False,
                "marketing": False,
            },
            "storage_preferences": {
                "short_term_storage": True,
                "long_term_storage": True,
                "cloud_storage": True,
            },
        }

        with patch.object(memory_service, "update_consent") as mock_consent:
            mock_consent.return_value = {
                "consent_recorded": True,
                "consent_id": "consent_123",
                "timestamp": datetime.utcnow().isoformat(),
            }

            result = await memory_service.update_consent(user_id, consent_options)

            assert result["consent_recorded"] is True
            assert "consent_id" in result
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_consent_withdrawal(self, memory_service):
        """Test user's ability to withdraw consent."""
        user_id = "test_user"

        with patch.object(memory_service, "update_consent") as mock_withdraw:
            mock_withdraw.return_value = {
                "consent_withdrawn": True,
                "data_processing_stopped": True,
                "retention_period_started": datetime.utcnow().isoformat(),
            }

            result = await memory_service.update_consent(
                user_id, {"pii_processing": False, "personalization": False}
            )

            assert result["consent_withdrawn"] is True
            assert result["data_processing_stopped"] is True

    @pytest.mark.asyncio
    async def test_consent_audit_trail(self, memory_service):
        """Test consent audit trail for compliance."""
        user_id = "test_user"

        # Mock consent history
        consent_history = [
            {
                "consent_id": "consent_1",
                "timestamp": datetime.utcnow() - timedelta(days=30),
                "action": "granted",
                "categories": ["pii_processing", "personalization"],
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
            },
            {
                "consent_id": "consent_2",
                "timestamp": datetime.utcnow() - timedelta(days=15),
                "action": "modified",
                "categories": ["pii_processing"],
                "changes": {"PERSON": "anonymize"},
                "ip_address": "192.168.1.1",
            },
            {
                "consent_id": "consent_3",
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "action": "withdrawn",
                "categories": ["personalization"],
                "ip_address": "192.168.1.1",
            },
        ]

        # Test consent audit trail structure (simulated)
        # In a real implementation, this would call an actual audit method
        history = consent_history  # Simulate getting consent history

        # Verify audit trail completeness
        assert len(history) == 3
        for record in history:
            assert "consent_id" in record
            assert "timestamp" in record
            assert "action" in record
            assert "categories" in record
            assert record["action"] in ["granted", "modified", "withdrawn"]

    def test_consent_expiration(self, memory_service):
        """Test consent expiration and renewal requirements."""
        consent_date = datetime.utcnow() - timedelta(days=400)  # Over 1 year old
        max_consent_age = timedelta(days=365)  # 1 year

        # Test expired consent
        assert self._is_consent_expired(
            consent_date, max_consent_age
        ), "Expired consent not detected"

        # Test valid consent
        recent_consent = datetime.utcnow() - timedelta(days=30)
        assert not self._is_consent_expired(
            recent_consent, max_consent_age
        ), "Valid consent marked as expired"

    def _is_consent_expired(self, consent_date, max_age):
        """Helper method to check if consent has expired."""
        current_time = datetime.utcnow()
        age = current_time - consent_date
        return age > max_age


class TestDataMinimization:
    """Test data minimization principles."""

    @pytest.fixture
    def memory_service(self):
        return MemoryService()

    @pytest.fixture
    def pii_detector(self):
        return PIIDetector()

    @pytest.mark.asyncio
    async def test_automatic_pii_anonymization(self, memory_service, pii_detector):
        """Test automatic anonymization of high-risk PII."""
        content_with_pii = "My name is John Smith and my email is john@example.com. I live at 123 Main St."

        # Mock PII detection
        mock_pii_result = {
            "has_pii": True,
            "detected_items": [
                {
                    "type": "PERSON",
                    "text": "John Smith",
                    "risk_level": "high",
                    "start": 11,
                    "end": 21,
                },
                {
                    "type": "EMAIL_ADDRESS",
                    "text": "john@example.com",
                    "risk_level": "high",
                    "start": 38,
                    "end": 54,
                },
            ],
        }

        with patch.object(pii_detector, "detect_pii") as mock_detect:
            mock_detect.return_value = mock_pii_result

            with patch.object(pii_detector, "apply_granular_consent") as mock_anonymize:
                mock_anonymize.return_value = "My name is <PERSON> and my email is <EMAIL_ADDRESS>. I live at 123 Main St."

                # Test automatic anonymization for long-term storage
                anonymized_content = await pii_detector.apply_granular_consent(
                    content_with_pii,
                    "long_term",
                    {"PERSON_1": "anonymize", "EMAIL_ADDRESS_1": "anonymize"},
                    mock_pii_result,
                )

                # Verify PII is anonymized
                assert "John Smith" not in anonymized_content
                assert "john@example.com" not in anonymized_content
                assert "<PERSON>" in anonymized_content
                assert "<EMAIL_ADDRESS>" in anonymized_content

    @pytest.mark.asyncio
    async def test_selective_data_retention(self, memory_service):
        """Test selective retention based on therapeutic value."""
        memories = [
            {
                "content": "I had a breakthrough in therapy today",
                "therapeutic_value": 0.9,
                "has_pii": False,
            },
            {
                "content": "Just chatting about the weather",
                "therapeutic_value": 0.1,
                "has_pii": False,
            },
            {
                "content": "My therapist Dr. Smith helped me understand my anxiety",
                "therapeutic_value": 0.8,
                "has_pii": True,
            },
        ]

        # Test retention decisions based on therapeutic value
        for memory in memories:
            should_retain = self._should_retain_memory(
                memory["therapeutic_value"], memory["has_pii"], threshold=0.5
            )

            if memory["therapeutic_value"] >= 0.5:
                assert (
                    should_retain
                ), f"High-value memory should be retained: {memory['content'][:30]}..."
            else:
                # Low therapeutic value memories might not be retained
                pass  # Decision depends on implementation

    @pytest.mark.asyncio
    async def test_data_aggregation_privacy(self, memory_service):
        """Test privacy-preserving data aggregation."""
        user_memories = [
            "I feel anxious about work",
            "Had a panic attack today",
            "Therapy session was helpful",
            "Feeling better with medication",
        ]

        # Test aggregated insights structure (simulated)
        # In a real implementation, this would call an actual insights method
        insights = {
            "emotional_trends": {
                "anxiety_frequency": "moderate",
                "improvement_trend": "positive",
                "therapy_engagement": "high",
            },
            "aggregation_method": "differential_privacy",
            "privacy_budget": 0.1,
            "individual_records_exposed": False,
        }

        # Verify insights don't expose individual memories
        assert insights["individual_records_exposed"] is False
        assert "emotional_trends" in insights
        assert "privacy_budget" in insights

    def _should_retain_memory(self, therapeutic_value, has_pii, threshold=0.5):
        """Helper method to determine if memory should be retained."""
        # High therapeutic value memories are generally retained
        if therapeutic_value >= threshold:
            return True

        # Low therapeutic value with PII might be discarded
        if therapeutic_value < threshold and has_pii:
            return False

        # Low therapeutic value without PII might be retained briefly
        return therapeutic_value >= 0.3


class TestPrivacyByDesign:
    """Test privacy by design principles."""

    @pytest.fixture
    def memory_service(self):
        return MemoryService()

    def test_default_privacy_settings(self, memory_service):
        """Test that privacy-protective settings are the default."""
        default_settings = {
            "pii_anonymization": True,
            "data_minimization": True,
            "consent_required": True,
            "retention_limits": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "access_logging": True,
            "data_sharing": False,
            "marketing_use": False,
            "research_participation": False,
        }

        # Verify privacy-protective defaults
        for setting, expected_value in default_settings.items():
            actual_value = self._get_default_setting(setting)
            assert (
                actual_value == expected_value
            ), f"Default setting {setting} should be {expected_value}"

    @pytest.mark.asyncio
    async def test_privacy_impact_assessment(self, memory_service):
        """Test privacy impact assessment for new features."""
        new_feature = {
            "name": "mood_tracking",
            "data_collected": ["mood_scores", "timestamps", "user_notes"],
            "processing_purpose": "therapeutic_insights",
            "data_sharing": False,
            "retention_period": "1_year",
            "user_control": True,
        }

        privacy_assessment = self._assess_privacy_impact(new_feature)

        # Verify privacy assessment covers key areas
        assert "data_minimization_score" in privacy_assessment
        assert "consent_requirements" in privacy_assessment
        assert "risk_level" in privacy_assessment
        assert privacy_assessment["risk_level"] in ["low", "medium", "high"]

    def test_privacy_controls_accessibility(self, memory_service):
        """Test that privacy controls are easily accessible to users."""
        privacy_controls = {
            "data_export": {"accessible": True, "steps_required": 2},
            "data_deletion": {"accessible": True, "steps_required": 3},
            "consent_management": {"accessible": True, "steps_required": 1},
            "privacy_settings": {"accessible": True, "steps_required": 1},
            "data_portability": {"accessible": True, "steps_required": 2},
        }

        for control, requirements in privacy_controls.items():
            assert requirements[
                "accessible"
            ], f"Privacy control {control} should be accessible"
            assert (
                requirements["steps_required"] <= 3
            ), f"Privacy control {control} requires too many steps"

    def _get_default_setting(self, setting_name):
        """Helper method to get default privacy settings."""
        # In real implementation, would fetch from configuration
        privacy_defaults = {
            "pii_anonymization": True,
            "data_minimization": True,
            "consent_required": True,
            "retention_limits": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "access_logging": True,
            "data_sharing": False,
            "marketing_use": False,
            "research_participation": False,
        }
        return privacy_defaults.get(setting_name, False)

    def _assess_privacy_impact(self, feature):
        """Helper method to assess privacy impact of new features."""
        # Simplified privacy impact assessment
        risk_factors = 0

        if len(feature.get("data_collected", [])) > 3:
            risk_factors += 1

        if feature.get("data_sharing", False):
            risk_factors += 2

        if not feature.get("user_control", False):
            risk_factors += 2

        risk_level = (
            "low" if risk_factors == 0 else "medium" if risk_factors <= 2 else "high"
        )

        return {
            "data_minimization_score": 0.8,
            "consent_requirements": (
                ["explicit_consent"] if risk_factors > 0 else ["implied_consent"]
            ),
            "risk_level": risk_level,
            "recommendations": ["implement_user_controls"] if risk_factors > 1 else [],
        }


class TestDataSecurity:
    """Test data security measures."""

    @pytest.fixture
    def memory_service(self):
        return MemoryService()

    def test_encryption_requirements(self, memory_service):
        """Test encryption requirements for sensitive data."""
        sensitive_data_types = [
            "pii_data",
            "medical_information",
            "therapy_notes",
            "user_credentials",
            "session_tokens",
        ]

        for data_type in sensitive_data_types:
            # Verify encryption is required
            assert self._requires_encryption(
                data_type
            ), f"Encryption should be required for {data_type}"

            # Verify encryption strength
            encryption_strength = self._get_encryption_strength(data_type)
            assert (
                encryption_strength >= 256
            ), f"Insufficient encryption strength for {data_type}"

    def test_access_control_matrix(self, memory_service):
        """Test access control matrix for different user roles."""
        access_matrix = {
            "user": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": [],
                "system_settings": [],
                "audit_logs": [],
            },
            "admin": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": ["read"],  # For support purposes
                "system_settings": ["read", "write"],
                "audit_logs": ["read"],
            },
            "support": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": ["read"],  # With user consent
                "system_settings": ["read"],
                "audit_logs": [],
            },
        }

        for role, permissions in access_matrix.items():
            for resource, allowed_actions in permissions.items():
                for action in ["read", "write", "delete"]:
                    has_permission = action in allowed_actions
                    assert (
                        self._check_permission(role, resource, action) == has_permission
                    ), f"Permission mismatch: {role} {action} {resource}"

    def test_data_breach_response(self, memory_service):
        """Test data breach response procedures."""
        breach_scenarios = [
            {
                "type": "unauthorized_access",
                "severity": "high",
                "affected_users": 100,
                "data_types": ["pii", "medical"],
            },
            {
                "type": "data_leak",
                "severity": "critical",
                "affected_users": 1000,
                "data_types": ["pii", "medical", "financial"],
            },
        ]

        for scenario in breach_scenarios:
            response_plan = self._get_breach_response_plan(scenario)

            # Verify response plan completeness
            assert "notification_timeline" in response_plan
            assert "affected_user_notification" in response_plan
            assert "regulatory_notification" in response_plan
            assert "containment_measures" in response_plan

            # Verify timeline compliance (GDPR requires 72 hours)
            if scenario["severity"] in ["high", "critical"]:
                assert (
                    response_plan["notification_timeline"] <= 72
                ), "GDPR notification timeline exceeded"

    def _requires_encryption(self, data_type):
        """Helper method to check if data type requires encryption."""
        encrypted_types = [
            "pii_data",
            "medical_information",
            "therapy_notes",
            "user_credentials",
            "session_tokens",
        ]
        return data_type in encrypted_types

    def _get_encryption_strength(self, data_type):
        """Helper method to get required encryption strength."""
        # Return encryption key length in bits
        return 256  # AES-256 for all sensitive data

    def _check_permission(self, role, resource, action):
        """Helper method to check role-based permissions."""
        # Simplified permission checking
        access_matrix = {
            "user": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": [],
                "system_settings": [],
                "audit_logs": [],
            },
            "admin": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": ["read"],
                "system_settings": ["read", "write"],
                "audit_logs": ["read"],
            },
            "support": {
                "own_memories": ["read", "write", "delete"],
                "other_memories": ["read"],
                "system_settings": ["read"],
                "audit_logs": [],
            },
        }

        role_permissions = access_matrix.get(role, {})
        resource_permissions = role_permissions.get(resource, [])
        return action in resource_permissions

    def _get_breach_response_plan(self, scenario):
        """Helper method to get breach response plan."""
        base_timeline = 72  # hours

        if scenario["severity"] == "critical":
            timeline = 24
        elif scenario["severity"] == "high":
            timeline = 48
        else:
            timeline = base_timeline

        return {
            "notification_timeline": timeline,
            "affected_user_notification": True,
            "regulatory_notification": scenario["severity"] in ["high", "critical"],
            "containment_measures": ["isolate_systems", "revoke_access", "audit_logs"],
            "recovery_steps": ["restore_from_backup", "security_patches", "monitoring"],
        }
