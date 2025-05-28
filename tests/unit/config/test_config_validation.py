"""
Tests for configuration validation and environment variable handling.
Tests prompt loading, required variable validation, and configuration warnings.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Import the configuration module
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../backend"))

from services.memory.config import Config, load_prompt_from_file


class TestPromptLoading:
    """Test prompt file loading functionality."""

    def test_load_prompt_from_file_success(self):
        """Test successful prompt loading from file."""
        test_content = "This is a test prompt with multiple lines.\nLine 2\nLine 3"

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch("os.path.exists", return_value=True):
                result = load_prompt_from_file("test_prompt.txt")

                assert result == test_content.strip()

    def test_load_prompt_from_file_not_found(self):
        """Test prompt loading when file doesn't exist."""
        fallback_content = "Fallback prompt content"

        with patch("os.path.exists", return_value=False):
            result = load_prompt_from_file("nonexistent.txt", fallback_content)

            assert result == fallback_content

    def test_load_prompt_from_file_empty(self):
        """Test prompt loading when file is empty."""
        fallback_content = "Fallback prompt content"

        with patch("builtins.open", mock_open(read_data="")):
            with patch("os.path.exists", return_value=True):
                result = load_prompt_from_file("empty_prompt.txt", fallback_content)

                assert result == fallback_content


class TestConfigValidation:
    """Test configuration validation functionality."""

    def test_validate_with_all_required_vars_chroma(self):
        """Test validation when all required variables are present for ChromaDB."""
        with patch.object(Config, "GOOGLE_API_KEY", "test_api_key"):
            with patch.object(Config, "VECTOR_DB_TYPE", "chroma"):
                with patch.object(Config, "USE_PINECONE", False):
                    # Should not raise any exception
                    Config.validate()

    def test_validate_with_all_required_vars_pinecone(self):
        """Test validation when all required variables are present for Pinecone."""
        with patch.object(Config, "GOOGLE_API_KEY", "test_api_key"):
            with patch.object(Config, "VECTOR_DB_TYPE", "pinecone"):
                with patch.object(Config, "PINECONE_API_KEY", "test_pinecone_key"):
                    with patch.object(Config, "USE_PINECONE", True):
                        # Should not raise any exception
                        Config.validate()

    def test_validate_missing_google_api_key(self):
        """Test validation when Google API key is missing."""
        with patch.object(Config, "GOOGLE_API_KEY", ""):
            with patch.object(Config, "VECTOR_DB_TYPE", "chroma"):
                with pytest.raises(ValueError) as exc_info:
                    Config.validate()

                assert "GOOGLE_API_KEY" in str(exc_info.value)


class TestPromptMethods:
    """Test prompt retrieval methods."""

    def test_get_mental_health_system_prompt_success(self):
        """Test successful mental health system prompt retrieval."""
        test_prompt = "You are a mental health assistant..."

        with patch(
            "services.memory.config.load_prompt_from_file", return_value=test_prompt
        ):
            result = Config.get_mental_health_system_prompt()
            assert result == test_prompt

    def test_get_mental_health_system_prompt_failure(self):
        """Test mental health system prompt retrieval when file loading fails."""
        with patch("services.memory.config.load_prompt_from_file", return_value=""):
            result = Config.get_mental_health_system_prompt()
            assert "CONFIGURATION ERROR" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
