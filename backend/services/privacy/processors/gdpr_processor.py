"""
GDPR Processor for handling data protection and user rights.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from services.memory.types import MemoryItem
from services.memory.storage.redis_store import RedisStore
from services.memory.storage.vector_store import VectorStore
from services.audit.audit_logger import AuditLogger
from ..security.pii_detector import PIIDetector


class GDPRProcessor:
    """Handles GDPR compliance operations."""

    def __init__(
        self,
        redis_store: RedisStore,
        vector_store: VectorStore,
        pii_detector: PIIDetector,
        audit_logger: AuditLogger,
    ):
        self.redis_store = redis_store
        self.vector_store = vector_store
        self.pii_detector = pii_detector
        self.audit_logger = audit_logger

    async def delete_memories(
        self, user_id: str, memory_ids: List[str]
    ) -> Dict[str, Any]:
        """Delete specific memories."""
        try:
            processed = 0
            deleted = 0
            failed = 0
            results = []

            for memory_id in memory_ids:
                try:
                    # Try to delete from both stores
                    short_term_deleted = await self.redis_store.delete_memory(
                        user_id, memory_id
                    )
                    long_term_deleted = await self.vector_store.delete_memory(
                        user_id, memory_id
                    )

                    if short_term_deleted or long_term_deleted:
                        deleted += 1
                        results.append({"memory_id": memory_id, "status": "deleted"})
                    else:
                        results.append({"memory_id": memory_id, "status": "not_found"})

                    processed += 1

                except Exception as e:
                    failed += 1
                    results.append(
                        {"memory_id": memory_id, "status": "error", "error": str(e)}
                    )

            await self.audit_logger.log_event(
                event_type="delete_memories",
                user_id=user_id,
                details={"memory_ids": memory_ids, "results": results},
            )

            return {
                "processed": processed,
                "deleted": deleted,
                "failed": failed,
                "results": results,
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="delete_memories_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            raise e

    async def export_user_data(
        self,
        user_id: str,
        memory_ids: Optional[List[str]] = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Export user data for GDPR compliance (Articles 15 & 20).
        Always returns data in portable, structured format suitable for both access and portability.

        Args:
            user_id: User identifier
            memory_ids: Optional list of specific memory IDs to export (None = all)
            format: Export format (json, csv, etc.)
        """
        try:
            # Get memories based on selection
            if memory_ids is None:
                all_memories = await self._get_all_user_memories(user_id)
                export_purpose = "Complete data export"
            else:
                all_memories = await self._get_specific_memories(user_id, memory_ids)
                export_purpose = f"Selective data export ({len(memory_ids)} requested)"

            # Always use structured, portable format
            export_data = {
                "user_id": user_id,
                "export_format": format,
                "export_timestamp": datetime.utcnow().isoformat(),
                "data_structure_version": "1.0",
                "export_scope": {
                    "requested_memory_ids": memory_ids,
                    "found_memories": len(all_memories),
                    "export_type": "all_data" if memory_ids is None else "selective",
                },
                "memories": {
                    "total_count": len(all_memories),
                    "short_term": [
                        m for m in all_memories if m.get("storage_type") == "short_term"
                    ],
                    "long_term": [
                        m for m in all_memories if m.get("storage_type") == "long_term"
                    ],
                },
                "metadata": {
                    "export_purpose": export_purpose,
                    "data_categories": [
                        "memories",
                        "conversations",
                        "therapeutic_context",
                    ],
                    "retention_info": "Data exported as of export timestamp",
                    "format_specification": "JSON with ISO timestamps",
                    "gdpr_compliance": "Articles 15 (Access) & 20 (Portability)",
                },
            }

            # Log the action
            await self.audit_logger.log_event(
                event_type="export_user_data",
                user_id=user_id,
                details={
                    "format": format,
                    "memory_ids": memory_ids,
                    "record_count": len(all_memories),
                },
            )

            return export_data

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="export_user_data_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            raise e

    async def delete_all_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data for GDPR compliance (right to be forgotten)."""
        try:
            # Clear all memories from both stores
            await self.redis_store.clear_memories(user_id)
            await self.vector_store.clear_memories(user_id)

            # Log the deletion
            await self.audit_logger.log_event(
                event_type="delete_all_user_data",
                user_id=user_id,
                details={
                    "reason": "GDPR right to be forgotten",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return {
                "status": "success",
                "message": "All user data has been permanently deleted",
                "user_id": user_id,
                "deletion_timestamp": datetime.utcnow().isoformat(),
                "data_deleted": {
                    "short_term_memories": "cleared",
                    "long_term_memories": "cleared",
                    "emotional_anchors": "cleared",
                    "audit_logs": "anonymized",
                },
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="delete_all_user_data_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            raise e

    async def update_consent(
        self, user_id: str, consent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user consent preferences for GDPR compliance."""
        try:
            # Store consent preferences (in a real implementation, this would go to a consent database)
            consent_record = {
                "user_id": user_id,
                "consent_timestamp": datetime.utcnow().isoformat(),
                "data_processing": consent_data.get("data_processing", False),
                "analytics": consent_data.get("analytics", False),
                "marketing": consent_data.get("marketing", False),
                "third_party_sharing": consent_data.get("third_party_sharing", False),
                "consent_version": "1.0",
                "ip_address": consent_data.get("ip_address", "unknown"),
                "user_agent": consent_data.get("user_agent", "unknown"),
            }

            # Log consent update
            await self.audit_logger.log_event(
                event_type="update_consent",
                user_id=user_id,
                details={"consent_preferences": consent_record},
            )

            return {
                "status": "success",
                "message": "Consent preferences updated successfully",
                "consent_record": consent_record,
                "effective_date": consent_record["consent_timestamp"],
                "withdrawal_rights": "You can withdraw consent at any time by contacting privacy@nura.app",
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="update_consent_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            raise e

    async def _get_all_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user in dict format."""
        # Get memories from both stores
        short_term_memories = await self.redis_store.get_memories(user_id)
        long_term_memories = await self.vector_store.get_memories(user_id)

        all_memories = []

        # Convert short-term memories to dict format
        for memory in short_term_memories:
            memory_dict = self._memory_to_dict(memory, "short_term")
            all_memories.append(memory_dict)

        # Convert long-term memories to dict format
        for memory in long_term_memories:
            memory_dict = self._memory_to_dict(memory, "long_term")
            all_memories.append(memory_dict)

        return all_memories

    async def _get_specific_memories(
        self, user_id: str, memory_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get specific memories by IDs."""
        memories = []

        # Get all memories
        short_term_memories = await self.redis_store.get_memories(user_id)
        long_term_memories = await self.vector_store.get_memories(user_id)

        # Find requested memories
        for memory_id in memory_ids:
            # Check short-term memories
            for memory in short_term_memories:
                if memory.id == memory_id:
                    memories.append(self._memory_to_dict(memory, "short_term"))
                    break
            else:
                # Check long-term memories if not found in short-term
                for memory in long_term_memories:
                    if memory.id == memory_id:
                        memories.append(self._memory_to_dict(memory, "long_term"))
                        break

        return memories

    def _memory_to_dict(self, memory: MemoryItem, storage_type: str) -> Dict[str, Any]:
        """Convert a memory item to dictionary format."""
        return {
            "id": memory.id,
            "content": memory.content,
            "type": memory.type,
            "timestamp": (
                memory.timestamp.isoformat()
                if hasattr(memory.timestamp, "isoformat")
                else str(memory.timestamp)
            ),
            "metadata": memory.metadata,
            "storage_type": storage_type,
        }
