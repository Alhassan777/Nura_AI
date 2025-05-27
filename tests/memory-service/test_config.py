import pytest
from unittest.mock import patch
import os

from ..config import Config


@pytest.fixture
def mock_env():
    """Create mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "REDIS_URL": "redis://localhost:6379",
            "CHROMA_PERSIST_DIR": "./chroma",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GOOGLE_API_KEY": "test-key",
            "USE_VERTEX_AI": "false",
            "JWT_SECRET_KEY": "test-secret",
            "JWT_ALGORITHM": "HS256",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "AUDIT_LOG_FILE": "test_audit.log",
            "AUDIT_LOG_LEVEL": "INFO",
            "SENSITIVE_ENTITIES": "PERSON,EMAIL,PHONE,SSN",
            "REQUIRE_CONSENT_ENTITIES": "PERSON,EMAIL",
            "SHORT_TERM_SIZE": "100",
            "LONG_TERM_SIZE": "1000",
            "RELEVANCE_THRESHOLD": "0.6",
            "STABILITY_THRESHOLD": "0.7",
            "EXPLICITNESS_THRESHOLD": "0.5",
        },
    ):
        yield


def test_config_initialization(mock_env):
    """Test configuration initialization."""
    # Initialize config
    config = Config()

    # Verify Redis settings
    assert config.REDIS_URL == "redis://localhost:6379"

    # Verify Chroma settings
    assert config.CHROMA_PERSIST_DIR == "./chroma"

    # Verify Google Cloud settings
    assert config.GOOGLE_CLOUD_PROJECT == "test-project"
    assert config.GOOGLE_API_KEY == "test-key"
    assert config.USE_VERTEX_AI is False

    # Verify JWT settings
    assert config.JWT_SECRET_KEY == "test-secret"
    assert config.JWT_ALGORITHM == "HS256"
    assert config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30

    # Verify audit settings
    assert config.AUDIT_LOG_FILE == "test_audit.log"
    assert config.AUDIT_LOG_LEVEL == "INFO"

    # Verify PII settings
    assert config.SENSITIVE_ENTITIES == ["PERSON", "EMAIL", "PHONE", "SSN"]
    assert config.REQUIRE_CONSENT_ENTITIES == ["PERSON", "EMAIL"]

    # Verify memory settings
    assert config.get_memory_config() == {
        "short_term_size": 100,
        "long_term_size": 1000,
        "relevance_threshold": 0.6,
        "stability_threshold": 0.7,
        "explicitness_threshold": 0.5,
    }


def test_config_missing_required(mock_env):
    """Test configuration with missing required settings."""
    # Remove required setting
    with patch.dict(os.environ, {}, clear=True):
        # Initialize config
        with pytest.raises(ValueError) as exc_info:
            Config()

        # Verify error
        assert "Missing required environment variable" in str(exc_info.value)


def test_config_invalid_boolean(mock_env):
    """Test configuration with invalid boolean value."""
    # Set invalid boolean
    with patch.dict(os.environ, {"USE_VERTEX_AI": "invalid"}):
        # Initialize config
        with pytest.raises(ValueError) as exc_info:
            Config()

        # Verify error
        assert "Invalid boolean value" in str(exc_info.value)


def test_config_invalid_integer(mock_env):
    """Test configuration with invalid integer value."""
    # Set invalid integer
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "invalid"}):
        # Initialize config
        with pytest.raises(ValueError) as exc_info:
            Config()

        # Verify error
        assert "Invalid integer value" in str(exc_info.value)


def test_config_invalid_float(mock_env):
    """Test configuration with invalid float value."""
    # Set invalid float
    with patch.dict(os.environ, {"RELEVANCE_THRESHOLD": "invalid"}):
        # Initialize config
        with pytest.raises(ValueError) as exc_info:
            Config()

        # Verify error
        assert "Invalid float value" in str(exc_info.value)


def test_config_invalid_list(mock_env):
    """Test configuration with invalid list value."""
    # Set invalid list
    with patch.dict(os.environ, {"SENSITIVE_ENTITIES": ""}):
        # Initialize config
        with pytest.raises(ValueError) as exc_info:
            Config()

        # Verify error
        assert "Invalid list value" in str(exc_info.value)


def test_config_default_values(mock_env):
    """Test configuration default values."""
    # Remove optional settings
    with patch.dict(
        os.environ,
        {
            "REDIS_URL": "redis://localhost:6379",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GOOGLE_API_KEY": "test-key",
            "JWT_SECRET_KEY": "test-secret",
        },
        clear=True,
    ):
        # Initialize config
        config = Config()

        # Verify default values
        assert config.CHROMA_PERSIST_DIR == "./chroma"
        assert config.USE_VERTEX_AI is False
        assert config.JWT_ALGORITHM == "HS256"
        assert config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert config.AUDIT_LOG_FILE == "audit.log"
        assert config.AUDIT_LOG_LEVEL == "INFO"
        assert config.SENSITIVE_ENTITIES == ["PERSON", "EMAIL", "PHONE", "SSN"]
        assert config.REQUIRE_CONSENT_ENTITIES == ["PERSON", "EMAIL"]
        assert config.get_memory_config() == {
            "short_term_size": 100,
            "long_term_size": 1000,
            "relevance_threshold": 0.6,
            "stability_threshold": 0.7,
            "explicitness_threshold": 0.5,
        }


def test_config_singleton(mock_env):
    """Test configuration singleton pattern."""
    # Initialize config twice
    config1 = Config()
    config2 = Config()

    # Verify same instance
    assert config1 is config2


def test_config_reload(mock_env):
    """Test configuration reload."""
    # Initialize config
    config = Config()

    # Change environment variable
    with patch.dict(os.environ, {"REDIS_URL": "redis://new-host:6379"}):
        # Reload config
        config.reload()

        # Verify new value
        assert config.REDIS_URL == "redis://new-host:6379"
