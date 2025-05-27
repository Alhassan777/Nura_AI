"""
Memory API Module
Handles memory storage, retrieval, and management endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from dataclasses import asdict

# Import services
from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem, MemoryContext, MemoryStats

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/memory", tags=["memory"])

# Initialize memory service
memory_service = MemoryService()


# Pydantic models
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


class PendingConsentRequest(BaseModel):
    memory_choices: Dict[str, Dict[str, Any]]


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
    elif Config.VECTOR_DB_TYPE == "vertex" or Config.USE_VERTEX_AI:
        if not Config.GOOGLE_CLOUD_PROJECT:
            missing_required.append("GOOGLE_CLOUD_PROJECT")

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


# Memory endpoints
@router.post("/", response_model=MemoryResponse)
async def process_memory(
    request: MemoryRequest, user_id: str = Query(..., description="User ID")
):
    """Process a new memory and store it if relevant."""
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


@router.post("/context", response_model=MemoryContextResponse)
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


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(user_id: str = Query(..., description="User ID")):
    """Get memory statistics for a user."""
    try:
        stats = await memory_service.get_memory_stats(user_id)
        return MemoryStatsResponse(
            stats=stats, configuration_status=get_configuration_status()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
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


@router.post("/forget")
async def clear_memories(user_id: str = Query(..., description="User ID")):
    """Clear all memories for a user."""
    try:
        await memory_service.clear_memories(user_id)
        return {"message": "All memories cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent", response_model=ConsentResponse)
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


@router.post("/export")
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


@router.post("/dual-storage", response_model=DualStorageMemoryResponse)
async def process_memory_dual_storage(
    request: MemoryRequest, user_id: str = Query(..., description="User ID")
):
    """Process memory with dual storage strategy."""
    try:
        config_status = get_configuration_status()

        result = await memory_service.process_memory(
            user_id=user_id,
            content=request.content,
            type=request.type,
            metadata=request.metadata,
            user_consent=None,
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


@router.post("/dual-storage/consent", response_model=DualStorageConsentResponse)
async def process_memory_with_dual_storage_consent(
    request: DualStorageConsentRequest, user_id: str = Query(..., description="User ID")
):
    """Process memory after user has provided dual storage consent."""
    try:
        config_status = get_configuration_status()

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


@router.get("/dual-storage/info")
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


@router.get("/session-summary")
async def get_session_summary(user_id: str):
    """Get a summary of chat memories for user review."""
    try:
        summary = await memory_service.get_chat_session_summary(user_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting session summary for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-choices")
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


@router.get("/emotional-anchors")
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


@router.get("/regular-memories")
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


@router.get("/all-long-term")
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


@router.get("/pending-consent")
async def get_pending_consent_memories(
    user_id: str = Query(..., description="User ID")
):
    """Get memories that are pending PII consent for long-term storage."""
    try:
        config_status = get_configuration_status()
        result = await memory_service.get_pending_consent_memories(user_id)

        return {
            **result,
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }

    except Exception as e:
        logger.error(f"Error getting pending consent memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-pending-consent")
async def process_pending_consent(
    request: PendingConsentRequest, user_id: str = Query(..., description="User ID")
):
    """Process pending memories with user consent decisions."""
    try:
        config_status = get_configuration_status()
        result = await memory_service.process_pending_consent(
            user_id, request.memory_choices
        )

        return {
            **result,
            "configuration_status": (
                config_status if config_status["has_configuration_issues"] else None
            ),
        }

    except Exception as e:
        logger.error(f"Error processing pending consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
