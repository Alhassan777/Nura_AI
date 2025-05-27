from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
from dataclasses import asdict
import redis.asyncio as redis
from datetime import timedelta
import json
import time
from datetime import datetime

from .memoryService import MemoryService
from .types import MemoryItem, MemoryContext, MemoryStats
from .assistant.mental_health_assistant import MentalHealthAssistant
from .config import Config

# Set up logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Nura Memory Service")

# Initialize services
memory_service = MemoryService()
mental_health_assistant = MentalHealthAssistant()

# Add Redis client for voice mappings (after existing Redis initialization)
# Voice mapping storage in Redis
redis_client = redis.from_url(Config.REDIS_URL)


# Helper function to check configuration status
def get_configuration_status() -> Dict[str, Any]:
    """Get current configuration status for API responses."""
    missing_required = []
    missing_optional = []

    # Check required configs based on actual Config validation logic
    if not Config.GOOGLE_API_KEY:
        missing_required.append("GOOGLE_API_KEY")

    # Check vector database specific requirements
    if Config.VECTOR_DB_TYPE == "pinecone" or Config.USE_PINECONE:
        if not Config.PINECONE_API_KEY:
            missing_required.append("PINECONE_API_KEY")
    elif Config.VECTOR_DB_TYPE == "vertex" or Config.USE_VERTEX_AI:
        if not Config.GOOGLE_CLOUD_PROJECT:
            missing_required.append("GOOGLE_CLOUD_PROJECT")

    # Check optional configs - only flag if they're actually missing/broken
    try:
        prompt = Config.get_mental_health_system_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("MENTAL_HEALTH_SYSTEM_PROMPT")
    except:
        missing_optional.append("MENTAL_HEALTH_SYSTEM_PROMPT")

    try:
        prompt = Config.get_conversation_guidelines()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("CONVERSATION_GUIDELINES")
    except:
        missing_optional.append("CONVERSATION_GUIDELINES")

    try:
        prompt = Config.get_crisis_detection_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("CRISIS_DETECTION_PROMPT")
    except:
        missing_optional.append("CRISIS_DETECTION_PROMPT")

    try:
        prompt = Config.get_memory_comprehensive_scoring_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("MEMORY_COMPREHENSIVE_SCORING_PROMPT")
    except:
        missing_optional.append("MEMORY_COMPREHENSIVE_SCORING_PROMPT")

    # Only flag these if they're using defaults and might cause issues
    if Config.REDIS_URL == "redis://localhost:6379":
        # Only add as optional if Redis is actually not accessible
        try:
            import redis

            r = redis.Redis.from_url(Config.REDIS_URL)
            r.ping()
        except:
            missing_optional.append("REDIS_URL - Redis not accessible")

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


# Request/Response models
class MemoryRequest(BaseModel):
    content: str
    type: str = "chat"
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(BaseModel):
    memory: Optional[MemoryItem]
    requires_consent: bool = False
    sensitive_types: List[str] = []
    configuration_status: Optional[Dict[str, Any]] = None


class DualStorageMemoryResponse(BaseModel):
    needs_consent: bool
    stored: bool = False
    consent_options: Optional[Dict[str, Any]] = None
    memory_id: Optional[str] = None
    storage_details: Optional[Dict[str, Any]] = None
    pii_summary: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    # New fields for component extraction
    components: Optional[List[Dict[str, Any]]] = None
    total_components: Optional[int] = None
    stored_components: Optional[int] = None
    storage_summary: Optional[Dict[str, Any]] = None
    configuration_status: Optional[Dict[str, Any]] = None


class DualStorageConsentRequest(BaseModel):
    memory_id: str
    original_content: str
    user_consent: Dict[str, Any]
    type: str = "chat"
    metadata: Optional[Dict[str, Any]] = None


class DualStorageConsentResponse(BaseModel):
    success: bool
    storage_details: Dict[str, Any]
    stored_memories: Dict[str, Any]
    pii_summary: Dict[str, Any]
    score: Dict[str, Any]
    configuration_status: Optional[Dict[str, Any]] = None


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


class MemoryContextRequest(BaseModel):
    query: Optional[str] = None


class MemoryContextResponse(BaseModel):
    context: MemoryContext
    configuration_status: Optional[Dict[str, Any]] = None


class MemoryStatsResponse(BaseModel):
    stats: MemoryStats
    configuration_status: Optional[Dict[str, Any]] = None


class ConsentRequest(BaseModel):
    memory_id: str
    grant_consent: bool


class ConsentResponse(BaseModel):
    success: bool
    message: str
    configuration_status: Optional[Dict[str, Any]] = None


class VoiceMappingRequest(BaseModel):
    callId: str
    customerId: str
    mode: str
    phoneNumber: Optional[str] = None


class VoiceWebhookEventRequest(BaseModel):
    event: Dict[str, Any]
    callId: str
    receivedAt: str
    source: str = "vapi_webhook"


class VoiceProcessingResult(BaseModel):
    success: bool
    callId: str
    customerId: Optional[str]
    processingTimeMs: float
    assistantReply: Optional[str] = None
    crisisLevel: Optional[str] = None
    memoryStored: bool = False
    error: Optional[str] = None
    timestamp: str
    # Section 3: Enhanced voice processing metadata
    voiceOptimized: Optional[bool] = None
    wordCount: Optional[int] = None
    estimatedSpeechTime: Optional[float] = None
    vapiDelivery: Optional[Dict[str, Any]] = None
    controlUrlUsed: Optional[str] = None
    requiresImmediateDelivery: Optional[bool] = None


@app.get("/health")
async def health_check():
    """Health check endpoint with configuration status."""
    config_status = get_configuration_status()

    return {
        "status": (
            "healthy" if not config_status["has_configuration_issues"] else "degraded"
        ),
        "message": "Nura Memory Service is running",
        "configuration": config_status,
        "timestamp": str(__import__("datetime").datetime.utcnow()),
        "version": "2025-05-26-updated",  # Added to verify server reload
    }


@app.post("/chat/assistant", response_model=ChatResponse)
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


@app.get("/chat/crisis-resources")
async def get_crisis_resources():
    """Get immediate crisis resources."""
    try:
        return await mental_health_assistant.provide_crisis_resources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=MemoryResponse)
async def process_chat(
    request: MemoryRequest, user_id: str = Query(..., description="User ID")
):
    """Process a new chat message and store it in memory if relevant."""
    try:
        memory = await memory_service.process_memory(
            user_id=user_id,
            content=request.content,
            type=request.type,
            metadata=request.metadata,
        )

        return MemoryResponse(
            memory=memory,
            requires_consent=memory.metadata.get("has_pii", False) if memory else False,
            sensitive_types=(
                memory.metadata.get("sensitive_types", []) if memory else []
            ),
            configuration_status=get_configuration_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/context", response_model=MemoryContextResponse)
async def get_memory_context(
    request: MemoryContextRequest, user_id: str = Query(..., description="User ID")
):
    """Get the current memory context for a user."""
    try:
        context = await memory_service.get_memory_context(
            user_id=user_id, query=request.query
        )
        return MemoryContextResponse(
            context=context, configuration_status=get_configuration_status()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(user_id: str = Query(..., description="User ID")):
    """Get memory statistics for a user."""
    try:
        stats = await memory_service.get_memory_stats(user_id)
        return MemoryStatsResponse(
            stats=stats, configuration_status=get_configuration_status()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str, user_id: str = Query(..., description="User ID")
):
    """Delete a specific memory."""
    try:
        success = await memory_service.delete_memory(user_id, memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/forget")
async def clear_memories(user_id: str = Query(..., description="User ID")):
    """Clear all memories for a user."""
    try:
        await memory_service.clear_memories(user_id)
        return {"message": "All memories cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/consent", response_model=ConsentResponse)
async def handle_consent(
    request: ConsentRequest, user_id: str = Query(..., description="User ID")
):
    """Handle consent for sensitive memories."""
    try:
        # Get memory
        context = await memory_service.get_memory_context(user_id)
        memory = next(
            (
                m
                for m in context.short_term + context.long_term
                if m.id == request.memory_id
            ),
            None,
        )

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        if request.grant_consent:
            # Restore original content if anonymized
            if memory.metadata.get("anonymized"):
                # Content restoration not implemented yet
                pass

            memory.metadata["has_consent"] = True
            return ConsentResponse(
                success=True,
                message="Consent granted successfully",
                configuration_status=get_configuration_status(),
            )
        else:
            # Delete memory if consent denied
            await memory_service.delete_memory(user_id, memory.id)
            return ConsentResponse(
                success=True,
                message="Memory deleted due to denied consent",
                configuration_status=get_configuration_status(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/export")
async def export_memories(user_id: str = Query(..., description="User ID")):
    """Export all memories for a user."""
    try:
        context = await memory_service.get_memory_context(user_id)
        return {
            "short_term": [asdict(m) for m in context.short_term],
            "long_term": [asdict(m) for m in context.long_term],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/dual-storage", response_model=DualStorageMemoryResponse)
async def process_memory_dual_storage(
    request: MemoryRequest, user_id: str = Query(..., description="User ID")
):
    """Process memory with dual storage strategy (different privacy for short-term vs long-term)."""
    try:
        config_status = get_configuration_status()

        # Process memory with dual storage
        result = await memory_service.process_memory(
            user_id=user_id,
            content=request.content,
            type=request.type,
            metadata=request.metadata,
            user_consent=None,  # No consent provided yet
        )

        return DualStorageMemoryResponse(
            needs_consent=result["needs_consent"],
            stored=result.get("stored", False),
            consent_options=result.get("consent_options"),
            memory_id=result.get("memory_id"),
            storage_details=result.get("storage_details"),
            pii_summary=result.get("pii_summary"),
            score=result.get("score"),
            reason=result.get("reason"),
            # New component fields
            components=result.get("components"),
            total_components=result.get("total_components"),
            stored_components=result.get("stored_components"),
            storage_summary=result.get("storage_summary"),
            configuration_status=(
                config_status if config_status["has_configuration_issues"] else None
            ),
        )

    except Exception as e:
        config_status = get_configuration_status()
        logger.error(f"Error in process_memory_dual_storage: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "configuration_issues": config_status["has_configuration_issues"],
                "configuration_status": config_status,
            },
        )


@app.post("/memory/dual-storage/consent", response_model=DualStorageConsentResponse)
async def process_memory_with_dual_storage_consent(
    request: DualStorageConsentRequest, user_id: str = Query(..., description="User ID")
):
    """Process memory after user has provided dual storage consent."""
    try:
        config_status = get_configuration_status()

        # Process memory with user consent
        result = await memory_service.process_memory_with_consent(
            user_id=user_id,
            memory_id=request.memory_id,
            original_content=request.original_content,
            user_consent=request.user_consent,
            type=request.type,
            metadata=request.metadata,
        )

        return DualStorageConsentResponse(
            success=result["stored"],
            storage_details=result["storage_details"],
            stored_memories=result["stored_memories"],
            pii_summary=result["pii_summary"],
            score=result["score"],
            configuration_status=(
                config_status if config_status["has_configuration_issues"] else None
            ),
        )

    except Exception as e:
        config_status = get_configuration_status()
        logger.error(f"Error in process_memory_with_dual_storage_consent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "configuration_issues": config_status["has_configuration_issues"],
                "configuration_status": config_status,
            },
        )


@app.get("/memory/dual-storage/info")
async def get_dual_storage_info():
    """Get information about the dual storage strategy."""
    return {
        "strategy": "dual_storage",
        "description": "Different privacy handling for short-term vs long-term memory",
        "storage_types": {
            "short_term": {
                "technology": "Redis",
                "duration": "Session-based (temporary)",
                "privacy_strategy": "Permissive (keeps original for personalization)",
                "purpose": "Immediate conversation context and personalization",
                "risk_level": "Low (ephemeral storage)",
            },
            "long_term": {
                "technology": "Vector database (Chroma/Vertex AI)",
                "duration": "Permanent",
                "privacy_strategy": "Conservative (anonymizes sensitive data)",
                "purpose": "Therapeutic continuity across sessions",
                "risk_level": "Managed (sensitive identifiers removed)",
            },
        },
        "privacy_categories": {
            "high_risk": {
                "entities": [
                    "PERSON",
                    "HEALTHCARE_PROVIDER",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "INSURANCE_INFO",
                    "WORKPLACE_INFO",
                    "FAMILY_MEMBER",
                ],
                "short_term_default": "keep_original",
                "long_term_default": "anonymize",
                "description": "Highly identifying personal information",
            },
            "medium_risk": {
                "entities": [
                    "MEDICATION",
                    "MENTAL_HEALTH_DIAGNOSIS",
                    "MEDICAL_FACILITY",
                    "SCHOOL_INFO",
                ],
                "short_term_default": "keep_original",
                "long_term_default": "user_choice",
                "description": "Medical information with therapeutic value",
            },
            "low_risk": {
                "entities": ["THERAPY_TYPE", "CRISIS_HOTLINE", "DATE_TIME"],
                "short_term_default": "keep_original",
                "long_term_default": "keep_original",
                "description": "Safe therapeutic context",
            },
        },
        "benefits": [
            "Personalized chat experience through short-term storage",
            "Privacy protection through long-term anonymization",
            "Therapeutic continuity with managed risk",
            "User control over sensitive information",
            "Compliance-ready audit trail",
        ],
    }


@app.get("/config/test")
async def test_configuration():
    """Test endpoint to verify configuration and demonstrate error handling."""
    config_status = get_configuration_status()

    if config_status["has_configuration_issues"]:
        logger.warning("Configuration test failed - missing environment variables")
        return {
            "status": "CONFIGURATION_ERROR",
            "message": "❌ Configuration test failed. The service is running but some features may not work properly.",
            "details": config_status,
            "recommendations": [
                "Copy env.example to .env file",
                "Set missing environment variables",
                "Restart the service after configuration",
                "Use /health endpoint for ongoing monitoring",
            ],
        }
    else:
        return {
            "status": "SUCCESS",
            "message": "✅ All configurations are properly set. Service is ready for full functionality.",
            "details": config_status,
        }


@app.get("/memory/session-summary")
async def get_session_summary(user_id: str):
    """Get a summary of chat memories for user review."""
    try:
        summary = await memory_service.get_chat_session_summary(user_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting session summary for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/apply-choices")
async def apply_memory_choices(request: dict):
    """Apply user choices about which memories to keep, remove, or anonymize."""
    try:
        user_id = request.get("user_id")
        memory_choices = request.get("memory_choices", {})

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        results = await memory_service.apply_user_memory_choices(
            user_id, memory_choices
        )
        return results
    except Exception as e:
        logger.error(f"Error applying memory choices for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/emotional-anchors")
async def get_emotional_anchors(user_id: str = Query(..., description="User ID")):
    """Get emotional anchors (meaningful connections) for a user."""
    try:
        config_status = get_configuration_status()
        emotional_anchors = await memory_service.get_emotional_anchors(user_id)

        return {
            "emotional_anchors": [asdict(anchor) for anchor in emotional_anchors],
            "count": len(emotional_anchors),
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }
    except Exception as e:
        logger.error(f"Error getting emotional anchors for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/regular-memories")
async def get_regular_memories(
    user_id: str = Query(..., description="User ID"),
    query: Optional[str] = Query(None, description="Search query for semantic search"),
):
    """Get regular lasting memories (excluding emotional anchors) for a user."""
    try:
        config_status = get_configuration_status()
        regular_memories = await memory_service.get_regular_memories(user_id, query)

        return {
            "regular_memories": [asdict(memory) for memory in regular_memories],
            "count": len(regular_memories),
            "query": query,
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }
    except Exception as e:
        logger.error(f"Error getting regular memories for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/all-long-term")
async def get_all_long_term_memories(user_id: str = Query(..., description="User ID")):
    """Get all long-term memories categorized by type."""
    try:
        config_status = get_configuration_status()

        # Get both types of memories
        emotional_anchors = await memory_service.get_emotional_anchors(user_id)
        regular_memories = await memory_service.get_regular_memories(user_id)

        return {
            "emotional_anchors": [asdict(anchor) for anchor in emotional_anchors],
            "regular_memories": [asdict(memory) for memory in regular_memories],
            "counts": {
                "emotional_anchors": len(emotional_anchors),
                "regular_memories": len(regular_memories),
                "total": len(emotional_anchors) + len(regular_memories),
            },
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }
    except Exception as e:
        logger.error(
            f"Error getting all long-term memories for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/pending-consent")
async def get_pending_consent_memories(
    user_id: str = Query(..., description="User ID")
):
    """Get memories that are pending PII consent for long-term storage."""
    try:
        config_status = get_configuration_status()
        result = await memory_service.get_pending_consent_memories(user_id)

        # Add configuration status to result
        return {
            **result,
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }

    except Exception as e:
        logger.error(f"Error getting pending consent memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class PendingConsentRequest(BaseModel):
    memory_choices: Dict[
        str, Dict[str, Any]
    ]  # memory_id -> {"consent": {...}, "action": "approve|deny"}


@app.post("/memory/process-pending-consent")
async def process_pending_consent(
    request: PendingConsentRequest, user_id: str = Query(..., description="User ID")
):
    """Process pending memories with user consent decisions."""
    try:
        config_status = get_configuration_status()
        result = await memory_service.process_pending_consent(
            user_id, request.memory_choices
        )

        # Add configuration status to result
        return {
            **result,
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }

    except Exception as e:
        logger.error(f"Error processing pending consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/privacy-review/{user_id}")
async def get_memories_for_privacy_review(user_id: str):
    """Get memories that contain PII for user privacy review."""
    try:
        # Get all memories with PII
        short_term_memories = await memory_service.redis_store.get_memories(user_id)
        long_term_memories = await memory_service.vector_store.get_memories(user_id)

        memories_with_pii = []

        # Check short-term memories
        for memory in short_term_memories:
            has_pii = memory.metadata.get("has_pii", False)
            # Handle both boolean and string representations
            if has_pii is True or has_pii == "True" or has_pii == "true":
                # Skip memories that have already been processed
                if memory.metadata.get("privacy_choice"):
                    continue

                pii_results = await memory_service.pii_detector.detect_pii(memory)

                memory_info = {
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.type,
                    "storage_type": "short_term",
                    "timestamp": (
                        memory.timestamp.isoformat()
                        if hasattr(memory.timestamp, "isoformat")
                        else str(memory.timestamp)
                    ),
                    "memory_type": memory.metadata.get("memory_type", "unknown"),
                    "pii_detected": pii_results["detected_items"],
                    "pii_summary": {
                        "types": list(
                            set(item["type"] for item in pii_results["detected_items"])
                        ),
                        "high_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "high"
                            ]
                        ),
                        "medium_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "medium"
                            ]
                        ),
                        "low_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "low"
                            ]
                        ),
                    },
                }
                memories_with_pii.append(memory_info)

                # Check long-term memories
        for memory in long_term_memories:
            has_pii = memory.metadata.get("has_pii", False)
            # Handle both boolean and string representations
            if has_pii is True or has_pii == "True" or has_pii == "true":
                # Skip memories that have already been processed
                if memory.metadata.get("privacy_choice"):
                    continue

                pii_results = await memory_service.pii_detector.detect_pii(memory)

                memory_info = {
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.type,
                    "storage_type": "long_term",
                    "timestamp": (
                        memory.timestamp.isoformat()
                        if hasattr(memory.timestamp, "isoformat")
                        else str(memory.timestamp)
                    ),
                    "memory_type": memory.metadata.get("memory_type", "unknown"),
                    "is_emotional_anchor": memory.metadata.get("display_category")
                    == "emotional_anchor",
                    "pii_detected": pii_results["detected_items"],
                    "pii_summary": {
                        "types": list(
                            set(item["type"] for item in pii_results["detected_items"])
                        ),
                        "high_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "high"
                            ]
                        ),
                        "medium_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "medium"
                            ]
                        ),
                        "low_risk_count": len(
                            [
                                item
                                for item in pii_results["detected_items"]
                                if item["risk_level"] == "low"
                            ]
                        ),
                    },
                }
                memories_with_pii.append(memory_info)

        return {
            "memories_with_pii": memories_with_pii,
            "total_count": len(memories_with_pii),
            "privacy_options": {
                "remove_entirely": {
                    "label": "Remove Entirely",
                    "description": "Delete this memory completely from all storage",
                    "icon": "🗑️",
                },
                "remove_pii_only": {
                    "label": "Remove PII Only",
                    "description": "Keep the memory but replace sensitive information with placeholders",
                    "icon": "🔒",
                },
                "keep_original": {
                    "label": "Keep Original",
                    "description": "Keep the memory exactly as is (for trusted therapeutic context)",
                    "icon": "✅",
                },
            },
        }

    except Exception as e:
        logger.error(f"Error getting memories for privacy review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/apply-privacy-choices/{user_id}")
async def apply_privacy_choices(user_id: str, choices: Dict[str, str]):
    """Apply user privacy choices for memories with PII.

    Args:
        choices: Dict mapping memory_id to choice ("remove_entirely", "remove_pii_only", "keep_original")
    """
    try:
        results = {
            "processed": [],
            "errors": [],
            "summary": {
                "removed_entirely": 0,
                "pii_removed": 0,
                "kept_original": 0,
                "total_processed": 0,
            },
        }

        for memory_id, choice in choices.items():
            try:
                # Find the memory in both stores
                memory = None
                storage_location = None

                # Check short-term first
                short_term_memories = await memory_service.redis_store.get_memories(
                    user_id
                )
                for mem in short_term_memories:
                    if mem.id == memory_id:
                        memory = mem
                        storage_location = "short_term"
                        break

                # Check long-term if not found
                if not memory:
                    long_term_memories = await memory_service.vector_store.get_memories(
                        user_id
                    )
                    for mem in long_term_memories:
                        if mem.id == memory_id:
                            memory = mem
                            storage_location = "long_term"
                            break

                if not memory:
                    results["errors"].append(
                        {"memory_id": memory_id, "error": "Memory not found"}
                    )
                    continue

                if choice == "remove_entirely":
                    # Delete from appropriate storage
                    if storage_location == "short_term":
                        await memory_service.redis_store.delete_memory(
                            user_id, memory_id
                        )
                    else:
                        await memory_service.vector_store.delete_memory(
                            user_id, memory_id
                        )

                    results["processed"].append(
                        {
                            "memory_id": memory_id,
                            "action": "removed_entirely",
                            "original_content": memory.content,
                        }
                    )
                    results["summary"]["removed_entirely"] += 1

                elif choice == "remove_pii_only":
                    try:
                        # Detect PII and create anonymized version
                        pii_results = await memory_service.pii_detector.detect_pii(
                            memory
                        )

                        logger.info(
                            f"PII detected in memory {memory_id}: {len(pii_results.get('detected_items', []))} items"
                        )

                        if not pii_results.get("detected_items"):
                            # No PII found, just update metadata
                            # Ensure timestamp is a datetime object
                            timestamp = memory.timestamp
                            if isinstance(timestamp, str):
                                from datetime import datetime

                                timestamp = datetime.fromisoformat(
                                    timestamp.replace("Z", "+00:00")
                                )

                            updated_memory = MemoryItem(
                                id=memory.id,
                                userId=memory.userId,
                                content=memory.content,
                                type=memory.type,
                                metadata={
                                    **memory.metadata,
                                    "privacy_choice": "remove_pii_only",
                                    "pii_removed": False,
                                    "no_pii_found": True,
                                },
                                timestamp=timestamp,
                            )
                            anonymized_content = memory.content
                        else:
                            # Force anonymization of all detected PII
                            # Create consent dictionary to anonymize all items
                            anonymize_consent = {}
                            for item in pii_results.get("detected_items", []):
                                anonymize_consent[item["id"]] = "anonymize"
                                logger.info(
                                    f"Will anonymize: {item['text']} (type: {item['type']})"
                                )

                            anonymized_content = await memory_service.pii_detector.apply_granular_consent(
                                memory.content,
                                storage_location,
                                anonymize_consent,  # Use the consent dictionary
                                pii_results,
                            )

                            logger.info(f"Original content: {memory.content}")
                            logger.info(f"Anonymized content: {anonymized_content}")

                            # Update the memory with anonymized content
                        # Ensure timestamp is a datetime object
                        timestamp = memory.timestamp
                        if isinstance(timestamp, str):
                            from datetime import datetime

                            timestamp = datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            )

                        updated_memory = MemoryItem(
                            id=memory.id,
                            userId=memory.userId,
                            content=anonymized_content,
                            type=memory.type,
                            metadata={
                                **memory.metadata,
                                "pii_removed": True,
                                "original_had_pii": True,
                                "privacy_choice": "remove_pii_only",
                                "has_pii": False,  # Mark as no longer containing PII
                                "original_content": memory.content,  # Store original for reference
                            },
                            timestamp=timestamp,
                        )

                        # Update memory instead of adding a new one
                        if storage_location == "short_term":
                            await memory_service.redis_store.update_memory(
                                user_id, updated_memory
                            )
                        else:
                            await memory_service.vector_store.update_memory(
                                user_id, updated_memory
                            )

                        results["processed"].append(
                            {
                                "memory_id": memory_id,
                                "action": "pii_removed",
                                "original_content": memory.content,
                                "anonymized_content": anonymized_content,
                                "pii_items_removed": [
                                    {
                                        "text": item["text"],
                                        "type": item["type"],
                                        "replaced_with": f"<{item['type']}>",
                                    }
                                    for item in pii_results.get("detected_items", [])
                                ],
                                "anonymization_success": anonymized_content
                                != memory.content,
                            }
                        )
                        results["summary"]["pii_removed"] += 1

                    except Exception as e:
                        logger.error(f"Error anonymizing memory {memory_id}: {str(e)}")
                        results["errors"].append(
                            {
                                "memory_id": memory_id,
                                "error": f"Failed to anonymize PII: {str(e)}",
                            }
                        )
                        continue

                elif choice == "keep_original":
                    # Just update metadata to indicate user choice
                    # Ensure timestamp is a datetime object
                    timestamp = memory.timestamp
                    if isinstance(timestamp, str):
                        from datetime import datetime

                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )

                    updated_memory = MemoryItem(
                        id=memory.id,
                        userId=memory.userId,
                        content=memory.content,
                        type=memory.type,
                        metadata={
                            **memory.metadata,
                            "privacy_choice": "keep_original",
                            "user_approved_pii": True,
                        },
                        timestamp=timestamp,
                    )

                    # Update memory instead of adding a new one
                    if storage_location == "short_term":
                        await memory_service.redis_store.update_memory(
                            user_id, updated_memory
                        )
                    else:
                        await memory_service.vector_store.update_memory(
                            user_id, updated_memory
                        )

                    results["processed"].append(
                        {
                            "memory_id": memory_id,
                            "action": "kept_original",
                            "content": memory.content,
                        }
                    )
                    results["summary"]["kept_original"] += 1

                results["summary"]["total_processed"] += 1

            except Exception as e:
                results["errors"].append({"memory_id": memory_id, "error": str(e)})

        return results

    except Exception as e:
        logger.error(f"Error applying privacy choices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/mapping")
async def store_voice_mapping(request: VoiceMappingRequest):
    """Store callId to customerId mapping in Redis."""
    try:
        # Store mapping with 30 minute TTL
        key = f"vapi:call:{request.callId}"
        mapping_data = {
            "customerId": request.customerId,
            "mode": request.mode,
            "phoneNumber": request.phoneNumber,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await redis_client.setex(
            key, int(timedelta(minutes=30).total_seconds()), json.dumps(mapping_data)
        )

        logger.info(f"Stored voice mapping: {request.callId} -> {request.customerId}")

        return {
            "success": True,
            "callId": request.callId,
            "customerId": request.customerId,
            "ttl_minutes": 30,
        }

    except Exception as e:
        logger.error(f"Failed to store voice mapping: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to store mapping: {str(e)}"
        )


@app.get("/voice/mapping/{call_id}")
async def get_voice_mapping(call_id: str):
    """Get customerId from callId."""
    try:
        key = f"vapi:call:{call_id}"
        mapping_json = await redis_client.get(key)

        if not mapping_json:
            raise HTTPException(status_code=404, detail="Call mapping not found")

        mapping_data = json.loads(mapping_json)
        return {
            "callId": call_id,
            "customerId": mapping_data["customerId"],
            "mode": mapping_data.get("mode"),
            "phoneNumber": mapping_data.get("phoneNumber"),
            "timestamp": mapping_data.get("timestamp"),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode mapping data for {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid mapping data")
    except Exception as e:
        logger.error(f"Failed to get voice mapping for {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mapping: {str(e)}")


@app.delete("/voice/mapping/{call_id}")
async def delete_voice_mapping(call_id: str):
    """Delete callId mapping (cleanup)."""
    try:
        key = f"vapi:call:{call_id}"
        result = await redis_client.delete(key)

        if result == 0:
            raise HTTPException(status_code=404, detail="Call mapping not found")

        logger.info(f"Deleted voice mapping for call {call_id}")
        return {"success": True, "deleted": True}

    except Exception as e:
        logger.error(f"Failed to delete voice mapping for {call_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete mapping: {str(e)}"
        )


@app.post("/voice/webhook-event", response_model=VoiceProcessingResult)
async def process_voice_webhook_event(request: VoiceWebhookEventRequest):
    """Process voice webhook events from Vapi - the core voice processing pipeline."""
    start_time = time.time()

    try:
        config_status = get_configuration_status()

        # Extract event details
        event = request.event
        call_id = request.callId
        event_type = event.get("type") or event.get("eventType")

        logger.info(f"🎯 Processing voice event: {event_type} for call {call_id}")

        # Get customer ID from call mapping (Section 1)
        customer_id = await get_customer_id_from_call(call_id)
        if not customer_id:
            logger.warning(f"No customer mapping found for call {call_id}")
            processing_time = (time.time() - start_time) * 1000

            return VoiceProcessingResult(
                success=False,
                callId=call_id,
                customerId=None,
                processingTimeMs=processing_time,
                error="Customer mapping not found for call",
                timestamp=datetime.utcnow().isoformat(),
            )

        logger.info(f"📋 Found customer {customer_id} for call {call_id}")

        # Extract message content and control URL from conversation-update event
        user_message = None
        control_url = None

        if event_type == "conversation-update":
            # Try different possible locations for the message content
            message = event.get("message", {})
            if isinstance(message, dict):
                user_message = message.get("content") or message.get("text")
            elif isinstance(message, str):
                user_message = message

            # Also check if it's in the transcript
            transcript = event.get("transcript", {})
            if not user_message and transcript:
                user_message = transcript.get("text") or transcript.get("content")

            # Check for user role specifically
            if message.get("role") == "user" and message.get("content"):
                user_message = message["content"]

            # Extract control URL for response delivery (Section 3: Vapi integration)
            call_info = event.get("call", {})
            control_url = call_info.get("controlUrl") or event.get("controlUrl")

            # Also check for phoneNumber in call info for phone calls
            phone_number = call_info.get("phoneNumber") or call_info.get(
                "customer", {}
            ).get("number")

        if not user_message:
            logger.warning(
                f"No user message found in conversation-update event for call {call_id}"
            )
            processing_time = (time.time() - start_time) * 1000

            return VoiceProcessingResult(
                success=False,
                callId=call_id,
                customerId=customer_id,
                processingTimeMs=processing_time,
                error="No user message found in event",
                timestamp=datetime.utcnow().isoformat(),
            )

        logger.info(
            f"💬 Processing message from call {call_id}: {user_message[:100]}..."
        )
        if control_url:
            logger.info(
                f"🎯 Control URL found for immediate response delivery: {control_url}"
            )

        # Get memory context for the user (Section 3: RAG integration)
        memory_context = await memory_service.get_memory_context(
            user_id=customer_id, query=user_message
        )

        # Generate assistant response using enhanced voice adapter (Section 3: Voice Processing Pipeline)
        from .voice_adapter import voice_adapter

        assistant_response = await voice_adapter.process_voice_message(
            user_message=user_message,
            user_id=customer_id,
            memory_context=memory_context,
            call_id=call_id,
            control_url=control_url,  # Pass control URL for immediate delivery
        )

        # Store the user message in memory
        user_memory = await memory_service.process_memory(
            user_id=customer_id,
            content=user_message,
            type="voice_user_message",
            metadata={
                "source": "voice_call",
                "call_id": call_id,
                "event_type": event_type,
                "received_at": request.receivedAt,
            },
        )

        # Store the assistant response in memory
        assistant_memory = await memory_service.process_memory(
            user_id=customer_id,
            content=assistant_response["response"],
            type="voice_assistant_response",
            metadata={
                "source": "voice_call",
                "call_id": call_id,
                "crisis_level": assistant_response["crisis_level"],
                "resources_provided": assistant_response["resources_provided"],
                "coping_strategies": assistant_response["coping_strategies"],
            },
        )

        processing_time = (time.time() - start_time) * 1000

        # Section 3: Enhanced response delivery and logging
        vapi_delivery_status = assistant_response.get("vapi_delivery", {})
        delivery_success = vapi_delivery_status.get("delivered", False)

        if delivery_success:
            logger.info(
                f"🎯 Response delivered to Vapi for call {call_id}: {assistant_response['response'][:50]}..."
            )
        else:
            logger.info(
                f"🤖 Assistant response generated for call {call_id}: {assistant_response['response'][:50]}..."
            )
            if control_url and not delivery_success:
                logger.warning(
                    f"⚠️  Failed to deliver response to control URL: {vapi_delivery_status.get('error', 'Unknown error')}"
                )

        # Store enhanced latency metrics with delivery status
        await store_voice_latency_metric(call_id, processing_time, delivery_success)

        logger.info(
            f"✅ Voice processing complete for call {call_id} in {processing_time:.1f}ms"
        )

        return VoiceProcessingResult(
            success=True,
            callId=call_id,
            customerId=customer_id,
            processingTimeMs=processing_time,
            assistantReply=assistant_response["response"],
            crisisLevel=assistant_response["crisis_level"],
            memoryStored=user_memory is not None or assistant_memory is not None,
            timestamp=datetime.utcnow().isoformat(),
            # Section 3: Enhanced voice processing metadata
            voiceOptimized=assistant_response.get("voice_optimized", False),
            wordCount=assistant_response.get("word_count"),
            estimatedSpeechTime=assistant_response.get("estimated_speech_time"),
            vapiDelivery=vapi_delivery_status,
            controlUrlUsed=control_url,
            requiresImmediateDelivery=assistant_response.get(
                "requires_immediate_delivery", False
            ),
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Voice processing failed for call {call_id}: {str(e)}")

        return VoiceProcessingResult(
            success=False,
            callId=call_id,
            customerId=customer_id if "customer_id" in locals() else None,
            processingTimeMs=processing_time,
            error=str(e),
            timestamp=datetime.utcnow().isoformat(),
        )


async def store_voice_latency_metric(
    call_id: str, processing_time_ms: float, delivery_success: bool = False
):
    """Store enhanced voice processing latency metrics with delivery status."""
    try:
        # Enhanced logging with delivery status
        delivery_status = "delivered" if delivery_success else "processed_only"
        logger.info(
            f"📊 Voice Latency Metric - Call: {call_id}, Time: {processing_time_ms:.1f}ms, Status: {delivery_status}"
        )

        # Store in Redis for basic metrics collection
        metrics_key = f"voice_metrics:latency:{datetime.utcnow().strftime('%Y-%m-%d')}"
        metric_data = {
            "call_id": call_id,
            "processing_time_ms": processing_time_ms,
            "delivery_success": delivery_success,
            "delivery_status": delivery_status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await redis_client.lpush(metrics_key, json.dumps(metric_data))
        await redis_client.expire(metrics_key, 86400 * 7)  # Keep for 7 days

    except Exception as e:
        logger.error(f"Failed to store latency metric: {str(e)}")


@app.get("/voice/metrics/latency")
async def get_voice_latency_metrics(date: str = None):
    """Get voice processing latency metrics for a specific date."""
    try:
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        metrics_key = f"voice_metrics:latency:{date}"
        raw_metrics = await redis_client.lrange(metrics_key, 0, -1)

        metrics = []
        total_time = 0
        for raw_metric in raw_metrics:
            try:
                metric = json.loads(raw_metric)
                metrics.append(metric)
                total_time += metric["processing_time_ms"]
            except json.JSONDecodeError:
                continue

        if not metrics:
            return {"date": date, "count": 0, "average_latency_ms": 0, "metrics": []}

        return {
            "date": date,
            "count": len(metrics),
            "average_latency_ms": round(total_time / len(metrics), 2),
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Failed to get latency metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to get customerId from callId
async def get_customer_id_from_call(call_id: str) -> Optional[str]:
    """Helper function to get customerId from callId."""
    try:
        key = f"vapi:call:{call_id}"
        mapping_json = await redis_client.get(key)

        if not mapping_json:
            return None

        mapping_data = json.loads(mapping_json)
        return mapping_data.get("customerId")

    except Exception as e:
        logger.error(f"Failed to get customer ID for call {call_id}: {str(e)}")
        return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
