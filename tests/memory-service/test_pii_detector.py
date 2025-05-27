import pytest
from unittest.mock import Mock, patch

from ..security.pii_detector import PIIDetector


@pytest.fixture
def pii_detector():
    """Create a PII detector instance for testing."""
    with patch("src.services.memory.security.pii_detector.Config") as mock_config:
        mock_config.SENSITIVE_ENTITIES = ["PERSON", "EMAIL", "PHONE", "SSN"]
        mock_config.REQUIRE_CONSENT_ENTITIES = ["PERSON", "EMAIL"]
        mock_config.ANONYMIZATION_MAP = {
            "PERSON": "[PERSON]",
            "EMAIL": "[EMAIL]",
            "PHONE": "[PHONE]",
            "SSN": "[SSN]",
        }

        detector = PIIDetector()
        return detector


def test_detect_pii(pii_detector):
    """Test PII detection."""
    # Mock Presidio analyzer
    pii_detector.analyzer.analyze = Mock(
        return_value=[
            {"entity_type": "PERSON", "start": 0, "end": 4, "score": 0.9},
            {"entity_type": "EMAIL", "start": 10, "end": 25, "score": 0.95},
        ]
    )

    # Test detection
    result = pii_detector.detect_pii("John's email is john@example.com")

    # Verify result
    assert result["has_pii"]
    assert len(result["entities"]) == 2
    assert "PERSON" in result["entities"]
    assert "EMAIL" in result["entities"]
    assert result["entities"]["PERSON"][0]["text"] == "John"
    assert result["entities"]["EMAIL"][0]["text"] == "john@example.com"

    # Verify calls
    pii_detector.analyzer.analyze.assert_called_once()


def test_detect_pii_no_pii(pii_detector):
    """Test PII detection with no PII."""
    # Mock Presidio analyzer
    pii_detector.analyzer.analyze = Mock(return_value=[])

    # Test detection
    result = pii_detector.detect_pii("This is a normal message")

    # Verify result
    assert not result["has_pii"]
    assert len(result["entities"]) == 0

    # Verify calls
    pii_detector.analyzer.analyze.assert_called_once()


def test_requires_consent(pii_detector):
    """Test consent requirement check."""
    # Test with entities requiring consent
    result = pii_detector.requires_consent(
        {
            "PERSON": [{"text": "John", "start": 0, "end": 4}],
            "EMAIL": [{"text": "john@example.com", "start": 10, "end": 25}],
        }
    )
    assert result is True

    # Test with entities not requiring consent
    result = pii_detector.requires_consent(
        {
            "PHONE": [{"text": "123-456-7890", "start": 0, "end": 12}],
            "SSN": [{"text": "123-45-6789", "start": 15, "end": 26}],
        }
    )
    assert result is False

    # Test with mixed entities
    result = pii_detector.requires_consent(
        {
            "PERSON": [{"text": "John", "start": 0, "end": 4}],
            "PHONE": [{"text": "123-456-7890", "start": 10, "end": 22}],
        }
    )
    assert result is True


def test_anonymize_content(pii_detector):
    """Test content anonymization."""
    # Test anonymization
    result = pii_detector.anonymize_content(
        "John's email is john@example.com and phone is 123-456-7890",
        {
            "PERSON": [{"text": "John", "start": 0, "end": 4}],
            "EMAIL": [{"text": "john@example.com", "start": 15, "end": 30}],
            "PHONE": [{"text": "123-456-7890", "start": 40, "end": 52}],
        },
    )

    # Verify result
    assert result == "[PERSON]'s email is [EMAIL] and phone is [PHONE]"


def test_anonymize_content_no_pii(pii_detector):
    """Test content anonymization with no PII."""
    # Test anonymization
    result = pii_detector.anonymize_content("This is a normal message", {})

    # Verify result
    assert result == "This is a normal message"


def test_anonymize_content_overlapping(pii_detector):
    """Test content anonymization with overlapping entities."""
    # Test anonymization
    result = pii_detector.anonymize_content(
        "John's email is john@example.com and his name is John",
        {
            "PERSON": [
                {"text": "John", "start": 0, "end": 4},
                {"text": "John", "start": 45, "end": 49},
            ],
            "EMAIL": [{"text": "john@example.com", "start": 15, "end": 30}],
        },
    )

    # Verify result
    assert result == "[PERSON]'s email is [EMAIL] and his name is [PERSON]"
