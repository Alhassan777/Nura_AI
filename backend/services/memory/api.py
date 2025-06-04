"""
Memory API Module
Handles memory storage, retrieval, and management endpoints.
SECURE: All endpoints use JWT authentication - users can only access their own data.

This is the MAIN memory API for the integrated Nura application.
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from dataclasses import asdict

# Import services (now local to this service)
from .memoryService import MemoryService
from .types import MemoryItem, MemoryContext, MemoryStats

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/memory", tags=["memory"])

# Initialize memory service
memory_service = MemoryService()


# Pydantic models (user_id always comes from JWT - no user input needed)
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
    from .config import Config

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


# 🔐 SECURE MEMORY ENDPOINTS - JWT Authentication Required


@router.post("/", response_model=MemoryResponse)
async def process_memory(
    request: MemoryRequest, user_id: str = Depends(get_current_user_id)
):
    """Process a new memory and store it if relevant. User authenticated via JWT."""
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
    request: MemoryContextRequest, user_id: str = Depends(get_current_user_id)
):
    """Get the current memory context for a user. User authenticated via JWT."""
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
async def get_memory_stats(user_id: str = Depends(get_current_user_id)):
    """Get memory statistics for a user. User authenticated via JWT."""
    try:
        stats = await memory_service.get_memory_stats(user_id)
        return MemoryStatsResponse(
            stats=stats, configuration_status=get_configuration_status()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a specific memory. User authenticated via JWT."""
    try:
        success = await memory_service.delete_memory(user_id, memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forget")
async def clear_memories(user_id: str = Depends(get_current_user_id)):
    """Clear all memories for the authenticated user. User authenticated via JWT."""
    try:
        await memory_service.clear_memories(user_id)
        return {"message": "All memories cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent", response_model=ConsentResponse)
async def handle_consent(
    request: ConsentRequest, user_id: str = Depends(get_current_user_id)
):
    """Handle consent decision for a pending memory. User authenticated via JWT."""
    try:
        if request.grant_consent:
            success = await memory_service.grant_consent(user_id, request.memory_id)
            if success:
                return ConsentResponse(
                    success=True,
                    message="Consent granted and memory stored",
                    configuration_status=get_configuration_status(),
                )
            else:
                return ConsentResponse(
                    success=False,
                    message="Failed to process consent",
                    configuration_status=get_configuration_status(),
                )
        else:
            success = await memory_service.deny_consent(user_id, request.memory_id)
            return ConsentResponse(
                success=success,
                message=(
                    "Consent denied and memory discarded"
                    if success
                    else "Memory not found"
                ),
                configuration_status=get_configuration_status(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_memories(user_id: str = Depends(get_current_user_id)):
    """Export all memories for the authenticated user. User authenticated via JWT."""
    try:
        memories = await memory_service.export_memories(user_id)
        return {"memories": memories, "total": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dual-storage", response_model=DualStorageMemoryResponse)
async def process_memory_dual_storage(
    request: MemoryRequest, user_id: str = Depends(get_current_user_id)
):
    """Process memory with dual storage approach. User authenticated via JWT."""
    try:
        result = await memory_service.process_memory_dual_storage(
            user_id=user_id,
            content=request.content,
            type=request.type,
            metadata=request.metadata,
        )

        result["configuration_status"] = get_configuration_status()
        return DualStorageMemoryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dual-storage/consent", response_model=DualStorageConsentResponse)
async def process_memory_with_dual_storage_consent(
    request: DualStorageConsentRequest, user_id: str = Depends(get_current_user_id)
):
    """Process user consent for dual storage memory. User authenticated via JWT."""
    try:
        result = await memory_service.process_dual_storage_consent(
            user_id=user_id,
            memory_id=request.memory_id,
            original_content=request.original_content,
            user_consent=request.user_consent,
            type=request.type,
            metadata=request.metadata,
        )

        result["configuration_status"] = get_configuration_status()
        return DualStorageConsentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotional-anchors")
async def get_emotional_anchors(user_id: str = Depends(get_current_user_id)):
    """Get emotional anchors for the authenticated user. JWT secured."""
    try:
        emotional_anchors = await memory_service.get_emotional_anchors(user_id)
        return {
            "emotional_anchors": [asdict(anchor) for anchor in emotional_anchors],
            "count": len(emotional_anchors),
            "configuration_status": get_configuration_status(),
        }
    except Exception as e:
        logger.error(f"Error getting emotional anchors for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regular-memories")
async def get_regular_memories(
    query: Optional[str] = Query(None, description="Search query for semantic search"),
    user_id: str = Depends(get_current_user_id),
):
    """Get regular lasting memories for the authenticated user. JWT secured."""
    try:
        regular_memories = await memory_service.get_regular_memories(user_id, query)
        return {
            "regular_memories": [asdict(memory) for memory in regular_memories],
            "count": len(regular_memories),
            "query": query,
            "configuration_status": get_configuration_status(),
        }
    except Exception as e:
        logger.error(f"Error getting regular memories for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-long-term")
async def get_all_long_term_memories(user_id: str = Depends(get_current_user_id)):
    """Get all long-term memories categorized by type. JWT secured."""
    try:
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
            "configuration_status": get_configuration_status(),
        }
    except Exception as e:
        logger.error(
            f"Error getting all long-term memories for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-consent")
async def get_pending_consent_memories(user_id: str = Depends(get_current_user_id)):
    """Get memories pending PII consent. JWT secured."""
    try:
        result = await memory_service.get_pending_consent_memories(user_id)
        result["configuration_status"] = get_configuration_status()
        return result
    except Exception as e:
        logger.error(f"Error getting pending consent memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-pending-consent")
async def process_pending_consent(
    request: PendingConsentRequest, user_id: str = Depends(get_current_user_id)
):
    """Process pending memories with user consent decisions. JWT secured."""
    try:
        result = await memory_service.process_pending_consent(
            user_id, request.memory_choices
        )
        result["configuration_status"] = get_configuration_status()
        return result
    except Exception as e:
        logger.error(f"Error processing pending consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Vapi Tool Integration Endpoints
class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)


class MemoryChunk(BaseModel):
    text: str = Field(..., description="Memory content text")
    score: float = Field(..., description="Similarity score")


class MemorySearchResponse(BaseModel):
    chunks: List[MemoryChunk] = Field(..., description="Search results")


class PushMemoryRequest(BaseModel):
    content: str = Field(..., description="Memory content to store")
    type: str = Field("voice_interaction", description="Type of memory")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class PushMemoryResponse(BaseModel):
    success: bool = Field(..., description="Whether memory was stored successfully")
    memory_id: Optional[str] = Field(None, description="ID of stored memory")
    message: str = Field(..., description="Status message")


@router.post("/search", response_model=MemorySearchResponse)
async def memory_search(
    request: MemorySearchRequest, user_id: str = Depends(get_current_user_id)
):
    """Search user's memories using vector similarity. JWT secured."""
    try:
        logger.info(f"Memory search for user {user_id}: {request.query[:50]}...")

        similar_memories = await memory_service.vector_store.similarity_search(
            query=request.query, user_id=user_id, k=request.top_k
        )

        chunks = []
        for memory in similar_memories:
            chunks.append(MemoryChunk(text=memory["content"], score=memory["score"]))

        logger.info(f"Found {len(chunks)} relevant memories for user {user_id}")
        return MemorySearchResponse(chunks=chunks)

    except Exception as e:
        logger.error(f"Memory search failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Memory search service temporarily unavailable: {str(e)}",
        )


@router.post("/push", response_model=PushMemoryResponse)
async def push_memory(
    request: PushMemoryRequest, user_id: str = Depends(get_current_user_id)
):
    """Store a new memory for the user. JWT secured."""
    try:
        logger.info(f"Storing memory for user {user_id}: {request.content[:50]}...")

        result = await memory_service.process_memory(
            user_id=user_id,
            content=request.content,
            type=request.type,
            metadata={
                **request.metadata,
                "source": "vapi_voice_call",
                "stored_via": "memory_api",
            },
        )

        if result.get("stored", False):
            memory_id = None
            components = result.get("components", [])
            if components:
                memory_id = components[0].get("component_memory", {}).get("id")

            return PushMemoryResponse(
                success=True, memory_id=memory_id, message="Memory stored successfully"
            )
        elif result.get("needs_consent", False):
            return PushMemoryResponse(
                success=True,
                memory_id=result.get("memory_id"),
                message="Memory stored in short-term, consent required for long-term storage",
            )
        else:
            return PushMemoryResponse(
                success=False,
                message=result.get(
                    "reason", "Memory not stored - insufficient relevance"
                ),
            )

    except Exception as e:
        logger.error(f"Failed to store memory for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")
