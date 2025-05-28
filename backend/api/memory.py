"""
Memory API Module
Handles memory storage, retrieval, and management endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Body
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
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
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
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
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


# Privacy endpoints for testing compatibility
@router.get("/privacy-review/{user_id}")
async def get_privacy_review(
    user_id: str,
    start_date: Optional[str] = Query(
        None, description="Start date filter (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    """Get memories for privacy review with PII analysis."""
    try:
        # Get user memories (this method needs to be implemented)
        memories = await memory_service.get_user_memories(user_id, start_date, end_date)

        # Analyze memories for PII and risk levels
        memories_with_pii = 0
        risk_breakdown = {"high": 0, "medium": 0, "low": 0}
        processed_memories = []

        for memory in memories:
            # Add PII analysis if not already present
            if not memory.get("pii_detected"):
                # Mock PII detection for now - this should use actual PII detector
                memory["pii_detected"] = (
                    "john@example.com" in memory.get("content", "").lower()
                )
                memory["risk_level"] = "high" if memory["pii_detected"] else "low"

            if memory.get("pii_detected"):
                memories_with_pii += 1

            risk_level = memory.get("risk_level", "low")
            risk_breakdown[risk_level] = risk_breakdown.get(risk_level, 0) + 1

            processed_memories.append(memory)

        return {
            "user_id": user_id,
            "total_memories": len(memories),
            "memories_with_pii": memories_with_pii,
            "risk_breakdown": risk_breakdown,
            "memories": processed_memories,
        }

    except Exception as e:
        logger.error(f"Error getting privacy review for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/revoke-consent")
async def revoke_consent_after_storage(
    request: dict, user_id: str = Query(..., description="User ID")
):
    """Revoke consent for already stored memories."""
    try:
        memory_ids = request.get("memory_ids", [])
        revocation_reason = request.get("revocation_reason", "")
        requested_action = request.get("requested_action", "anonymize_or_delete")

        # Use the anonymize_memories method for revocation
        revocation_result = await memory_service.anonymize_memories(
            user_id, memory_ids, ["PERSON", "ADDRESS", "PHONE_NUMBER", "EMAIL_ADDRESS"]
        )

        # Format the response to match the expected structure
        formatted_result = {
            "processed": revocation_result["processed"],
            "modified": revocation_result.get("anonymized", 0),
            "deleted": revocation_result.get("failed", 0),  # Simplified mapping
            "errors": [],
            "results": [
                {
                    "memory_id": result["memory_id"],
                    "action_taken": (
                        "anonymized" if result["status"] == "anonymized" else "deleted"
                    ),
                    "status": (
                        "success"
                        if result["status"] in ["anonymized", "no_matching_pii"]
                        else "error"
                    ),
                    "new_content": result.get("anonymized_content", ""),
                    "reason": result.get("error", "Processed successfully"),
                }
                for result in revocation_result["results"]
            ],
            "gdpr_compliance": {
                "right_exercised": "rectification_and_erasure",
                "processing_time": "immediate",
                "audit_logged": True,
                "user_notification": "Consent revocation processed successfully",
            },
        }

        return formatted_result
    except Exception as e:
        logger.error(f"Error revoking consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-privacy-choices/{user_id}")
async def apply_privacy_choices(user_id: str, request: dict):
    """Apply bulk privacy choices for pending consent memories."""
    try:
        memory_choices = request.get("memory_choices", {})
        bulk_settings = request.get("bulk_settings", {})

        # Process the bulk consent choices
        bulk_result = await memory_service.process_pending_consent(
            user_id, memory_choices
        )

        return bulk_result
    except Exception as e:
        logger.error(f"Error applying privacy choices for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-privacy-choices")
async def apply_privacy_choices_query(
    request: dict, user_id: str = Query(..., description="User ID")
):
    """Apply bulk privacy choices for pending consent memories."""
    try:
        memory_choices = request.get("memory_choices", {})
        bulk_settings = request.get("bulk_settings", {})

        # Process the bulk consent choices
        bulk_result = await memory_service.process_pending_consent(
            user_id, memory_choices
        )

        return bulk_result
    except Exception as e:
        logger.error(f"Error applying privacy choices for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# GDPR Compliance endpoints
@router.get("/gdpr/export/{user_id}")
async def gdpr_data_export(user_id: str):
    """GDPR-compliant data export."""
    try:
        export_data = await memory_service.export_user_data(user_id)
        return export_data.get("export_data", export_data)
    except Exception as e:
        logger.error(f"Error exporting GDPR data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.delete("/gdpr/delete-all/{user_id}")
async def gdpr_right_to_be_forgotten(user_id: str, request: dict = Body(...)):
    """GDPR right to be forgotten (complete data deletion)."""
    try:
        confirmation = request.get("confirmation")
        if confirmation != "I understand this action is irreversible":
            raise HTTPException(status_code=400, detail="Invalid confirmation")

        result = await memory_service.delete_all_user_data(user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GDPR deletion for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/gdpr/portable/{user_id}")
async def gdpr_data_portability(
    user_id: str, format: str = Query("json", description="Export format")
):
    """GDPR data portability in machine-readable format."""
    try:
        portable_data = await memory_service.export_portable_data(user_id, format)
        return portable_data
    except Exception as e:
        logger.error(f"Error exporting portable data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/gdpr/consent/{user_id}")
async def gdpr_consent_management(user_id: str, request: dict):
    """GDPR consent management."""
    try:
        result = await memory_service.update_consent(user_id, request)
        return result
    except Exception as e:
        logger.error(f"Error updating consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/gdpr/retention-policy")
async def gdpr_data_retention_policy():
    """Get GDPR data retention policy information."""
    return {
        "retention_periods": {
            "short_term_memories": "Session-based (cleared on logout)",
            "long_term_memories": "7 years (therapeutic records)",
            "pii_data": "As long as associated memory exists",
            "audit_logs": "7 years (compliance requirement)",
            "consent_records": "7 years (legal requirement)",
        },
        "deletion_triggers": [
            "User request (right to be forgotten)",
            "Account deletion",
            "Retention period expiry",
            "Data minimization review",
        ],
        "data_categories": {
            "essential": "Required for service functionality",
            "therapeutic": "Mental health insights and progress",
            "operational": "System logs and performance data",
            "compliance": "Audit trails and consent records",
        },
        "user_rights": [
            "Right to access (Article 15)",
            "Right to rectification (Article 16)",
            "Right to erasure (Article 17)",
            "Right to data portability (Article 20)",
            "Right to object (Article 21)",
        ],
        "contact": {
            "data_protection_officer": "dpo@nura.ai",
            "privacy_team": "privacy@nura.ai",
        },
    }


# Additional consent management endpoints
@router.get("/expired-consents")
async def get_expired_consent_requests(
    user_id: str = Query(..., description="User ID")
):
    """Get consent requests that have expired."""
    try:
        expired_consents = await memory_service.get_expired_consent_requests(user_id)
        return expired_consents
    except Exception as e:
        logger.error(f"Error getting expired consents for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent-history")
async def get_consent_audit_trail(user_id: str = Query(..., description="User ID")):
    """Get audit trail of consent decisions for a user."""
    try:
        audit_trail = await memory_service.get_consent_audit_trail(user_id)
        return audit_trail
    except Exception as e:
        logger.error(f"Error getting consent audit trail for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent-preview")
async def preview_consent_choices(
    request: dict, user_id: str = Query(..., description="User ID")
):
    """Preview how content will look with different consent choices."""
    try:
        content = request.get("content", "")
        preview_options = request.get("preview_options", {})

        preview_result = await memory_service.preview_consent_choices(
            user_id, content, preview_options
        )
        return preview_result
    except Exception as e:
        logger.error(f"Error previewing consent choices for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent-recommendations")
async def get_consent_recommendations(
    request: dict, user_id: str = Query(..., description="User ID")
):
    """Get AI-powered consent recommendations based on user preferences."""
    try:
        content = request.get("content", "")
        user_preferences = request.get("user_preferences", {})

        recommendations = await memory_service.get_consent_recommendations(
            user_id, content, user_preferences
        )
        return recommendations
    except Exception as e:
        logger.error(
            f"Error getting consent recommendations for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))
