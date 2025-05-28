"""
Unit tests for PII Detector service.
Tests PII detection, risk classification, and anonymization functionality.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from services.memory.security.pii_detector import PIIDetector
from services.memory.types import MemoryItem


class TestPIIDetector:
    """Test suite for PII detection functionality."""

    @pytest.fixture
    def pii_detector(self):
        """Create a PII detector instance for testing."""
        return PIIDetector()

    @pytest.fixture
    def sample_memory_item(self):
        """Create a sample memory item for testing."""
        return MemoryItem(
            id="test-memory-1",
            userId="test-user-123",
            content="Test content",
            type="conversation",
            metadata={},
            timestamp=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_detect_pii_with_high_risk_content(
        self, pii_detector, sample_memory_item
    ):
        """Test PII detection with high-risk content (names, emails, phones)."""
        sample_memory_item.content = "My name is John Doe and my email is john.doe@example.com. My phone is 555-123-4567."

        result = await pii_detector.detect_pii(sample_memory_item)

        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "high"
        assert len(result["detected_items"]) > 0

        # Should detect multiple types of PII
        pii_types = [item["type"] for item in result["detected_items"]]
        assert "PERSON" in pii_types or "EMAIL_ADDRESS" in pii_types

    @pytest.mark.asyncio
    async def test_detect_pii_with_medium_risk_content(self, pii_detector):
        """Test PII detection with medium-risk content (medical info)."""
        content = "I was diagnosed with depression at Mayo Clinic last year."

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk in [
            "medium",
            "high",
        ]  # Could be classified as either
        assert len(result["detected_items"]) > 0

    @pytest.mark.asyncio
    async def test_detect_pii_with_low_risk_content(self, pii_detector):
        """Test PII detection with low-risk content (therapy types)."""
        content = "I'm doing cognitive behavioral therapy and it's helping."

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        # This might or might not be detected as PII depending on configuration
        assert "has_pii" in result
        assert "detected_items" in result

    @pytest.mark.asyncio
    async def test_detect_pii_with_no_pii_content(self, pii_detector):
        """Test PII detection with content containing no PII."""
        content = "I feel anxious about my upcoming presentation. Any advice?"

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is False
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "low"
        assert len(result["detected_items"]) == 0

    @pytest.mark.asyncio
    async def test_detect_pii_with_healthcare_providers(self, pii_detector):
        """Test detection of healthcare provider names."""
        content = "I see Dr. Smith at Johns Hopkins for my therapy sessions."

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk in ["high", "medium"]

        # Should detect person name and potentially organization
        pii_types = [item["type"] for item in result["detected_items"]]
        assert "PERSON" in pii_types

    @pytest.mark.asyncio
    async def test_detect_pii_with_addresses(self, pii_detector):
        """Test detection of addresses."""
        content = "I live at 123 Main Street, New York, NY 10001."

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "high"

        # Should detect location information
        detected_text = " ".join([item["text"] for item in result["detected_items"]])
        assert any(
            addr in detected_text.lower()
            for addr in ["main street", "new york", "10001"]
        )

    @pytest.mark.asyncio
    async def test_detect_pii_confidence_scoring(self, pii_detector):
        """Test that PII detection includes confidence scores."""
        content = "My name is definitely John Smith and my email is john@example.com."

        # Create a MemoryItem for testing
        from datetime import datetime
        import uuid
        from backend.services.memory.types import MemoryItem

        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is True
        assert len(result["detected_items"]) > 0

        # All detected items should have confidence scores
        for item in result["detected_items"]:
            assert "confidence" in item
            assert 0.0 <= item["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_detect_pii_with_phone_numbers(self, pii_detector):
        """Test detection of various phone number formats."""
        test_cases = [
            "Call me at 555-123-4567",
            "My number is (555) 123-4567",
            "Reach me at 555.123.4567",
            "Phone: +1-555-123-4567",
        ]

        for content in test_cases:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            assert result["has_pii"] is True, f"Failed to detect phone in: {content}"
            # Calculate overall risk level
            risk_levels = [item["risk_level"] for item in result["detected_items"]]
            overall_risk = (
                "high"
                if "high" in risk_levels
                else ("medium" if "medium" in risk_levels else "low")
            )
            assert overall_risk == "high"

            # Should detect phone number
            pii_types = [item["type"] for item in result["detected_items"]]
            assert "PHONE_NUMBER" in pii_types

    @pytest.mark.asyncio
    async def test_detect_pii_with_email_addresses(self, pii_detector):
        """Test detection of various email formats."""
        test_cases = [
            "Contact me at john.doe@example.com",
            "My email is jane_smith@company.org",
            "Send to: user123@domain.net",
        ]

        for content in test_cases:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            assert result["has_pii"] is True, f"Failed to detect email in: {content}"
            # Calculate overall risk level
            risk_levels = [item["risk_level"] for item in result["detected_items"]]
            overall_risk = (
                "high"
                if "high" in risk_levels
                else ("medium" if "medium" in risk_levels else "low")
            )
            assert overall_risk == "high"

            # Should detect email address
            pii_types = [item["type"] for item in result["detected_items"]]
            assert "EMAIL_ADDRESS" in pii_types

    @pytest.mark.asyncio
    async def test_detect_pii_risk_level_classification(self, pii_detector):
        """Test that risk levels are classified correctly."""
        test_cases = [
            ("My name is John", "high"),  # Names are high risk
            ("Call 911 for emergency", "low"),  # Emergency numbers are low risk
            ("I go to therapy", "low"),  # General therapy mention is low risk
            ("john@example.com", "high"),  # Email is high risk
        ]

        for content, expected_risk in test_cases:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            if result["has_pii"]:
                # Calculate overall risk level
                risk_levels = [item["risk_level"] for item in result["detected_items"]]
                overall_risk = (
                    "high"
                    if "high" in risk_levels
                    else ("medium" if "medium" in risk_levels else "low")
                )
                assert overall_risk == expected_risk, f"Wrong risk level for: {content}"

    @pytest.mark.asyncio
    async def test_detect_pii_empty_content(self, pii_detector):
        """Test PII detection with empty content."""
        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content="",
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is False
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "low"
        assert len(result["detected_items"]) == 0

    @pytest.mark.asyncio
    async def test_detect_pii_very_long_content(self, pii_detector):
        """Test PII detection with very long content."""
        # Create long content with PII embedded
        long_content = "This is a very long message. " * 100
        long_content += "My name is John Doe and my email is john@example.com."
        long_content += " More text here. " * 50

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=long_content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "high"
        assert len(result["detected_items"]) > 0

    @pytest.mark.asyncio
    async def test_detect_pii_special_characters(self, pii_detector):
        """Test PII detection with special characters and encoding."""
        content = "My name is José García and my email is josé@example.com"

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        # Should handle special characters correctly
        assert result["has_pii"] is True
        # Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else ("medium" if "medium" in risk_levels else "low")
        )
        assert overall_risk == "high"

    @pytest.mark.asyncio
    async def test_detect_pii_false_positives(self, pii_detector):
        """Test that common false positives are handled correctly."""
        false_positive_cases = [
            "I love New York pizza",  # Location names in context
            "Call me maybe",  # "Call me" without actual number
            "My therapist says",  # Generic therapist mention
            "Dr. Pepper is my favorite drink",  # Dr. title in non-medical context
        ]

        for content in false_positive_cases:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            # These should either not detect PII or classify as low risk
            if result["has_pii"]:
                # Calculate overall risk level
                risk_levels = [item["risk_level"] for item in result["detected_items"]]
                overall_risk = (
                    "high"
                    if "high" in risk_levels
                    else ("medium" if "medium" in risk_levels else "low")
                )
                assert overall_risk in [
                    "low",
                    "medium",
                ], f"False positive high risk for: {content}"

    @pytest.mark.asyncio
    async def test_detect_pii_medical_conditions(self, pii_detector):
        """Test detection of medical conditions and diagnoses."""
        medical_content = [
            "I was diagnosed with bipolar disorder",
            "My ADHD medication is helping",
            "I have chronic depression and anxiety",
        ]

        for content in medical_content:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            # Medical conditions might be detected as PII
            if result["has_pii"]:
                # Calculate overall risk level
                risk_levels = [item["risk_level"] for item in result["detected_items"]]
                overall_risk = (
                    "high"
                    if "high" in risk_levels
                    else ("medium" if "medium" in risk_levels else "low")
                )
                assert overall_risk in ["medium", "high"]

    @pytest.mark.asyncio
    async def test_detect_pii_crisis_hotlines(self, pii_detector):
        """Test that crisis hotlines are classified as low risk."""
        crisis_content = [
            "Call 988 for suicide prevention",
            "Text HOME to 741741",
            "National Suicide Prevention Lifeline: 988",
        ]

        for content in crisis_content:
            # Create a MemoryItem for testing
            memory_item = MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content=content,
                type="test",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            result = await pii_detector.detect_pii(memory_item)

            # Crisis hotlines should be low risk even if detected
            if result["has_pii"]:
                # Calculate overall risk level
                risk_levels = [item["risk_level"] for item in result["detected_items"]]
                overall_risk = (
                    "high"
                    if "high" in risk_levels
                    else ("medium" if "medium" in risk_levels else "low")
                )
                assert (
                    overall_risk == "low"
                ), f"Crisis hotline should be low risk: {content}"


class TestPIIDetectorIntegration:
    """Integration tests for PII detector with real dependencies."""

    @pytest.fixture
    def pii_detector(self):
        """Create a real PII detector instance."""
        return PIIDetector()

    @pytest.mark.asyncio
    async def test_presidio_integration(self, pii_detector):
        """Test integration with Presidio analyzer."""
        content = "My name is John Doe and I live in New York."

        # This test uses the real Presidio integration
        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        assert "has_pii" in result
        assert "detected_items" in result

        if result["has_pii"]:
            # Should have proper structure from Presidio
            for item in result["detected_items"]:
                assert "type" in item
                assert "text" in item
                assert "start" in item
                assert "end" in item

    @pytest.mark.asyncio
    async def test_huggingface_ner_integration(self, pii_detector):
        """Test integration with Hugging Face NER model."""
        content = "Dr. Smith at Johns Hopkins treated my depression."

        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)

        # Should detect person and organization entities
        assert "has_pii" in result
        assert "detected_items" in result

    @pytest.mark.asyncio
    async def test_performance_with_large_content(self, pii_detector):
        """Test performance with large content blocks."""
        import time

        # Create large content block
        large_content = "This is a test message with some PII. " * 1000
        large_content += "My name is John Doe and my email is john@example.com."

        start_time = time.time()
        # Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user",
            content=large_content,
            type="test",
            metadata={},
            timestamp=datetime.utcnow(),
        )

        result = await pii_detector.detect_pii(memory_item)
        end_time = time.time()

        # Should complete within reasonable time (adjust threshold as needed)
        processing_time = end_time - start_time
        assert (
            processing_time < 30.0
        ), f"PII detection took too long: {processing_time}s"

        # Should still detect PII correctly
        assert result["has_pii"] is True
