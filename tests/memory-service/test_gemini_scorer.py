import pytest
from unittest.mock import Mock, patch

from ..scoring.gemini_scorer import GeminiScorer
from ..types import MemoryItem, MemoryScore


@pytest.fixture
def gemini_scorer():
    """Create a Gemini scorer instance for testing."""
    with patch("src.services.memory.scoring.gemini_scorer.Config") as mock_config:
        mock_config.GOOGLE_CLOUD_PROJECT = "test-project"
        mock_config.GOOGLE_API_KEY = "test-key"
        mock_config.USE_VERTEX_AI = False
        mock_config.get_memory_config.return_value = {
            "relevance_threshold": 0.6,
            "stability_threshold": 0.7,
            "explicitness_threshold": 0.5,
        }

        scorer = GeminiScorer()
        return scorer


@pytest.fixture
def sample_memory():
    """Create a sample memory item for testing."""
    return MemoryItem(
        id="test-id",
        userId="test-user",
        content="I've been feeling anxious lately and need help with my mental health",
        type="chat",
        metadata={
            "timestamp": "2024-03-20T10:00:00Z",
            "has_pii": False,
            "sensitive_types": [],
        },
    )


@pytest.mark.asyncio
async def test_score_memory(gemini_scorer, sample_memory):
    """Test memory scoring."""
    # Mock Gemini model
    gemini_scorer.model.generate_content = Mock(
        return_value=Mock(
            text='{"relevance": 0.8, "stability": 0.9, "explicitness": 0.7, "sensitivity": true, "sensitive_types": ["MENTAL_HEALTH"]}'
        )
    )

    # Score memory
    score = await gemini_scorer.score_memory(sample_memory)

    # Verify result
    assert isinstance(score, MemoryScore)
    assert score.relevance == 0.8
    assert score.stability == 0.9
    assert score.explicitness == 0.7
    assert score.sensitivity is True
    assert "MENTAL_HEALTH" in score.sensitive_types

    # Verify calls
    gemini_scorer.model.generate_content.assert_called_once()
    prompt = gemini_scorer.model.generate_content.call_args[0][0]
    assert "I've been feeling anxious lately" in prompt
    assert "MENTAL_HEALTH" in prompt


@pytest.mark.asyncio
async def test_score_memory_with_pii(gemini_scorer, sample_memory):
    """Test memory scoring with PII."""
    # Update memory with PII
    sample_memory.metadata["has_pii"] = True
    sample_memory.metadata["sensitive_types"] = ["PERSON"]

    # Mock Gemini model
    gemini_scorer.model.generate_content = Mock(
        return_value=Mock(
            text='{"relevance": 0.8, "stability": 0.9, "explicitness": 0.7, "sensitivity": true, "sensitive_types": ["MENTAL_HEALTH", "PERSON"]}'
        )
    )

    # Score memory
    score = await gemini_scorer.score_memory(sample_memory)

    # Verify result
    assert isinstance(score, MemoryScore)
    assert score.relevance == 0.8
    assert score.stability == 0.9
    assert score.explicitness == 0.7
    assert score.sensitivity is True
    assert "MENTAL_HEALTH" in score.sensitive_types
    assert "PERSON" in score.sensitive_types

    # Verify calls
    gemini_scorer.model.generate_content.assert_called_once()
    prompt = gemini_scorer.model.generate_content.call_args[0][0]
    assert "PERSON" in prompt


@pytest.mark.asyncio
async def test_score_memory_low_relevance(gemini_scorer, sample_memory):
    """Test memory scoring with low relevance."""
    # Mock Gemini model
    gemini_scorer.model.generate_content = Mock(
        return_value=Mock(
            text='{"relevance": 0.3, "stability": 0.9, "explicitness": 0.7, "sensitivity": false, "sensitive_types": []}'
        )
    )

    # Score memory
    score = await gemini_scorer.score_memory(sample_memory)

    # Verify result
    assert isinstance(score, MemoryScore)
    assert score.relevance == 0.3
    assert score.stability == 0.9
    assert score.explicitness == 0.7
    assert score.sensitivity is False
    assert len(score.sensitive_types) == 0


def test_should_store_memory(gemini_scorer):
    """Test memory storage decision."""
    # Test with high scores
    score = MemoryScore(
        relevance=0.8,
        stability=0.9,
        explicitness=0.7,
        sensitivity=False,
        sensitive_types=[],
    )
    assert gemini_scorer.should_store_memory(score) is True

    # Test with low relevance
    score.relevance = 0.3
    assert gemini_scorer.should_store_memory(score) is False

    # Test with low stability
    score.relevance = 0.8
    score.stability = 0.3
    assert gemini_scorer.should_store_memory(score) is False

    # Test with low explicitness
    score.stability = 0.9
    score.explicitness = 0.3
    assert gemini_scorer.should_store_memory(score) is False

    # Test with sensitive content
    score.explicitness = 0.7
    score.sensitivity = True
    assert gemini_scorer.should_store_memory(score) is True


@pytest.mark.asyncio
async def test_score_memory_error_handling(gemini_scorer, sample_memory):
    """Test memory scoring error handling."""
    # Mock Gemini model to raise an exception
    gemini_scorer.model.generate_content = Mock(side_effect=Exception("API error"))

    # Score memory
    score = await gemini_scorer.score_memory(sample_memory)

    # Verify default score
    assert isinstance(score, MemoryScore)
    assert score.relevance == 0.5  # Default value
    assert score.stability == 0.5  # Default value
    assert score.explicitness == 0.5  # Default value
    assert score.sensitivity is False
    assert len(score.sensitive_types) == 0

    # Verify calls
    gemini_scorer.model.generate_content.assert_called_once()
