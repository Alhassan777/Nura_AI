"""
Image Generation API Module
Handles requests to create visual representations of user emotions and ideas.
SECURE: All endpoints can be secured with JWT authentication if needed.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, field_validator
from datetime import datetime

from .emotion_visualizer import EmotionVisualizer
from .image_generator import ImageGenerator
from .prompt_builder import PromptBuilder
from models import GeneratedImage
from utils.database import get_db
from sqlalchemy.orm import Session
from utils.auth import get_current_user_id

# Import unified authentication system (optional for image generation)
# from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

# Initialize router
router = APIRouter(prefix="/image-generation", tags=["image-generation"])


# Request/Response models
class ImageGenerationRequest(BaseModel):
    user_input: str
    include_long_term_memory: bool = False
    save_locally: bool = False
    identified_emotion: Optional[str] = None
    name: Optional[str] = None  # User can optionally provide a name


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


class GeneratedImageResponse(BaseModel):
    id: str
    user_id: str
    name: Optional[str]
    prompt: str
    image_format: str
    image_data: Optional[str]
    image_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("user_id", mode="before")
    @classmethod
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string if needed."""
        if hasattr(v, "__str__"):
            return str(v)
        return v


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
    prompt_builder = PromptBuilder()

    # For now, we'll need to pass the LLM client
    # This should be injected from your existing LLM setup
    llm_client = None  # TODO: Inject your actual LLM client here

    return EmotionVisualizer(prompt_builder, image_generator, llm_client)


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_emotional_image(
    request: ImageGenerationRequest,
    user_id: str = Depends(get_current_user_id),
    emotion_visualizer: EmotionVisualizer = Depends(get_emotion_visualizer),
):
    """
    Generate an image representation of user's emotional state or ideas.

    This endpoint takes user input and creates a visual artwork that represents
    their emotions, thoughts, or described imagery using AI image generation.
    """

    try:
        result = await emotion_visualizer.create_emotional_image(
            user_id=user_id,
            user_input=request.user_input,
            include_long_term=request.include_long_term_memory,
            save_locally=request.save_locally,
            identified_emotion=request.identified_emotion,
            name=request.name,
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


@router.get("/images", response_model=list[GeneratedImageResponse])
async def list_generated_images(
    user_id: str = Depends(get_current_user_id),
    name: Optional[str] = Query(None),
    prompt: Optional[str] = Query(None),
    emotion_type: Optional[str] = Query(None),
    created_from: Optional[str] = Query(
        None, description="ISO date string: YYYY-MM-DD"
    ),
    created_to: Optional[str] = Query(None, description="ISO date string: YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    List all generated images for the user, with optional fuzzy search (name, prompt), emotion_type, and date range.
    """
    query = db.query(GeneratedImage).filter(GeneratedImage.user_id == user_id)
    if name:
        # Fuzzy search: ilike with wildcards between words
        fuzzy = "%" + "%".join(name.split()) + "%"
        query = query.filter(GeneratedImage.name.ilike(fuzzy))
    if prompt:
        fuzzy = "%" + "%".join(prompt.split()) + "%"
        query = query.filter(GeneratedImage.prompt.ilike(fuzzy))
    if emotion_type:
        query = query.filter(
            GeneratedImage.image_metadata["emotion_type"].astext == emotion_type
        )
    if created_from:
        try:
            dt_from = datetime.fromisoformat(created_from)
            query = query.filter(GeneratedImage.created_at >= dt_from)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid created_from date format. Use YYYY-MM-DD.",
            )
    if created_to:
        try:
            dt_to = datetime.fromisoformat(created_to)
            query = query.filter(GeneratedImage.created_at <= dt_to)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid created_to date format. Use YYYY-MM-DD.",
            )
    images = query.order_by(GeneratedImage.created_at.desc()).all()
    return images


@router.get("/images/{image_id}", response_model=GeneratedImageResponse)
async def get_generated_image(
    image_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific generated image by ID for the user.
    """
    image = (
        db.query(GeneratedImage)
        .filter(GeneratedImage.id == image_id, GeneratedImage.user_id == user_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found or access denied.")
    return image


class UpdateImageNameRequest(BaseModel):
    name: str


@router.patch("/images/{image_id}/name", response_model=GeneratedImageResponse)
async def update_image_name(
    image_id: str,
    req: UpdateImageNameRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Update the name of a generated image (user can only update their own images).
    """
    image = (
        db.query(GeneratedImage)
        .filter(GeneratedImage.id == image_id, GeneratedImage.user_id == user_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found or access denied.")
    image.name = req.name
    db.commit()
    db.refresh(image)
    return image


class UpdateImageMetadataRequest(BaseModel):
    image_metadata: dict


@router.patch("/images/{image_id}/metadata", response_model=GeneratedImageResponse)
async def update_image_metadata(
    image_id: str,
    req: UpdateImageMetadataRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Update the metadata of a generated image (user can only update their own images).
    """
    image = (
        db.query(GeneratedImage)
        .filter(GeneratedImage.id == image_id, GeneratedImage.user_id == user_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found or access denied.")
    image.image_metadata = req.image_metadata
    db.commit()
    db.refresh(image)
    return image


@router.delete("/images/{image_id}", response_model=dict)
async def delete_generated_image(
    image_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Delete a generated image (user can only delete their own images).
    """
    image = (
        db.query(GeneratedImage)
        .filter(GeneratedImage.id == image_id, GeneratedImage.user_id == user_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found or access denied.")
    db.delete(image)
    db.commit()
    return {"success": True, "message": "Image deleted."}
