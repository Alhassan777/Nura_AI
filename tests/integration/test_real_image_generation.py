"""
Real integration test for EmotionVisualizer that generates actual images.
This test uses the real API services to demonstrate the pipeline with actual image generation.
"""

import os
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(".env")  # Load from current directory (backend)

from services.image_generation.emotion_visualizer import EmotionVisualizer
from services.image_generation.prompt_builder import PromptBuilder
from services.image_generation.image_generator import ImageGenerator
from services.memory.assistant.mental_health_assistant import (
    MentalHealthAssistant,
)


class RealImageGenerationDemo:
    """Demo class for generating real images with different memory contexts."""

    def __init__(self):
        # Create output directory for generated images
        self.output_dir = Path("generated_images_demo")
        self.output_dir.mkdir(exist_ok=True)

        # Initialize services using the new simplified architecture
        # PromptBuilder now uses MemoryService internally for consistent memory retrieval
        self.prompt_builder = PromptBuilder()
        self.image_generator = ImageGenerator()
        self.llm_client = MentalHealthAssistant()

        self.emotion_visualizer = EmotionVisualizer(
            prompt_builder=self.prompt_builder,
            image_generator=self.image_generator,
            llm_client=self.llm_client,
        )

    def create_mock_memory_context(self, scenario: str) -> Dict[str, Any]:
        """Create realistic memory contexts for different scenarios."""

        scenarios = {
            "overwhelmed_at_work": {
                "input_context": "I feel like I'm drowning in responsibilities and can't find my way to the surface",
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
                "identified_emotion": "anxiety",
            },
            "hopeful_recovery": {
                "input_context": "I can feel myself getting stronger each day, like watching the sunrise",
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
                "identified_emotion": "hopeful",
            },
            "nostalgic_memory": {
                "input_context": "I can almost smell her kitchen and feel the warmth of those Sunday afternoons",
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
                "identified_emotion": "melancholic",
            },
            "racing_thoughts": {
                "input_context": "My mind feels like a storm that won't calm down, with thoughts spinning faster and faster",
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
                "identified_emotion": "anxiety",
            },
        }

        return scenarios.get(scenario, scenarios["overwhelmed_at_work"])

    async def generate_image_for_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Generate an image for a specific scenario and save it."""

        print(f"\n{'='*60}")
        print(f"GENERATING IMAGE FOR: {scenario_name.upper()}")
        print(f"{'='*60}")

        scenario_data = self.create_mock_memory_context(scenario_name)

        try:
            # Mock the prompt builder's context gathering
            async def mock_build_context(
                user_id, user_input, include_long_term, identified_emotion
            ):
                return {
                    "input_context": scenario_data["input_context"],
                    "short_term_context": scenario_data["short_term_context"],
                    "emotional_anchors": scenario_data["emotional_anchors"],
                    "long_term_context": scenario_data["long_term_context"],
                    "has_sufficient_content": True,
                    "input_analysis": {
                        "emotional_content": True,
                        "visual_content": True,
                        "richness_score": 3,
                    },
                }

            # Temporarily replace the method
            original_method = self.prompt_builder.build_image_prompt_context
            self.prompt_builder.build_image_prompt_context = mock_build_context

            # Generate the image
            result = await self.emotion_visualizer.create_emotional_image(
                user_id="demo_user",
                user_input=scenario_data["input_context"],
                include_long_term=True,
                save_locally=False,  # We'll save manually
                identified_emotion=scenario_data["identified_emotion"],
            )

            # Restore original method
            self.prompt_builder.build_image_prompt_context = original_method

            if result["success"]:
                # Save the image
                filename = (
                    f"{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                filepath = self.output_dir / filename

                # Decode and save the image
                image_data = base64.b64decode(result["image_data"])
                with open(filepath, "wb") as f:
                    f.write(image_data)

                result["saved_path"] = str(filepath)

                # Print results
                print(f"✅ SUCCESS!")
                print(f"📝 User Input: {scenario_data['input_context']}")
                print(f"🎨 Visual Prompt: {result['visual_prompt']}")
                print(f"😊 Emotion Type: {result['emotion_type']}")
                print(f"💾 Saved to: {filepath}")
                print(f"🔧 Model: {result['model_used']}")

            else:
                print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

            return result

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {"success": False, "error": str(e)}

    async def run_demo(self):
        """Run the complete demo with multiple scenarios."""

        print("\n" + "🎨" * 20)
        print("REAL IMAGE GENERATION DEMO")
        print("🎨" * 20)
        print(f"Images will be saved to: {self.output_dir.absolute()}")

        scenarios = [
            "overwhelmed_at_work",
            "hopeful_recovery",
            "nostalgic_memory",
            "racing_thoughts",
        ]

        results = {}

        for scenario in scenarios:
            try:
                result = await self.generate_image_for_scenario(scenario)
                results[scenario] = result

                # Small delay between generations to be respectful to APIs
                await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Failed to generate image for {scenario}: {e}")
                results[scenario] = {"success": False, "error": str(e)}

        # Summary
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")

        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)

        print(f"✅ Successful generations: {successful}/{total}")

        for scenario, result in results.items():
            if result.get("success"):
                print(f"🖼️  {scenario}: {result.get('saved_path', 'N/A')}")
            else:
                print(f"❌ {scenario}: {result.get('error', 'Failed')}")

        print(f"\n📁 All images saved to: {self.output_dir.absolute()}")
        return results


# Standalone function for easy testing
async def run_real_image_generation_demo():
    """Run the real image generation demo."""
    demo = RealImageGenerationDemo()
    return await demo.run_demo()


# For running directly
if __name__ == "__main__":
    asyncio.run(run_real_image_generation_demo())
