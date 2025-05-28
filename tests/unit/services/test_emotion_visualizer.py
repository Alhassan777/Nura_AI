import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from typing import Dict, Any, Optional

# Imports for the class under test and its dependencies
from backend.services.image_generation.emotion_visualizer import EmotionVisualizer
from backend.services.image_generation.prompt_builder import PromptBuilder
from backend.services.image_generation.image_generator import ImageGenerator
from backend.services.memory.assistant.mental_health_assistant import (
    MentalHealthAssistant,
)
import google.generativeai as genai  # For mocking GenerationConfig and response objects

# pytest_plugins = ['pytest_asyncio'] # Not needed for pytest >= 3.9


@pytest.fixture
def mock_prompt_builder():
    mock = AsyncMock(spec=PromptBuilder)
    mock.format_prompt_template = MagicMock(return_value="Formatted LLM Prompt")
    return mock


@pytest.fixture
def mock_image_generator():
    mock = AsyncMock(spec=ImageGenerator)
    mock.get_recommended_params_for_emotion = MagicMock(return_value={"param": "value"})
    return mock


@pytest.fixture
def mock_llm_client():
    mock = MagicMock(spec=MentalHealthAssistant)

    # Mock the model attribute
    mock.model = MagicMock()

    # Mock the generate_content method to return an awaitable
    mock_llm_response = MagicMock()
    mock_llm_response.text = "A beautiful visual prompt about user feelings."
    mock.model.generate_content = AsyncMock(return_value=mock_llm_response)

    # Mock the metadata_config
    mock.metadata_config = genai.types.GenerationConfig(temperature=0.5)
    return mock


@pytest.fixture
def emotion_visualizer(mock_prompt_builder, mock_image_generator, mock_llm_client):
    return EmotionVisualizer(
        prompt_builder=mock_prompt_builder,
        image_generator=mock_image_generator,
        llm_client=mock_llm_client,
    )


@pytest.mark.asyncio
async def test_create_emotional_image_happy_path(
    emotion_visualizer, mock_prompt_builder, mock_image_generator, mock_llm_client
):
    user_id = "test_user_123"
    user_input = "I feel a bit down today, like a rainy sky."
    identified_emotion = "sadness"

    # Mock PromptBuilder response
    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "short_term_context": "User: I feel a bit down today...",
        "emotional_anchors": "Key emotional themes: sadness | rainy days",
        "long_term_context": "Past mention of feeling blue on rainy days.",
        "input_analysis": {
            "emotional_content": True,
            "visual_content": True,
            "richness_score": 2,
        },
        "has_sufficient_content": True,
    }

    # Mock ImageGenerator response
    mock_image_generator.generate_with_retry.return_value = {
        "success": True,
        "image_data": "base64_encoded_image_data",
        "image_format": "png",
        "model": "FLUX.1-dev",
    }

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id,
        user_input=user_input,
        include_long_term=True,
        save_locally=False,
        identified_emotion=identified_emotion,
    )

    assert result["success"] is True
    assert result["image_data"] == "base64_encoded_image_data"
    assert "A beautiful visual prompt about user feelings." in result["visual_prompt"]
    assert result["emotion_type"] is not None  # an emotion type should be determined
    assert result["context_analysis"]["emotional_content"] is True

    mock_prompt_builder.build_image_prompt_context.assert_called_once_with(
        user_id, user_input, True, identified_emotion
    )
    # Assert that format_prompt_template was called by _generate_visual_prompt
    mock_prompt_builder.format_prompt_template.assert_called_once()

    # Assert LLM call
    mock_llm_client.model.generate_content.assert_called_once_with(
        "Formatted LLM Prompt", generation_config=mock_llm_client.metadata_config
    )

    mock_image_generator.generate_with_retry.assert_called_once()
    # The first argument to generate_with_retry is the visual_prompt from LLM
    # Ensure the cleaned prompt is passed
    cleaned_visual_prompt_arg = mock_image_generator.generate_with_retry.call_args[0][0]
    assert cleaned_visual_prompt_arg == "A beautiful visual prompt about user feelings."
    # The keyword argument custom_params should be what get_recommended_params_for_emotion returned
    assert mock_image_generator.generate_with_retry.call_args[1]["custom_params"] == {
        "param": "value"
    }


@pytest.mark.asyncio
async def test_create_emotional_image_insufficient_content(
    emotion_visualizer, mock_prompt_builder
):
    user_id = "test_user_456"
    user_input = "Hi"
    identified_emotion = None  # Explicitly set to None for this test case

    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "short_term_context": "",
        "emotional_anchors": "",
        "long_term_context": "",
        "input_analysis": {
            "emotional_content": False,
            "visual_content": False,
            "richness_score": 0,
        },
        "has_sufficient_content": False,
    }

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id, user_input=user_input, identified_emotion=identified_emotion
    )

    assert result["success"] is False
    assert result["needs_more_input"] is True
    assert "I need a bit more to work with" in result["message"]
    mock_prompt_builder.build_image_prompt_context.assert_called_once_with(
        user_id,
        user_input,
        False,
        identified_emotion,  # Verify None is passed correctly
    )


@pytest.mark.asyncio
async def test_create_emotional_image_llm_failure_empty_response(
    emotion_visualizer, mock_prompt_builder, mock_llm_client
):
    user_id = "test_user_789"
    user_input = "This is some valid input for prompting."

    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "has_sufficient_content": True,
        # ... other context fields
    }

    # Mock LLM to return an empty/insufficient response
    mock_llm_response = MagicMock()
    mock_llm_response.text = ""  # Empty response
    mock_llm_client.model.generate_content.return_value = mock_llm_response

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id, user_input=user_input
    )

    assert result["success"] is False
    assert result.get("error") == "llm_response_insufficient"
    assert "LLM failed to generate sufficient visual description" in result["message"]
    mock_prompt_builder.format_prompt_template.assert_called_once()
    assert mock_llm_client.model.generate_content.call_count == 1


@pytest.mark.asyncio
async def test_create_emotional_image_llm_exception(
    emotion_visualizer, mock_prompt_builder, mock_llm_client
):
    user_id = "test_user_101"
    user_input = "More valid input."

    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "has_sufficient_content": True,
        # ... other context fields
    }

    # Mock LLM to raise an exception
    mock_llm_client.model.generate_content.side_effect = Exception(
        "LLM simulated error"
    )

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id, user_input=user_input
    )

    assert result["success"] is False
    assert result.get("error") == "llm_error"
    assert "Error generating visual prompt: LLM simulated error" in result["message"]
    mock_prompt_builder.format_prompt_template.assert_called_once()
    assert mock_llm_client.model.generate_content.call_count == 1


@pytest.mark.asyncio
async def test_create_emotional_image_generator_failure(
    emotion_visualizer, mock_prompt_builder, mock_image_generator, mock_llm_client
):
    user_id = "test_user_112"
    user_input = "Feeling a surge of energy!"
    identified_emotion = "energetic"

    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "short_term_context": "User: Feeling energetic!",
        "emotional_anchors": "Key emotional themes: energy",
        "long_term_context": "",
        "input_analysis": {
            "emotional_content": True,
            "visual_content": False,
            "richness_score": 1,
        },
        "has_sufficient_content": True,
    }

    # LLM is fine
    mock_llm_response = MagicMock()
    mock_llm_response.text = "A vibrant scene of exploding colors and motion."
    mock_llm_client.model.generate_content.return_value = mock_llm_response

    # Mock ImageGenerator to fail
    mock_image_generator.generate_with_retry.return_value = {
        "success": False,
        "error": "api_error",
        "message": "Hugging Face API down",
    }

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id, user_input=user_input, identified_emotion=identified_emotion
    )

    assert result["success"] is False
    assert result.get("error") == "image_generation_failed"
    assert "Failed to generate image: Hugging Face API down" in result["message"]
    assert result["visual_prompt"] == "A vibrant scene of exploding colors and motion."

    mock_prompt_builder.format_prompt_template.assert_called_once()
    assert mock_llm_client.model.generate_content.call_count == 1
    mock_image_generator.generate_with_retry.assert_called_once()

    # Verify identified_emotion was passed correctly to build_image_prompt_context
    mock_prompt_builder.build_image_prompt_context.assert_called_once_with(
        user_id, user_input, False, identified_emotion
    )


@pytest.mark.asyncio
async def test_create_emotional_image_save_locally(
    emotion_visualizer, mock_prompt_builder, mock_image_generator, mock_llm_client
):
    user_id = "test_user_local_save"
    user_input = "I want to save this memory as an image."

    mock_prompt_builder.build_image_prompt_context.return_value = {
        "input_context": user_input,
        "short_term_context": "User: I want to save this memory as an image.",
        "emotional_anchors": "Key emotional themes: memory, image",
        "long_term_context": "",
        "has_sufficient_content": True,
        "input_analysis": {
            "emotional_content": True,
            "visual_content": True,
            "richness_score": 2,
        },
    }

    mock_llm_response = MagicMock()
    mock_llm_response.text = "A locally saved masterpiece."
    mock_llm_client.model.generate_content.return_value = mock_llm_response

    mock_image_generator.generate_with_retry.return_value = {
        "success": True,
        "image_data": "local_image_data_base64",
        "image_format": "png",
        "model": "FLUX.1-dev",
    }
    # Mock save_image_locally
    mock_image_generator.save_image_locally = AsyncMock(
        return_value="/path/to/saved/image.png"
    )

    result = await emotion_visualizer.create_emotional_image(
        user_id=user_id, user_input=user_input, save_locally=True  # Enable local saving
    )

    assert result["success"] is True
    assert result["image_data"] == "local_image_data_base64"
    assert result["saved_path"] == "/path/to/saved/image.png"
    mock_image_generator.save_image_locally.assert_called_once_with(
        "local_image_data_base64",
        ANY,  # filename is dynamically generated with timestamp
    )
    # Check that the filename contains user_id
    saved_filename_arg = mock_image_generator.save_image_locally.call_args[0][1]
    assert user_id in saved_filename_arg
    assert "emotion_art_" in saved_filename_arg


# It might be useful to also test _analyze_emotion_type directly if it had more complex logic,
# but given its current keyword-based approach, testing it via create_emotional_image implicitly covers it
# when checking mock_image_generator.get_recommended_params_for_emotion calls.


# Test for _clean_visual_prompt logic
def test_clean_visual_prompt(emotion_visualizer):
    raw_text_1 = (
        '"✏️ GENERATE YOUR RESPONSE: A beautiful landscape with mountains and a river."'
    )
    cleaned_1 = emotion_visualizer._clean_visual_prompt(raw_text_1)
    assert cleaned_1 == "A beautiful landscape with mountains and a river."

    raw_text_2 = "  Here's the visual scene: An abstract representation of joy.  "
    cleaned_2 = emotion_visualizer._clean_visual_prompt(raw_text_2)
    assert cleaned_2 == "An abstract representation of joy."

    raw_text_3 = "Visual prompt: A single tree in a vast desert"  # No ending period
    cleaned_3 = emotion_visualizer._clean_visual_prompt(raw_text_3)
    assert cleaned_3 == "A single tree in a vast desert."

    raw_text_4 = "Just a plain sentence without artifacts."
    cleaned_4 = emotion_visualizer._clean_visual_prompt(raw_text_4)
    assert cleaned_4 == "Just a plain sentence without artifacts."
