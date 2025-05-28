"""
API endpoints for image generation service.
Handles requests to create visual representations of user emotions and ideas.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from ..services.image_generation import EmotionVisualizer, ImageGenerator, PromptBuilder
from ..services.memory.storage.redis_store import RedisStore
from ..services.memory.storage.vector_store import VectorStore


# Initialize router
router = APIRouter(prefix="/api/image-generation", tags=["image-generation"])


# Request/Response models
class ImageGenerationRequest(BaseModel):
    user_id: str
    user_input: str
    include_long_term_memory: bool = False
    save_locally: bool = False
    identified_emotion: Optional[str] = None


class ImageValidationRequest(BaseModel):
    user_id: str
    user_input: str


class ImageGenerationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded image
    image_format: Optional[str] = None
    visual_prompt: Optional[str] = None
    emotion_type: Optional[str] = None
    context_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    needs_more_input: Optional[bool] = None


class ImageValidationResponse(BaseModel):
    suitable: bool
    confidence: str
    analysis: Dict[str, Any]
    recommendation: str
    error: Optional[str] = None


class GenerationStatusResponse(BaseModel):
    user_id: str
    service_available: bool
    estimated_generation_time: str


# Dependency injection
async def get_emotion_visualizer() -> EmotionVisualizer:
    """Get configured emotion visualizer instance."""

    # Initialize image generator (requires HF_TOKEN env var)
    try:
        image_generator = ImageGenerator()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail="Image generation service not properly configured. Missing Hugging Face token.",
        )

    # Initialize the emotion visualizer with MemoryService-based components
    # PromptBuilder now uses MemoryService internally for consistent memory access
    prompt_builder = PromptBuilder()

    # For now, we'll need to pass the LLM client
    # This should be injected from your existing LLM setup
    llm_client = None  # TODO: Inject your actual LLM client here

    return EmotionVisualizer(prompt_builder, image_generator, llm_client)


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_emotional_image(
    request: ImageGenerationRequest,
    emotion_visualizer: EmotionVisualizer = Depends(get_emotion_visualizer),
):
    """
    Generate an image representation of user's emotional state or ideas.

    This endpoint takes user input and creates a visual artwork that represents
    their emotions, thoughts, or described imagery using AI image generation.
    """

    try:
        result = await emotion_visualizer.create_emotional_image(
            user_id=request.user_id,
            user_input=request.user_input,
            include_long_term=request.include_long_term_memory,
            save_locally=request.save_locally,
            identified_emotion=request.identified_emotion,
        )

        return ImageGenerationResponse(
            success=result["success"],
            message=result.get("message"),
            image_data=result.get("image_data"),
            image_format=result.get("image_format"),
            visual_prompt=result.get("visual_prompt"),
            emotion_type=result.get("emotion_type"),
            context_analysis=result.get("context_analysis"),
            created_at=result.get("created_at"),
            needs_more_input=result.get("needs_more_input", False),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate image: {str(e)}"
        )


@router.post("/validate", response_model=ImageValidationResponse)
async def validate_input_for_visualization(
    request: ImageValidationRequest,
    emotion_visualizer: EmotionVisualizer = Depends(get_emotion_visualizer),
):
    """
    Validate if user input is suitable for image generation.

    This endpoint quickly checks if the provided user input contains enough
    emotional or visual content to generate a meaningful image representation.
    """

    try:
        result = await emotion_visualizer.validate_user_input_for_visualization(
            user_id=request.user_id, user_input=request.user_input
        )

        return ImageValidationResponse(
            suitable=result["suitable"],
            confidence=result.get("confidence", "unknown"),
            analysis=result.get("analysis", {}),
            recommendation=result.get("recommendation", ""),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate input: {str(e)}"
        )


@router.get("/status/{user_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    user_id: str,
    emotion_visualizer: EmotionVisualizer = Depends(get_emotion_visualizer),
):
    """
    Get the status of image generation service for a user.

    Returns information about service availability and estimated generation times.
    """

    try:
        result = await emotion_visualizer.get_generation_status(user_id)

        return GenerationStatusResponse(
            user_id=result["user_id"],
            service_available=result["service_available"],
            estimated_generation_time=result["estimated_generation_time"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get generation status: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for image generation service."""

    try:
        # Quick check that HF token is available
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            return {
                "status": "degraded",
                "message": "Hugging Face token not configured",
                "timestamp": datetime.utcnow().isoformat(),
            }

        return {
            "status": "healthy",
            "message": "Image generation service is operational",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Service error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Additional utility endpoints


@router.post("/quick-generate")
async def quick_generate_image(
    user_input: str,
    user_id: str = "anonymous",
    emotion_visualizer: EmotionVisualizer = Depends(get_emotion_visualizer),
):
    """
    Quick image generation endpoint for testing purposes.

    Generates an image with minimal context gathering for faster results.
    """

    try:
        # Validate input first
        validation = await emotion_visualizer.validate_user_input_for_visualization(
            user_id, user_input
        )

        if not validation["suitable"]:
            return {
                "success": False,
                "message": validation["recommendation"],
                "validation": validation,
            }

        # Generate with minimal context
        result = await emotion_visualizer.create_emotional_image(
            user_id=user_id,
            user_input=user_input,
            include_long_term=False,  # Skip long-term for speed
            save_locally=False,
        )

        return {
            "success": result["success"],
            "image_data": result.get("image_data"),
            "visual_prompt": result.get("visual_prompt"),
            "emotion_type": result.get("emotion_type"),
            "message": result.get("message"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Quick generation failed: {str(e)}"
        )
