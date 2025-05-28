"""
Pipeline integration test for EmotionVisualizer with realistic memory contexts.
This test simulates actual data to see how different memory inputs affect generated images.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from backend.services.image_generation.emotion_visualizer import EmotionVisualizer
from backend.services.image_generation.prompt_builder import PromptBuilder
from backend.services.image_generation.image_generator import ImageGenerator
from backend.services.memory.assistant.mental_health_assistant import (
    MentalHealthAssistant,
)


class TestEmotionVisualizerPipeline:
    """Test realistic pipeline scenarios with various memory contexts."""

    @pytest.fixture
    def mock_prompt_builder(self):
        mock = AsyncMock(spec=PromptBuilder)

        # Read the actual prompt template
        with open("backend/services/memory/prompts/photo_generation.txt", "r") as f:
            template = f.read()

        def format_template(context):
            return template.format(
                input_context=context["input_context"],
                short_term_context=context["short_term_context"],
                emotional_anchors=context["emotional_anchors"],
                long_term_context=context["long_term_context"],
            )

        mock.format_prompt_template = MagicMock(side_effect=format_template)
        return mock

    @pytest.fixture
    def mock_image_generator(self):
        mock = AsyncMock(spec=ImageGenerator)
        mock.get_recommended_params_for_emotion = MagicMock(
            return_value={
                "guidance_scale": 7.5,
                "num_inference_steps": 50,
                "width": 1024,
                "height": 1024,
            }
        )
        mock.generate_with_retry = AsyncMock(
            return_value={
                "success": True,
                "image_data": "mock_base64_image_data",
                "image_format": "png",
                "model": "FLUX.1-dev",
            }
        )
        return mock

    @pytest.fixture
    def mock_llm_client(self):
        mock = MagicMock(spec=MentalHealthAssistant)
        mock.model = MagicMock()

        # This will be set dynamically in each test
        mock_response = MagicMock()
        mock_response.text = "Generated visual prompt will be set in test"
        mock.model.generate_content = AsyncMock(return_value=mock_response)
        mock.metadata_config = MagicMock()
        return mock

    @pytest.fixture
    def emotion_visualizer(
        self, mock_prompt_builder, mock_image_generator, mock_llm_client
    ):
        return EmotionVisualizer(
            prompt_builder=mock_prompt_builder,
            image_generator=mock_image_generator,
            llm_client=mock_llm_client,
        )

    def create_memory_context(self, scenario: str) -> Dict[str, Any]:
        """Create realistic memory contexts for different scenarios."""

        scenarios = {
            "minimal_context": {
                "short_term_context": "User: Hi there\nAssistant: Hello! How are you feeling today?",
                "emotional_anchors": "No strong emotional anchors found.",
                "long_term_context": "No relevant long-term context.",
            },
            "rich_emotional_context": {
                "short_term_context": (
                    "User: I've been feeling really overwhelmed lately with work\n"
                    "Assistant: It sounds like you're carrying a heavy load right now\n"
                    "User: Yeah, everything feels like it's piling up and I can't catch my breath\n"
                    "Assistant: That feeling of being buried under responsibilities can be exhausting\n"
                    "User: It's like I'm drowning in a sea of endless tasks"
                ),
                "emotional_anchors": (
                    "Key emotional themes: overwhelm, heavy burden, drowning sensations | "
                    "workplace stress and anxiety | feelings of being trapped"
                ),
                "long_term_context": (
                    "Previous mentions of perfectionist tendencies | "
                    "Past discussions about needing control | "
                    "History of using water metaphors for emotional states"
                ),
            },
            "hopeful_transition": {
                "short_term_context": (
                    "User: I think I'm starting to feel better about things\n"
                    "Assistant: That's wonderful to hear. What's been helping?\n"
                    "User: I've been going for morning walks and the sunrise reminds me there's always a new day\n"
                    "Assistant: Natural rhythms can be really grounding and healing\n"
                    "User: Yes, it feels like I'm slowly climbing out of the darkness"
                ),
                "emotional_anchors": (
                    "Key emotional themes: hope and healing | sunrise and new beginnings | "
                    "nature as therapy | gradual recovery journey"
                ),
                "long_term_context": (
                    "Previous period of depression mentioned | "
                    "Childhood memories of nature providing comfort | "
                    "Pattern of using light/dark metaphors for mood"
                ),
            },
            "nostalgia_and_loss": {
                "short_term_context": (
                    "User: I found my grandmother's old recipe book today\n"
                    "Assistant: That must have brought up a lot of memories\n"
                    "User: It did. I can almost smell her kitchen and hear her humming while she cooked\n"
                    "Assistant: Sensory memories can be so vivid and powerful\n"
                    "User: I miss those warm Sunday afternoons at her house"
                ),
                "emotional_anchors": (
                    "Key emotional themes: nostalgia and longing | grandmother's memory | "
                    "sensory memories of warmth and comfort | Sunday family traditions"
                ),
                "long_term_context": (
                    "Grandmother passed away two years ago | "
                    "Cooking was a shared bonding activity | "
                    "Sunday family gatherings were central to childhood"
                ),
            },
            "anxiety_with_visual_elements": {
                "short_term_context": (
                    "User: My mind keeps racing with all these what-if scenarios\n"
                    "Assistant: Anxiety can create that spiraling pattern of thoughts\n"
                    "User: It's like there's a storm in my head that won't calm down\n"
                    "Assistant: That's a vivid way to describe it - the chaos and intensity\n"
                    "User: The thoughts are all dark gray and swirling, getting faster and faster"
                ),
                "emotional_anchors": (
                    "Key emotional themes: racing thoughts and mental storms | "
                    "anxiety spirals | dark gray swirling imagery | chaos and lack of control"
                ),
                "long_term_context": (
                    "History of anxiety episodes during major life changes | "
                    "Previous therapy discussions about thought patterns | "
                    "Tends to visualize emotions as weather patterns"
                ),
            },
        }

        return scenarios.get(scenario, scenarios["minimal_context"])

    @pytest.mark.asyncio
    async def test_minimal_context_scenario(
        self, emotion_visualizer, mock_prompt_builder, mock_llm_client
    ):
        """Test with minimal memory context - should request more input."""

        user_input = "Hi there"
        memory_context = self.create_memory_context("minimal_context")

        # Mock the context building
        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": False,
            "input_analysis": {
                "emotional_content": False,
                "visual_content": False,
                "richness_score": 0,
            },
            **memory_context,
        }

        result = await emotion_visualizer.create_emotional_image(
            user_id="test_user", user_input=user_input
        )

        assert result["success"] is False
        assert result["needs_more_input"] is True
        assert "I need a bit more to work with" in result["message"]

    @pytest.mark.asyncio
    async def test_rich_emotional_context_scenario(
        self,
        emotion_visualizer,
        mock_prompt_builder,
        mock_llm_client,
        mock_image_generator,
    ):
        """Test with rich emotional context - should generate vivid imagery."""

        user_input = "I feel like I'm drowning in responsibilities and can't find my way to the surface"
        memory_context = self.create_memory_context("rich_emotional_context")

        # Mock the context building
        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": True,
            "input_analysis": {
                "emotional_content": True,
                "visual_content": True,
                "richness_score": 3,
            },
            **memory_context,
        }

        # Mock LLM response for this rich context
        expected_visual_prompt = (
            "A figure suspended underwater in dark blue-gray depths, surrounded by swirling papers and documents "
            "that float like debris. Far above, a faint golden light filters down through the murky water, "
            "while the person reaches upward with determination despite the weight pulling them down."
        )

        mock_llm_client.model.generate_content.return_value.text = (
            expected_visual_prompt
        )

        result = await emotion_visualizer.create_emotional_image(
            user_id="test_user", user_input=user_input, include_long_term=True
        )

        assert result["success"] is True
        assert result["visual_prompt"] == expected_visual_prompt
        assert result["emotion_type"] in [
            "melancholic",
            "mysterious",
        ]  # Should detect heavy/dark emotion

        # Verify the LLM received the full context
        call_args = mock_llm_client.model.generate_content.call_args[0][0]
        assert "drowning in responsibilities" in call_args
        assert "overwhelm, heavy burden, drowning sensations" in call_args
        assert "workplace stress and anxiety" in call_args

    @pytest.mark.asyncio
    async def test_hopeful_transition_scenario(
        self,
        emotion_visualizer,
        mock_prompt_builder,
        mock_llm_client,
        mock_image_generator,
    ):
        """Test with hopeful context - should generate uplifting imagery."""

        user_input = (
            "I can feel myself getting stronger each day, like watching the sunrise"
        )
        memory_context = self.create_memory_context("hopeful_transition")

        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": True,
            "input_analysis": {
                "emotional_content": True,
                "visual_content": True,
                "richness_score": 2,
            },
            **memory_context,
        }

        expected_visual_prompt = (
            "A golden sunrise breaks over rolling hills where morning mist slowly lifts, revealing a winding path "
            "that climbs steadily upward. Warm amber and rose light bathes everything in hope, while delicate "
            "wildflowers emerge from the clearing fog, celebrating the gradual arrival of a new day."
        )

        mock_llm_client.model.generate_content.return_value.text = (
            expected_visual_prompt
        )

        result = await emotion_visualizer.create_emotional_image(
            user_id="test_user", user_input=user_input, include_long_term=True
        )

        assert result["success"] is True
        assert result["emotion_type"] == "hopeful"

        # Verify hopeful context influenced the generation
        call_args = mock_llm_client.model.generate_content.call_args[0][0]
        assert "sunrise" in call_args
        assert "hope and healing" in call_args
        assert "new beginnings" in call_args

    @pytest.mark.asyncio
    async def test_nostalgia_scenario(
        self,
        emotion_visualizer,
        mock_prompt_builder,
        mock_llm_client,
        mock_image_generator,
    ):
        """Test with nostalgic context - should generate warm, memory-based imagery."""

        user_input = "I can almost smell her kitchen and feel the warmth of those Sunday afternoons"
        memory_context = self.create_memory_context("nostalgia_and_loss")

        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": True,
            "input_analysis": {
                "emotional_content": True,
                "visual_content": True,
                "richness_score": 2,
            },
            **memory_context,
        }

        expected_visual_prompt = (
            "A sun-dappled kitchen bathed in golden afternoon light, where flour motes dance in the warm air "
            "and the scent of fresh bread mingles with memories. An empty chair sits by the window, "
            "while a worn recipe book lies open on a wooden table marked by years of loving use."
        )

        mock_llm_client.model.generate_content.return_value.text = (
            expected_visual_prompt
        )

        result = await emotion_visualizer.create_emotional_image(
            user_id="test_user", user_input=user_input, include_long_term=True
        )

        assert result["success"] is True

        # Verify nostalgic elements influenced the generation
        call_args = mock_llm_client.model.generate_content.call_args[0][0]
        assert "grandmother's memory" in call_args
        assert "Sunday family traditions" in call_args
        assert "sensory memories of warmth" in call_args

    @pytest.mark.asyncio
    async def test_context_comparison(
        self,
        emotion_visualizer,
        mock_prompt_builder,
        mock_llm_client,
        mock_image_generator,
    ):
        """Test how the same user input generates different results with different contexts."""

        user_input = "I feel overwhelmed"

        scenarios = [
            ("minimal_context", "Basic overwhelm without context"),
            ("rich_emotional_context", "Overwhelm with work stress context"),
            (
                "anxiety_with_visual_elements",
                "Overwhelm with anxiety and visual metaphors",
            ),
        ]

        results = {}

        for scenario_name, description in scenarios:
            memory_context = self.create_memory_context(scenario_name)

            # Determine sufficient content based on scenario
            has_sufficient = scenario_name != "minimal_context"

            mock_prompt_builder.build_image_prompt_context.return_value = {
                "input_context": user_input,
                "has_sufficient_content": has_sufficient,
                "input_analysis": {
                    "emotional_content": True,
                    "visual_content": has_sufficient,
                    "richness_score": 2 if has_sufficient else 0,
                },
                **memory_context,
            }

            if has_sufficient:
                # Create different visual prompts based on context
                if scenario_name == "rich_emotional_context":
                    mock_response = "A person buried under a mountain of papers and responsibilities, struggling to breathe."
                elif scenario_name == "anxiety_with_visual_elements":
                    mock_response = "Dark gray storm clouds swirl rapidly in a chaotic sky, with lightning crackling between racing thoughts."
                else:
                    mock_response = "A simple scene of overwhelming pressure."

                mock_llm_client.model.generate_content.return_value.text = mock_response

            result = await emotion_visualizer.create_emotional_image(
                user_id="test_user", user_input=user_input, include_long_term=True
            )

            results[scenario_name] = {
                "description": description,
                "success": result["success"],
                "visual_prompt": result.get("visual_prompt", "No prompt generated"),
                "needs_more_input": result.get("needs_more_input", False),
            }

        # Verify different contexts produce different results
        assert results["minimal_context"]["needs_more_input"] is True
        assert results["rich_emotional_context"]["success"] is True
        assert results["anxiety_with_visual_elements"]["success"] is True

        # The visual prompts should be different
        assert (
            results["rich_emotional_context"]["visual_prompt"]
            != results["anxiety_with_visual_elements"]["visual_prompt"]
        )

        # Print results for manual verification
        print("\n" + "=" * 60)
        print("CONTEXT COMPARISON RESULTS")
        print("=" * 60)
        print(f"User Input: '{user_input}'")
        print()

        for scenario, result in results.items():
            print(f"SCENARIO: {scenario}")
            print(f"Description: {result['description']}")
            print(f"Success: {result['success']}")
            print(f"Visual Prompt: {result['visual_prompt']}")
            print(f"Needs More Input: {result['needs_more_input']}")
            print("-" * 40)

    def test_prompt_template_formatting(self, mock_prompt_builder):
        """Test that the prompt template correctly formats with different contexts."""

        # Test rich context formatting
        context = {
            "input_context": "I feel like I'm drowning in work",
            "short_term_context": "User has been discussing work stress for several messages",
            "emotional_anchors": "Key themes: overwhelm, water metaphors, workplace anxiety",
            "long_term_context": "History of perfectionist tendencies and control issues",
        }

        formatted_prompt = mock_prompt_builder.format_prompt_template(context)

        # Verify all context elements are included
        assert "I feel like I'm drowning in work" in formatted_prompt
        assert "discussing work stress" in formatted_prompt
        assert "overwhelm, water metaphors" in formatted_prompt
        assert "perfectionist tendencies" in formatted_prompt

        # Verify template structure is preserved
        assert "📊 INPUT DATA ANALYSIS:" in formatted_prompt
        assert "🎨 GENERATION TASK:" in formatted_prompt
        assert "✏️ GENERATE YOUR RESPONSE:" in formatted_prompt

        print("\n" + "=" * 60)
        print("FORMATTED PROMPT EXAMPLE")
        print("=" * 60)
        print(formatted_prompt)
        print("=" * 60)

    @pytest.mark.asyncio
    async def test_identified_emotion_impact(
        self,
        emotion_visualizer,
        mock_prompt_builder,
        mock_llm_client,
        mock_image_generator,
    ):
        """Test how identified_emotion affects memory retrieval and prompt generation."""

        user_input = "I've been struggling lately"

        # Test without identified emotion
        memory_context_no_emotion = {
            "short_term_context": "User: I've been struggling lately\nAssistant: Tell me more about what you're going through",
            "emotional_anchors": "Key emotional themes: general struggle | unspecified difficulties",
            "long_term_context": "Previous mentions of general life challenges",
        }

        # Test with identified emotion - should get more specific emotional context
        memory_context_with_emotion = {
            "short_term_context": "User: I've been struggling lately\nAssistant: Tell me more about what you're going through",
            "emotional_anchors": "Key emotional themes: anxiety and worry | racing thoughts | fear of unknown | restlessness",
            "long_term_context": "Previous anxiety episodes | history of overthinking | pattern of worry about future events",
        }

        # Test 1: Without identified emotion
        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": True,
            "input_analysis": {
                "emotional_content": True,
                "visual_content": False,
                "richness_score": 1,
            },
            **memory_context_no_emotion,
        }

        mock_llm_client.model.generate_content.return_value.text = "A person walking through an undefined gray landscape, uncertain of direction."

        result_no_emotion = await emotion_visualizer.create_emotional_image(
            user_id="test_user",
            user_input=user_input,
            include_long_term=True,
            identified_emotion=None,
        )

        # Test 2: With identified emotion (anxiety)
        mock_prompt_builder.build_image_prompt_context.return_value = {
            "input_context": user_input,
            "has_sufficient_content": True,
            "input_analysis": {
                "emotional_content": True,
                "visual_content": True,
                "richness_score": 2,
            },
            **memory_context_with_emotion,
        }

        mock_llm_client.model.generate_content.return_value.text = "Swirling storm clouds gather overhead as restless winds whip through an uncertain landscape, where every shadow holds a question and every path leads to the unknown."

        result_with_emotion = await emotion_visualizer.create_emotional_image(
            user_id="test_user",
            user_input=user_input,
            include_long_term=True,
            identified_emotion="anxiety",
        )

        # Verify both calls were made with correct parameters
        assert mock_prompt_builder.build_image_prompt_context.call_count == 2

        # First call should have None for identified_emotion
        first_call = mock_prompt_builder.build_image_prompt_context.call_args_list[0]
        assert first_call[0][3] is None  # identified_emotion parameter

        # Second call should have "anxiety" for identified_emotion
        second_call = mock_prompt_builder.build_image_prompt_context.call_args_list[1]
        assert second_call[0][3] == "anxiety"  # identified_emotion parameter

        # Verify different visual prompts were generated
        assert (
            result_no_emotion["visual_prompt"] != result_with_emotion["visual_prompt"]
        )
        assert "storm clouds" in result_with_emotion["visual_prompt"]
        assert "restless winds" in result_with_emotion["visual_prompt"]

        # Print comparison for manual verification
        print("\n" + "=" * 70)
        print("IDENTIFIED EMOTION IMPACT COMPARISON")
        print("=" * 70)
        print(f"User Input: '{user_input}'")
        print()

        print("WITHOUT IDENTIFIED EMOTION:")
        print(f"Visual Prompt: {result_no_emotion['visual_prompt']}")
        print(
            f"Emotion Type Detected: {result_no_emotion.get('emotion_type', 'unknown')}"
        )
        print()

        print("WITH IDENTIFIED EMOTION (anxiety):")
        print(f"Visual Prompt: {result_with_emotion['visual_prompt']}")
        print(
            f"Emotion Type Detected: {result_with_emotion.get('emotion_type', 'unknown')}"
        )
        print("=" * 70)
