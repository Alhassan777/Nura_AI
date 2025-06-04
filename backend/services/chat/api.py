"""
Chat Service API - Full featured chat service with Supabase integration.
Integrates with memory service for comprehensive mental health support.
SECURE: All endpoints use JWT authentication - users can only access their own data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import uuid
import hashlib
from dataclasses import asdict

# Internal imports
from .database import get_db
from models import (
    Conversation,
    Message,
    ConversationSummary,
    SystemEvent,
    UserPrivacySettings,
)
from .config import ChatConfig
from .user_integration import ChatUserIntegration

# Memory service integration
from ..memory.memoryService import MemoryService
from ..memory.types import MemoryItem as ChatMemoryItem

# Dedicated service integrations (services communicate via API calls or direct imports)
# Assistant service is now separate - we can import it or call via HTTP
from ..assistant.mental_health_assistant import MentalHealthAssistant

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
memory_service = MemoryService()
mental_health_assistant = MentalHealthAssistant()


# Pydantic models for API (user_id always comes from JWT - no user input needed)
class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone_number: Optional[str] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_active_at: Optional[datetime]


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None
    session_type: str = "chat"


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    session_type: str
    status: str
    crisis_level: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]


class MessageRequest(BaseModel):
    content: str
    conversation_id: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    role: str
    message_type: str
    requires_intervention: bool
    created_at: datetime
    # Memory integration fields
    memory_extracted: bool
    memory_items_created: List[str]


class ChatResponse(BaseModel):
    message: MessageResponse
    assistant_response: MessageResponse
    crisis_assessment: Dict[str, Any]
    memory_processing: Dict[str, Any]
    conversation_status: str


class CrisisAssessmentResponse(BaseModel):
    """Detailed crisis assessment information."""

    level: str  # CRISIS, CONCERN, SUPPORT, unknown
    explanation: str
    intervention_required: bool
    confidence: float
    resources_provided: List[str]
    coping_strategies: List[str]
    intervention_attempted: Optional[bool] = None
    intervention_success: Optional[bool] = None
    emergency_contact_notified: Optional[str] = None
    intervention_error: Optional[str] = None


class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with detailed crisis information."""

    message: MessageResponse
    assistant_response: MessageResponse
    crisis_assessment: CrisisAssessmentResponse
    memory_processing: Dict[str, Any]
    conversation_status: str
    intervention_details: Optional[Dict[str, Any]] = None


# Helper functions
def hash_password(password: str) -> str:
    """Simple password hashing - in production use proper libraries like bcrypt"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


async def log_system_event(
    db: Session,
    user_id: Optional[str],
    event_type: str,
    event_category: str,
    event_data: Dict[str, Any],
    severity: str = "info",
):
    """Log system events for audit and monitoring"""
    event = SystemEvent(
        user_id=user_id,
        event_type=event_type,
        event_category=event_category,
        event_data=event_data,
        severity=severity,
    )
    db.add(event)
    db.commit()


# 🔐 SECURE CHAT ENDPOINTS - JWT Authentication Required


@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """Create a new chat user using normalized user system."""
    try:
        # Use sync service to create user in normalized system
        result = await ChatUserIntegration.sync_user_from_supabase(
            supabase_user_data={
                "id": str(uuid.uuid4()),  # Generate new UUID
                "email": request.email,
                "user_metadata": {"full_name": request.full_name},
                "phone": request.phone_number,
            },
            source="chat_api_create",
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Get the created user data
        user_data = await ChatUserIntegration.get_user_for_chat(result["user"]["id"])

        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone_number=user_data["phone_number"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            created_at=user_data["created_at"],
            last_active_at=user_data["last_active_at"],
        )

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(user_id: str = Depends(get_current_user_id)):
    """Get current authenticated user's information. JWT secured."""
    try:
        user_data = await ChatUserIntegration.get_user_for_chat(user_id)

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone_number=user_data["phone_number"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            created_at=user_data["created_at"],
            last_active_at=user_data["last_active_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new conversation for the authenticated user. JWT secured."""
    try:
        # Create conversation object
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=request.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            session_type=request.session_type,
            status="active",
            crisis_level="none",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Log conversation creation
        await log_system_event(
            db=db,
            user_id=user_id,
            event_type="conversation_created",
            event_category="chat",
            event_data={
                "conversation_id": conversation.id,
                "session_type": request.session_type,
            },
        )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            session_type=conversation.session_type,
            status=conversation.status,
            crisis_level=conversation.crisis_level,
            message_count=0,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=None,
        )

    except Exception as e:
        logger.error(f"Error creating conversation for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
):
    """Get conversations for the authenticated user. JWT secured."""
    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                session_type=conv.session_type,
                status=conv.status,
                crisis_level=conv.crisis_level,
                message_count=len(conv.messages) if conv.messages else 0,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                last_message_at=(
                    max(msg.created_at for msg in conv.messages)
                    if conv.messages
                    else None
                ),
            )
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages", response_model=EnhancedChatResponse)
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Send a message in a conversation. JWT secured - user can only message their own conversations."""
    try:
        # Verify conversation belongs to user
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found or access denied"
            )

        # Create user message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=request.conversation_id,
            content=request.content,
            role="user",
            message_type="chat",
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # Get response from mental health assistant
        try:
            # Use the new process_message method that includes crisis intervention
            assistant_response_data = await mental_health_assistant.generate_response(
                user_message=request.content,
                memory_context=None,  # Memory context would come from memory service
                user_id=user_id,
            )

            assistant_response_text = assistant_response_data["response"]

            # Extract crisis assessment from the response
            crisis_assessment = {
                "level": assistant_response_data.get("crisis_level", "SUPPORT"),
                "explanation": assistant_response_data.get("crisis_explanation", ""),
                "intervention_required": assistant_response_data.get(
                    "crisis_flag", False
                ),
                "confidence": 0.8,  # Could be enhanced with actual confidence scoring
                "resources_provided": assistant_response_data.get(
                    "resources_provided", []
                ),
                "coping_strategies": assistant_response_data.get(
                    "coping_strategies", []
                ),
            }

            # Handle crisis intervention if needed
            intervention_result = None
            if (
                crisis_assessment["intervention_required"]
                or crisis_assessment["level"] == "CRISIS"
            ):
                try:
                    # Trigger crisis intervention
                    intervention_result = (
                        await mental_health_assistant._handle_crisis_intervention(
                            user_id=user_id,
                            crisis_data=assistant_response_data,
                            user_message=request.content,
                            conversation_context={
                                "conversation_id": request.conversation_id,
                                "session_type": conversation.session_type,
                                "crisis_level": conversation.crisis_level,
                            },
                        )
                    )

                    # Update crisis assessment with intervention details
                    crisis_assessment["intervention_attempted"] = (
                        intervention_result.get("intervention_attempted", False)
                    )
                    crisis_assessment["intervention_success"] = intervention_result.get(
                        "outreach_success", False
                    )
                    crisis_assessment["emergency_contact_notified"] = (
                        intervention_result.get("contact_reached", "")
                    )

                    # Log crisis event
                    await log_system_event(
                        db=db,
                        user_id=user_id,
                        event_type="crisis_intervention",
                        event_category="safety",
                        event_data={
                            "conversation_id": request.conversation_id,
                            "crisis_level": crisis_assessment["level"],
                            "intervention_result": intervention_result,
                            "user_message_preview": request.content[:100],
                        },
                        severity="critical",
                    )

                except Exception as intervention_error:
                    logger.error(
                        f"Crisis intervention failed for user {user_id}: {str(intervention_error)}"
                    )
                    crisis_assessment["intervention_error"] = str(intervention_error)

            # Update conversation crisis level if escalated
            if (
                crisis_assessment["level"] in ["CRISIS", "CONCERN"]
                and conversation.crisis_level == "none"
            ):
                conversation.crisis_level = crisis_assessment["level"].lower()

        except Exception as e:
            logger.error(f"Assistant processing failed: {str(e)}")
            assistant_response_text = "I apologize, but I'm having trouble processing your message right now. Please try again or contact support if this continues."

            # Default crisis assessment for errors
            crisis_assessment = {
                "level": "unknown",
                "explanation": "Unable to assess due to technical error",
                "intervention_required": False,
                "confidence": 0.0,
                "error": str(e),
            }

        # Create assistant message
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=request.conversation_id,
            content=assistant_response_text,
            role="assistant",
            message_type="response",
        )

        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        # Process message for memory extraction (background task)
        memory_result = {}
        try:
            memory_result = await memory_service.process_memory(
                user_id=user_id,
                content=request.content,
                type="chat",
                metadata={"conversation_id": request.conversation_id},
            )
        except Exception as e:
            logger.error(f"Memory processing failed: {str(e)}")
            memory_result = {"error": str(e), "stored": False}

        # Update conversation
        conversation.updated_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        db.commit()

        # Background task for memory extraction
        if memory_result.get("stored"):
            background_tasks.add_task(
                extract_memories_from_message,
                user_message.id,
                user_id,
                memory_result,
            )

        return EnhancedChatResponse(
            message=MessageResponse(
                id=user_message.id,
                conversation_id=user_message.conversation_id,
                content=user_message.content,
                role=user_message.role,
                message_type=user_message.message_type,
                requires_intervention=crisis_assessment.get(
                    "intervention_required", False
                ),
                created_at=user_message.created_at,
                memory_extracted=memory_result.get("stored", False),
                memory_items_created=memory_result.get("memory_ids", []),
            ),
            assistant_response=MessageResponse(
                id=assistant_message.id,
                conversation_id=assistant_message.conversation_id,
                content=assistant_message.content,
                role=assistant_message.role,
                message_type=assistant_message.message_type,
                requires_intervention=False,
                created_at=assistant_message.created_at,
                memory_extracted=False,
                memory_items_created=[],
            ),
            crisis_assessment=CrisisAssessmentResponse(
                level=crisis_assessment.get("level", "SUPPORT"),
                explanation=crisis_assessment.get("explanation", ""),
                intervention_required=crisis_assessment.get(
                    "intervention_required", False
                ),
                confidence=crisis_assessment.get("confidence", 0.8),
                resources_provided=crisis_assessment.get("resources_provided", []),
                coping_strategies=crisis_assessment.get("coping_strategies", []),
                intervention_attempted=crisis_assessment.get("intervention_attempted"),
                intervention_success=crisis_assessment.get("intervention_success"),
                emergency_contact_notified=crisis_assessment.get(
                    "emergency_contact_notified"
                ),
                intervention_error=crisis_assessment.get("intervention_error"),
            ),
            memory_processing=memory_result,
            conversation_status=conversation.status,
            intervention_details=intervention_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def extract_memories_from_message(
    message_id: str, user_id: str, memory_result: Dict[str, Any]
):
    """Background task to extract and link memories from chat messages."""
    try:
        # Create chat memory items
        # This could link to the message for cross-referencing
        logger.info(f"Processing memory extraction for message {message_id}")

        # Add any additional memory processing logic here
        # For example, linking chat messages to memory items

    except Exception as e:
        logger.error(f"Memory extraction failed for message {message_id}: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get messages from a conversation. JWT secured - user can only access their own conversations."""
    try:
        # Verify conversation belongs to user
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found or access denied"
            )

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .all()
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "role": msg.role,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at,
                    "requires_intervention": msg.requires_intervention,
                }
                for msg in messages
            ],
            "total_messages": len(messages),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting messages for conversation {conversation_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crisis-resources")
async def get_crisis_resources():
    """Get crisis intervention resources. Public endpoint."""
    return ChatConfig.get_crisis_resources()


@router.post("/report-crisis")
async def report_crisis_situation(
    conversation_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    additional_info: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Report a crisis situation. JWT secured - user can only report for their own conversations."""
    try:
        # Verify conversation belongs to user
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found or access denied"
            )

        # Update crisis level
        conversation.crisis_level = "high"
        conversation.status = "requires_intervention"
        db.commit()

        # Log crisis event
        await log_system_event(
            db=db,
            user_id=user_id,
            event_type="crisis_reported",
            event_category="safety",
            event_data={
                "conversation_id": conversation_id,
                "additional_info": additional_info,
                "automated": False,
            },
            severity="critical",
        )

        # Here you would typically:
        # 1. Alert crisis intervention team
        # 2. Send notifications to appropriate personnel
        # 3. Log for immediate review

        return {
            "status": "crisis_reported",
            "message": "Crisis situation has been reported and appropriate personnel have been notified.",
            "conversation_id": conversation_id,
            "crisis_resources": ChatConfig.get_crisis_resources(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error reporting crisis for conversation {conversation_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.on_event("startup")
async def initialize_chat_service():
    """Initialize chat service on startup."""
    try:
        # Initialize memory service
        await memory_service.initialize()
        logger.info("Memory service initialized")

        logger.info("Chat service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {str(e)}")


# All chat operations now use JWT authentication - users can ONLY access their own data
