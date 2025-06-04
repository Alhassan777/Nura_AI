"""
Assistant Service API - Mental health assistant functionality.
Provides AI-powered mental health support and crisis detection.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Internal imports
from .mental_health_assistant import MentalHealthAssistant

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/assistant", tags=["assistant"])

# Initialize assistant
mental_health_assistant = MentalHealthAssistant()


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    memory_context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    crisis_level: str
    crisis_explanation: str
    resources_provided: List[str]
    coping_strategies: List[str]
    session_metadata: Dict[str, Any]
    crisis_flag: bool
    configuration_warning: Optional[bool] = None
    timestamp: str


class CrisisAssessmentRequest(BaseModel):
    message: str


class CrisisAssessmentResponse(BaseModel):
    level: str
    explanation: str
    resources: Dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """Generate a mental health assistant response."""
    try:
        # Convert memory context if provided
        memory_context = None
        if request.memory_context:
            # This would convert the dict to MemoryContext object
            # For now, we'll pass None and let the assistant handle it
            pass

        response_data = await mental_health_assistant.generate_response(
            user_message=request.message,
            memory_context=memory_context,
            user_id=request.user_id,
        )

        return ChatResponse(
            response=response_data["response"],
            crisis_level=response_data["crisis_level"],
            crisis_explanation=response_data["crisis_explanation"],
            resources_provided=response_data["resources_provided"],
            coping_strategies=response_data["coping_strategies"],
            session_metadata=response_data["session_metadata"],
            crisis_flag=response_data["crisis_flag"],
            configuration_warning=response_data.get("configuration_warning"),
            timestamp=response_data["timestamp"].isoformat(),
        )

    except Exception as e:
        logger.error(f"Error generating assistant response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crisis-assessment", response_model=CrisisAssessmentResponse)
async def assess_crisis(request: CrisisAssessmentRequest):
    """Assess crisis level of a message."""
    try:
        crisis_assessment = await mental_health_assistant._assess_crisis_level(
            request.message
        )
        crisis_resources = await mental_health_assistant.provide_crisis_resources()

        return CrisisAssessmentResponse(
            level=crisis_assessment["level"],
            explanation=crisis_assessment["explanation"],
            resources=crisis_resources,
        )

    except Exception as e:
        logger.error(f"Error assessing crisis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crisis-resources")
async def get_crisis_resources():
    """Get crisis resources and emergency contacts."""
    try:
        return await mental_health_assistant.provide_crisis_resources()
    except Exception as e:
        logger.error(f"Error getting crisis resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(router, host="0.0.0.0", port=8000)
