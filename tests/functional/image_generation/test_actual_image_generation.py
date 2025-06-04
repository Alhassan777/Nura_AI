#!/usr/bin/env python3
"""
Test Actual Image Generation - End-to-End Real Image Creation
This script tests the complete image generation pipeline by actually creating images.
"""

import sys
import os
import asyncio
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from backend.services.image_generation.emotion_visualizer import EmotionVisualizer
    from backend.services.image_generation.image_generator import ImageGenerator
    from backend.services.image_generation.prompt_builder import PromptBuilder
    from backend.utils.database import get_database_manager
    from backend.models import GeneratedImage, User
    import uuid

    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class SimpleLLMClient:
    """Simple LLM client wrapper for testing."""

    def __init__(self):
        # Configure Google AI
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Create model with default config
        self.metadata_config = genai.types.GenerationConfig(
            temperature=0.5,
            top_p=0.85,
            top_k=30,
            max_output_tokens=1024,
            candidate_count=1,
        )

        self.model = genai.GenerativeModel(
            "gemini-1.5-pro",  # Use a stable model
            generation_config=self.metadata_config,
        )


class RealImageGenerationTest:
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.results = []

    async def test_actual_image_generation(self):
        """Test actual image generation with real API calls."""
        print("\n🎨 Testing Actual Image Generation...")

        try:
            # Initialize the emotion visualizer with LLM client
            llm_client = SimpleLLMClient()
            emotion_visualizer = EmotionVisualizer(llm_client=llm_client)

            # Test with a rich emotional input
            test_input = "I'm feeling incredibly peaceful and calm today. The sunset over the ocean reminds me of warm golden honey flowing over smooth stones. I can almost hear the gentle waves and feel the soft sea breeze on my face."

            print(f"📝 Input: {test_input}")
            print("🔄 Generating image... (this may take 30-60 seconds)")

            # Actually generate an image
            result = await emotion_visualizer.create_emotional_image(
                user_id=self.test_user_id,
                user_input=test_input,
                save_locally=True,  # Save to local file system too
                name="Test Peaceful Sunset",
            )

            if result.get("success"):
                print("✅ Image generation successful!")

                # Verify the image data
                image_data = result.get("image_data")
                if (
                    image_data and len(image_data) > 100
                ):  # Should be substantial base64 data
                    print(f"📊 Image data length: {len(image_data)} characters")

                    # Decode and save the image locally for verification
                    try:
                        image_bytes = base64.b64decode(image_data)

                        # Save with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"test_generated_image_{timestamp}.png"

                        with open(filename, "wb") as f:
                            f.write(image_bytes)

                        print(f"🖼️  Image saved locally as: {filename}")
                        print(f"📏 Image file size: {len(image_bytes)} bytes")

                        # Display additional generation details
                        print(f"🎭 Detected emotion: {result.get('emotion_type')}")
                        print(
                            f"📝 Visual prompt used: {result.get('visual_prompt', '')[:100]}..."
                        )
                        print(f"🤖 Model used: {result.get('model_used')}")
                        print(
                            f"⚙️  Generation params: {result.get('generation_params')}"
                        )

                        self.results.append(
                            {
                                "test": "Actual Image Generation",
                                "status": "PASS",
                                "image_size_bytes": len(image_bytes),
                                "image_data_length": len(image_data),
                                "emotion_type": result.get("emotion_type"),
                                "model_used": result.get("model_used"),
                                "saved_file": filename,
                            }
                        )

                        return True

                    except Exception as e:
                        print(f"❌ Error processing image data: {e}")
                        return False
                else:
                    print("❌ No valid image data received")
                    return False
            else:
                print(
                    f"❌ Image generation failed: {result.get('message', 'Unknown error')}"
                )
                if result.get("error"):
                    print(f"🔍 Error type: {result.get('error')}")
                return False

        except Exception as e:
            print(f"❌ Exception during image generation: {e}")
            self.results.append(
                {"test": "Actual Image Generation", "status": "FAIL", "error": str(e)}
            )
            return False

    async def test_huggingface_api_direct(self):
        """Test direct Hugging Face API call to verify connectivity."""
        print("\n🌐 Testing Direct Hugging Face API...")

        try:
            image_generator = ImageGenerator()

            # Simple test prompt
            test_prompt = (
                "A serene sunset over calm ocean waters, peaceful and beautiful"
            )

            print(f"📝 Test prompt: {test_prompt}")
            print("🔄 Calling Hugging Face FLUX.1-dev API...")

            result = await image_generator.generate_image_from_prompt(test_prompt)

            if result.get("success"):
                print("✅ Direct API call successful!")
                print(
                    f"📊 Response size: {len(result.get('image_data', ''))} characters"
                )
                print(f"🎨 Format: {result.get('image_format')}")
                print(f"🤖 Model: {result.get('model')}")

                self.results.append(
                    {
                        "test": "Direct HuggingFace API",
                        "status": "PASS",
                        "response_size": len(result.get("image_data", "")),
                        "format": result.get("image_format"),
                        "model": result.get("model"),
                    }
                )
                return True
            else:
                print(f"❌ API call failed: {result.get('message')}")
                print(f"🔍 Error: {result.get('error')}")
                self.results.append(
                    {
                        "test": "Direct HuggingFace API",
                        "status": "FAIL",
                        "error": result.get("error"),
                        "message": result.get("message"),
                    }
                )
                return False

        except Exception as e:
            print(f"❌ Exception during API test: {e}")
            return False

    async def test_different_emotions(self):
        """Test image generation with different emotional inputs."""
        print("\n🎭 Testing Different Emotional Inputs...")

        test_cases = [
            {
                "emotion": "energetic",
                "input": "I'm bursting with energy! Like lightning dancing through storm clouds, electric and vibrant!",
                "name": "Electric Energy",
            },
            {
                "emotion": "mysterious",
                "input": "There's something mysterious in the shadows, ancient secrets whispered by moonlight through misty forests.",
                "name": "Moonlight Mystery",
            },
            {
                "emotion": "hopeful",
                "input": "Despite everything, I feel hopeful. Like the first spring flower breaking through winter snow, full of possibility.",
                "name": "Spring Hope",
            },
        ]

        emotion_visualizer = EmotionVisualizer(llm_client=SimpleLLMClient())
        successful_generations = 0

        for i, case in enumerate(test_cases):
            print(f"\n🎨 Test {i+1}/3: {case['emotion'].title()} emotion")
            print(f"📝 Input: {case['input'][:60]}...")

            try:
                result = await emotion_visualizer.create_emotional_image(
                    user_id=self.test_user_id,
                    user_input=case["input"],
                    name=case["name"],
                )

                if result.get("success"):
                    print(f"✅ {case['emotion'].title()} image generated successfully")
                    detected = result.get("emotion_type", "unknown")
                    print(f"🎭 Detected emotion: {detected}")
                    successful_generations += 1

                    # Save a sample of each type
                    if i == 0:  # Save first one as example
                        image_data = result.get("image_data")
                        if image_data:
                            image_bytes = base64.b64decode(image_data)
                            filename = f"test_{case['emotion']}_image.png"
                            with open(filename, "wb") as f:
                                f.write(image_bytes)
                            print(f"🖼️  Sample saved as: {filename}")
                else:
                    print(
                        f"❌ {case['emotion'].title()} generation failed: {result.get('message')}"
                    )

            except Exception as e:
                print(f"❌ Error generating {case['emotion']} image: {e}")

        success_rate = successful_generations / len(test_cases)
        print(
            f"\n📊 Emotion Generation Results: {successful_generations}/{len(test_cases)} successful ({success_rate:.1%})"
        )

        self.results.append(
            {
                "test": "Different Emotions",
                "status": "PASS" if success_rate >= 0.5 else "FAIL",
                "successful_generations": successful_generations,
                "total_attempts": len(test_cases),
                "success_rate": success_rate,
            }
        )

        return success_rate >= 0.5

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 REAL IMAGE GENERATION TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)

        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📊 Total: {total}")

        if passed == total:
            print("\n🎉 ALL REAL IMAGE GENERATION TESTS PASSED!")
            print("🚀 The pipeline can successfully create actual images!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed - review issues above")

        # Save detailed results
        with open("real_image_generation_results.json", "w") as f:
            json.dump(
                {
                    "summary": {
                        "passed": passed,
                        "failed": total - passed,
                        "total": total,
                        "all_tests_passed": passed == total,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "detailed_results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed results saved to: real_image_generation_results.json")


async def main():
    """Run all real image generation tests."""
    print("🎨 Starting Real Image Generation Tests")
    print("=" * 70)

    tester = RealImageGenerationTest()

    # Test 1: Direct API connectivity
    api_success = await tester.test_huggingface_api_direct()

    if api_success:
        # Test 2: Full pipeline with actual image generation
        await tester.test_actual_image_generation()

        # Test 3: Multiple emotion types
        await tester.test_different_emotions()
    else:
        print("\n⚠️  Skipping further tests due to API connectivity issues")
        print("🔍 Check your HF_TOKEN environment variable and internet connection")

    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
