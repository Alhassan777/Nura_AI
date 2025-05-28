"""
Privacy API Module
Handles privacy review, consent management, and PII-related endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Import services
from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/privacy", tags=["privacy"])

# Initialize memory service
memory_service = MemoryService()


# Pydantic models
class PrivacyChoicesRequest(BaseModel):
    choices: Dict[str, str]  # memory_id -> choice


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


# Privacy endpoints
@router.get("/review/{user_id}")
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


@router.post("/apply-choices/{user_id}")
async def apply_privacy_choices(user_id: str, request: PrivacyChoicesRequest):
    """Apply user privacy choices for memories with PII."""
    try:
        choices = request.choices
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
                            anonymize_consent = {}
                            for item in pii_results.get("detected_items", []):
                                anonymize_consent[item["id"]] = "anonymize"
                                logger.info(
                                    f"Will anonymize: {item['text']} (type: {item['type']})"
                                )

                            anonymized_content = await memory_service.pii_detector.apply_granular_consent(
                                memory.content,
                                storage_location,
                                anonymize_consent,
                                pii_results,
                            )

                            logger.info(f"Original content: {memory.content}")
                            logger.info(f"Anonymized content: {anonymized_content}")

                        # Update the memory with anonymized content
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
                                "has_pii": False,
                                "original_content": memory.content,
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
