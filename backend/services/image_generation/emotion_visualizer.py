"""
Main emotion visualizer that orchestrates the entire process of converting
user emotions and ideas into visual representations.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .prompt_builder import PromptBuilder
from .image_generator import ImageGenerator
from ..memory.storage.redis_store import RedisStore
from ..memory.storage.vector_store import VectorStore
from models import GeneratedImage
from utils.database import get_db


class EmotionVisualizer:
    """Main service for converting emotions and ideas into visual art."""

    def __init__(
        self,
        prompt_builder: PromptBuilder = None,
        image_generator: ImageGenerator = None,
        llm_client: Any = None,  # LLM client for processing prompts
    ):
        # Use provided components or create defaults
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.image_generator = image_generator or ImageGenerator()
        self.llm_client = llm_client

    async def create_emotional_image(
        self,
        user_id: str,
        user_input: str,
        include_long_term: bool = False,
        save_locally: bool = False,
        identified_emotion: Optional[str] = None,
        name: Optional[str] = None,  # New: user-provided name
    ) -> Dict[str, Any]:
        """
        Create an image representation of user's emotional state or ideas.

        Args:
            user_id: The user's unique identifier
            user_input: Current user input/message
            include_long_term: Whether to include long-term memory context
            save_locally: Whether to save the generated image locally
            identified_emotion: Optional pre-identified emotion to guide generation
            name: Optional user-provided name for the image

        Returns:
            Dictionary containing image generation results and metadata
        """

        try:
            # Step 1: Build comprehensive context
            context = await self.prompt_builder.build_image_prompt_context(
                user_id, user_input, include_long_term, identified_emotion
            )

            # Step 2: Check if we have sufficient content
            if not context["has_sufficient_content"]:
                return {
                    "success": False,
                    "needs_more_input": True,
                    "message": "I'd love to create a visual representation of what you're feeling or thinking about, but I need a bit more to work with. Could you share what's on your mind, how you're feeling, or perhaps describe any images, colors, or places that come to mind?",
                    "context_analysis": context["input_analysis"],
                }

            # Step 3: Generate the visual prompt and name using LLM
            visual_prompt_result = await self._generate_visual_prompt_with_name(context)

            if not visual_prompt_result["success"]:
                return visual_prompt_result

            visual_prompt = visual_prompt_result["visual_prompt"]
            suggested_name = visual_prompt_result.get("suggested_name")
            # Use user-provided name if given, else LLM-suggested name
            image_name = name or suggested_name

            # Step 4: Determine emotion type for generation parameters
            emotion_type = self._analyze_emotion_type(context)
            generation_params = self.image_generator.get_recommended_params_for_emotion(
                emotion_type
            )

            # Step 5: Generate the image
            image_result = await self.image_generator.generate_with_retry(
                visual_prompt, custom_params=generation_params
            )

            if not image_result["success"]:
                return {
                    "success": False,
                    "error": "image_generation_failed",
                    "message": f"Failed to generate image: {image_result.get('message', 'Unknown error')}",
                    "visual_prompt": visual_prompt,
                    "context_used": context,
                }

            # Step 6: Save locally if requested
            saved_path = None
            if save_locally:
                filename = (
                    f"emotion_art_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                saved_path = await self.image_generator.save_image_locally(
                    image_result["image_data"], filename
                )

            # Step 7: Store generated image in the database
            try:
                with get_db() as db:
                    generated_image = GeneratedImage(
                        user_id=user_id,
                        prompt=visual_prompt,
                        image_data=image_result["image_data"],
                        image_format=image_result.get("image_format", "png"),
                        name=image_name,
                        image_metadata={
                            "emotion_type": emotion_type,
                            "generation_params": generation_params,
                            "context_analysis": context["input_analysis"],
                            "model_used": image_result["model"],
                        },
                    )
                    db.add(generated_image)
                    db.commit()
            except Exception as db_exc:
                # Log but do not fail the main flow
                print(f"[WARN] Failed to store generated image in DB: {db_exc}")

            # Step 8: Return complete result
            return {
                "success": True,
                "image_data": image_result["image_data"],
                "image_format": image_result["image_format"],
                "visual_prompt": visual_prompt,
                "emotion_type": emotion_type,
                "generation_params": generation_params,
                "context_analysis": context["input_analysis"],
                "saved_path": saved_path,
                "model_used": image_result["model"],
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": "unexpected_error",
                "message": f"An unexpected error occurred: {str(e)}",
            }

    async def _generate_visual_prompt_with_name(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a visual prompt and a suggested name using the LLM and context data."""
        try:
            # Format the prompt template with context, requesting a name
            formatted_prompt = self.prompt_builder.format_prompt_template(context)
            prompt_with_name = (
                formatted_prompt
                + "\n\nAdditionally, provide a short, descriptive name for this image (max 6 words) on a new line starting with 'Name: '."
            )
            response = await asyncio.to_thread(
                self.llm_client.model.generate_content,
                prompt_with_name,
                generation_config=self.llm_client.metadata_config,
            )
            if not response or not response.text or len(response.text.strip()) < 20:
                return {
                    "success": False,
                    "error": "llm_response_insufficient",
                    "message": "LLM failed to generate sufficient visual description",
                }
            # Parse the response for prompt and name
            lines = response.text.strip().split("\n")
            visual_prompt = ""
            suggested_name = None
            for line in lines:
                if line.strip().lower().startswith("name:"):
                    suggested_name = line.split(":", 1)[-1].strip()
                else:
                    visual_prompt += line.strip() + " "
            visual_prompt = visual_prompt.strip()
            return {
                "success": True,
                "visual_prompt": visual_prompt,
                "suggested_name": suggested_name,
                "raw_llm_response": response.text,
            }
        except Exception as e:
            return {
                "success": False,
                "error": "llm_error",
                "message": f"Error generating visual prompt and name: {str(e)}",
            }

    def _clean_visual_prompt(self, llm_response: str) -> str:
        """Clean and format the LLM response for image generation."""

        # Remove common prefixes/suffixes
        response = llm_response.strip()

        # Remove quotes if they wrap the entire response
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]

        # Remove instruction artifacts
        unwanted_phrases = [
            "✏️ GENERATE YOUR RESPONSE:",
            "Here's the visual scene:",
            "Visual prompt:",
            "Scene description:",
            "The image shows:",
            "Generate:",
            "Output:",
        ]

        for phrase in unwanted_phrases:
            response = response.replace(phrase, "").strip()

        # Ensure it ends properly
        if not response.endswith("."):
            response += "."

        return response

    def _analyze_emotion_type(self, context: Dict[str, Any]) -> str:
        """Analyze the overall emotional tone to determine generation parameters."""

        input_text = context["input_context"].lower()
        short_term = context["short_term_context"].lower()

        # Combine text for analysis
        combined_text = f"{input_text} {short_term}"

        # Define emotion keywords
        emotion_mappings = {
            "calm": [
                "calm",
                "peaceful",
                "serene",
                "quiet",
                "still",
                "gentle",
                "soft",
                "tranquil",
            ],
            "energetic": [
                "excited",
                "energetic",
                "dynamic",
                "vibrant",
                "active",
                "intense",
                "powerful",
            ],
            "mysterious": [
                "mysterious",
                "unknown",
                "hidden",
                "secret",
                "fog",
                "mist",
                "shadow",
                "unclear",
            ],
            "hopeful": [
                "hope",
                "hopeful",
                "bright",
                "light",
                "sunrise",
                "future",
                "possibility",
                "optimistic",
            ],
            "melancholic": [
                "sad",
                "melancholy",
                "gray",
                "heavy",
                "dark",
                "loss",
                "nostalgic",
                "wistful",
            ],
        }

        # Score each emotion type
        emotion_scores = {}
        for emotion_type, keywords in emotion_mappings.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            emotion_scores[emotion_type] = score

        # Return the emotion with highest score, default to "mysterious"
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)

        return "mysterious"

    async def get_generation_status(self, user_id: str) -> Dict[str, Any]:
        """Get the status of image generation for a user."""

        # This could be extended to track generation progress
        # For now, return basic status
        return {
            "user_id": user_id,
            "service_available": True,
            "estimated_generation_time": "30-60 seconds",
        }

    async def validate_user_input_for_visualization(
        self, user_id: str, user_input: str
    ) -> Dict[str, Any]:
        """
        Validate if user input is suitable for visualization without full processing.

        Args:
            user_id: User identifier
            user_input: User's input text

        Returns:
            Validation result with recommendations
        """

        try:
            # Quick context check (without expensive operations)
            basic_context = {
                "input_context": user_input,
                "short_term_context": "",  # Skip for validation
                "emotional_anchors": "",  # Skip for validation
                "long_term_context": "",  # Skip for validation
            }

            # Analyze input content
            input_analysis = self.prompt_builder._analyze_input_content(user_input)

            # Quick check for sufficient content
            has_content = self.prompt_builder._has_sufficient_visual_content(
                user_input, "", ""
            )

            if has_content:
                return {
                    "suitable": True,
                    "confidence": (
                        "high" if input_analysis["richness_score"] >= 2 else "medium"
                    ),
                    "analysis": input_analysis,
                    "recommendation": "Input is suitable for image generation.",
                }
            else:
                return {
                    "suitable": False,
                    "confidence": "low",
                    "analysis": input_analysis,
                    "recommendation": "Please share more about your feelings, thoughts, or any visual imagery that comes to mind.",
                }

        except Exception as e:
            return {
                "suitable": False,
                "error": str(e),
                "recommendation": "Unable to validate input. Please try again.",
            }
