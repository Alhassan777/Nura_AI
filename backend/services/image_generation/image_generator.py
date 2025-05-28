"""
Image generation service using Hugging Face FLUX.1-dev model.
Converts emotional and visual prompts into images.
"""

import asyncio
import base64
import httpx
import os
from typing import Dict, Any, Optional
import json
from io import BytesIO


class ImageGenerator:
    """Handles image generation using Hugging Face FLUX.1-dev model."""

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize the image generator.

        Args:
            hf_token: Hugging Face API token. If None, will look for HF_TOKEN env var.
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        if not self.hf_token:
            raise ValueError(
                "Hugging Face token is required. Set HF_TOKEN environment variable."
            )

        # FLUX.1-dev API endpoint
        self.api_url = (
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
        )

        self.headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
        }

        # Default generation parameters
        self.default_params = {
            "inputs": "",
            "parameters": {
                "guidance_scale": 7.5,
                "num_inference_steps": 50,
                "width": 1024,
                "height": 1024,
                "seed": None,  # Will be randomized if not provided
            },
        }

    async def generate_image_from_prompt(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an image from a text prompt using FLUX.1-dev.

        Args:
            prompt: The text prompt describing the image to generate
            negative_prompt: Optional negative prompt (what to avoid)
            custom_params: Optional custom parameters for generation

        Returns:
            Dictionary containing image data and metadata
        """

        # Prepare the payload
        payload = self.default_params.copy()
        payload["inputs"] = self._enhance_prompt(prompt, negative_prompt)

        # Apply custom parameters if provided
        if custom_params:
            payload["parameters"].update(custom_params)

        # Remove None values from parameters as Hugging Face API doesn't accept them
        payload["parameters"] = {
            k: v for k, v in payload["parameters"].items() if v is not None
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.api_url, headers=self.headers, json=payload
                )

                if response.status_code == 200:
                    # FLUX returns image bytes directly
                    image_bytes = response.content

                    # Convert to base64 for easy handling
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                    return {
                        "success": True,
                        "image_data": image_base64,
                        "image_format": "png",
                        "prompt_used": payload["inputs"],
                        "parameters": payload["parameters"],
                        "model": "FLUX.1-dev",
                    }

                elif response.status_code == 503:
                    # Model is loading, try again
                    return {
                        "success": False,
                        "error": "model_loading",
                        "message": "The FLUX model is currently loading. Please try again in a few moments.",
                        "retry_after": 20,
                    }

                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    return {
                        "success": False,
                        "error": "api_error",
                        "message": error_msg,
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "timeout",
                "message": "Image generation timed out. Please try again.",
            }

        except Exception as e:
            return {
                "success": False,
                "error": "unexpected_error",
                "message": f"Unexpected error: {str(e)}",
            }

    def _enhance_prompt(
        self, prompt: str, negative_prompt: Optional[str] = None
    ) -> str:
        """
        Enhance the prompt for better FLUX.1-dev results.

        Args:
            prompt: Original prompt
            negative_prompt: Optional negative prompt

        Returns:
            Enhanced prompt string
        """

        # Add quality and style enhancers for FLUX
        style_enhancers = [
            "highly detailed",
            "beautiful composition",
            "soft natural lighting",
            "atmospheric perspective",
            "artistic quality",
        ]

        # Combine original prompt with enhancers
        enhanced_parts = [prompt.strip()]
        enhanced_parts.extend(style_enhancers)

        enhanced_prompt = ", ".join(enhanced_parts)

        # Add negative prompt if provided
        if negative_prompt:
            enhanced_prompt += f" | Negative: {negative_prompt}"

        return enhanced_prompt

    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate image with automatic retry logic for model loading.

        Args:
            prompt: The text prompt
            max_retries: Maximum number of retry attempts
            custom_params: Optional custom parameters

        Returns:
            Dictionary containing image data and metadata
        """

        for attempt in range(max_retries + 1):
            result = await self.generate_image_from_prompt(
                prompt, custom_params=custom_params
            )

            if result["success"]:
                return result

            # If model is loading and we have retries left, wait and try again
            if result.get("error") == "model_loading" and attempt < max_retries:

                wait_time = result.get("retry_after", 20)
                await asyncio.sleep(wait_time)
                continue

            # Return the error if we can't retry or max retries reached
            return result

        return {
            "success": False,
            "error": "max_retries_exceeded",
            "message": f"Failed to generate image after {max_retries} retries.",
        }

    def get_recommended_params_for_emotion(self, emotion_type: str) -> Dict[str, Any]:
        """
        Get recommended generation parameters based on emotion type.

        Args:
            emotion_type: Type of emotion (calm, energetic, mysterious, etc.)

        Returns:
            Dictionary of recommended parameters
        """

        emotion_params = {
            "calm": {
                "guidance_scale": 6.0,
                "num_inference_steps": 40,
                "width": 1024,
                "height": 768,  # Landscape for calming scenes
            },
            "energetic": {
                "guidance_scale": 8.0,
                "num_inference_steps": 45,
                "width": 768,
                "height": 1024,  # Portrait for dynamic scenes
            },
            "mysterious": {
                "guidance_scale": 7.0,
                "num_inference_steps": 55,
                "width": 1024,
                "height": 1024,  # Square for mysterious/abstract
            },
            "hopeful": {
                "guidance_scale": 6.5,
                "num_inference_steps": 40,
                "width": 1024,
                "height": 768,  # Landscape for expansive hope
            },
            "melancholic": {
                "guidance_scale": 7.5,
                "num_inference_steps": 50,
                "width": 768,
                "height": 1024,  # Portrait for introspective mood
            },
        }

        return emotion_params.get(emotion_type, self.default_params["parameters"])

    async def save_image_locally(
        self, image_base64: str, filename: str, directory: str = "generated_images"
    ) -> str:
        """
        Save base64 image to local filesystem.

        Args:
            image_base64: Base64 encoded image data
            filename: Name for the saved file
            directory: Directory to save in

        Returns:
            Path to saved file
        """

        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Decode base64 and save
        image_bytes = base64.b64decode(image_base64)
        filepath = os.path.join(directory, f"{filename}.png")

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return filepath
