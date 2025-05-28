"""
Chat API Module
Handles chat interactions and mental health assistant endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Import services
from services.memory.memoryService import MemoryService
from services.memory.assistant.mental_health_assistant import MentalHealthAssistant

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
memory_service = MemoryService()
mental_health_assistant = MentalHealthAssistant()


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    include_memory: bool = True


class ChatResponse(BaseModel):
    response: str
    crisis_level: str
    crisis_explanation: str
    resources_provided: List[str]
    coping_strategies: List[str]
    memory_stored: bool
    timestamp: str
    configuration_warning: Optional[bool] = None
    configuration_status: Optional[Dict[str, Any]] = None


# Helper function
def get_configuration_status() -> Dict[str, Any]:
    """Get current configuration status for API responses."""
    from services.memory.config import Config

    missing_required = []
    missing_optional = []

    # Check required configs
    if not Config.GOOGLE_API_KEY:
        missing_required.append("GOOGLE_API_KEY")

    # Check vector database specific requirements
    if Config.VECTOR_DB_TYPE == "pinecone" or Config.USE_PINECONE:
        if not Config.PINECONE_API_KEY:
            missing_required.append("PINECONE_API_KEY")

    has_issues = bool(missing_required or missing_optional)

    return {
        "has_configuration_issues": has_issues,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "status": "degraded" if has_issues else "fully_configured",
        "message": (
            "⚠️ Service running with missing configurations. Some features may not work as expected."
            if has_issues
            else "✅ Service fully configured"
        ),
    }


# Chat endpoints
@router.post("/assistant", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest, user_id: str = Query(..., description="User ID")
):
    """Chat with the mental health assistant, with memory integration."""
    try:
        # Get configuration status
        config_status = get_configuration_status()

        # Get memory context if requested
        memory_context = None
        if request.include_memory:
            memory_context = await memory_service.get_memory_context(
                user_id=user_id, query=request.message
            )

        # Generate assistant response
        assistant_response = await mental_health_assistant.generate_response(
            user_message=request.message, memory_context=memory_context, user_id=user_id
        )

        # Store the user message in memory
        user_memory = await memory_service.process_memory(
            user_id=user_id,
            content=request.message,
            type="user_message",
            metadata={"source": "chat_interface"},
        )

        # Store the assistant response in memory
        assistant_memory = await memory_service.process_memory(
            user_id=user_id,
            content=assistant_response["response"],
            type="assistant_response",
            metadata={
                "source": "chat_interface",
                "crisis_level": assistant_response["crisis_level"],
                "resources_provided": assistant_response["resources_provided"],
                "coping_strategies": assistant_response["coping_strategies"],
            },
        )

        return ChatResponse(
            response=assistant_response["response"],
            crisis_level=assistant_response["crisis_level"],
            crisis_explanation=assistant_response["crisis_explanation"],
            resources_provided=assistant_response["resources_provided"],
            coping_strategies=assistant_response["coping_strategies"],
            memory_stored=user_memory is not None or assistant_memory is not None,
            timestamp=assistant_response["timestamp"].isoformat(),
            configuration_warning=assistant_response.get(
                "configuration_warning", False
            ),
            configuration_status=(
                config_status if config_status["has_configuration_issues"] else None
            ),
        )

    except Exception as e:
        config_status = get_configuration_status()
        logger.error(f"Error in chat_with_assistant: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "configuration_status": config_status,
                "message": "Service error occurred. Please check configuration if issues persist.",
            },
        )


@router.get("/crisis-resources")
async def get_crisis_resources():
    """Get immediate crisis resources."""
    try:
        return await mental_health_assistant.provide_crisis_resources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
