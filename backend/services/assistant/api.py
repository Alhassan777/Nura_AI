"""
Mental Health Assistant API - Core chat and crisis assessment functionality.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .mental_health_assistant import MentalHealthAssistant
from utils.auth import get_current_user_id

import logging

logger = logging.getLogger(__name__)

# Initialize router and assistant
router = APIRouter(prefix="/assistant", tags=["assistant"])
mental_health_assistant = MentalHealthAssistant()


# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation context")
    memory_context: Optional[Dict[str, Any]] = Field(None, description="Memory context")


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
    memory_stored: bool
    schedule_analysis: Optional[Dict[str, Any]] = None
    action_plan_analysis: Optional[Dict[str, Any]] = None


class CrisisAssessmentRequest(BaseModel):
    message: str


class CrisisAssessmentResponse(BaseModel):
    level: str
    explanation: str
    resources: Dict[str, Any]


# API Endpoints


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest, user_id: str = Depends(get_current_user_id)
):
    """
    Main chat endpoint for mental health assistance.
    Provides crisis assessment, coping strategies, and resource recommendations.
    """
    try:
        # Process the message through the assistant extractor
        response_data = await mental_health_assistant.process_message(
            user_message=request.message,
            user_id=user_id,
            conversation_id=request.conversation_id,
            memory_context=request.memory_context,
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
            timestamp=datetime.utcnow().isoformat(),
            memory_stored=response_data["memory_stored"],
            schedule_analysis=response_data.get("schedule_analysis"),
            action_plan_analysis=response_data.get("action_plan_analysis"),
        )

    except Exception as e:
        logger.error(f"Error in assistant chat for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/crisis-assessment", response_model=CrisisAssessmentResponse)
async def assess_crisis(request: CrisisAssessmentRequest):
    """
    Dedicated crisis assessment endpoint.
    Evaluates the severity of a user's mental health crisis.
    """
    try:
        assessment = await mental_health_assistant._assess_crisis_level(request.message)
        crisis_resources = await mental_health_assistant.provide_crisis_resources()

        return CrisisAssessmentResponse(
            level=assessment["level"],
            explanation=assessment["explanation"],
            resources=crisis_resources,
        )

    except Exception as e:
        logger.error(f"Error in crisis assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to assess crisis level")


@router.get("/crisis-resources")
async def get_crisis_resources():
    """Get comprehensive crisis intervention resources."""
    return {
        "hotlines": [
            {
                "name": "National Suicide Prevention Lifeline",
                "number": "988",
                "available": "24/7",
            },
            {
                "name": "Crisis Text Line",
                "number": "Text HOME to 741741",
                "available": "24/7",
            },
            {
                "name": "SAMHSA National Helpline",
                "number": "1-800-662-4357",
                "available": "24/7",
            },
        ],
        "immediate_actions": [
            "Call 911 or go to your nearest emergency room if in immediate danger",
            "Reach out to a trusted friend, family member, or mental health professional",
            "Remove any means of self-harm from your immediate environment",
            "Stay with someone or ask someone to stay with you",
            "Consider calling a crisis hotline to talk through your feelings",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(router, host="0.0.0.0", port=8000)
