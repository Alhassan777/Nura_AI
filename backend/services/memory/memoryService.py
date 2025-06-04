"""
Memory Service - Central memory management orchestrator.

This service handles the complete memory processing workflow:
1. Creating base memory items from user input
2. Processing memory components (conversation chunks, themes, insights)
3. Scoring components for relevance and permanence
4. Dual storage strategy (short-term Redis + long-term vector store)
5. PII detection and user consent management
6. Privacy-compliant retrieval and GDPR operations
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dataclasses import asdict

from .types import MemoryItem, MemoryScore, MemoryContext, MemoryConfig, MemoryStats
from .storage.redis_store import RedisStore
from .storage.vector_store import VectorStore
from utils.scoring.gemini_scorer import GeminiScorer
from ..privacy.security.pii_detector import PIIDetector
from services.audit.audit_logger import AuditLogger
from .config import Config

# Import processors (now in memory service root)
from .memory_processor import MemoryProcessor
from .storage_processor import StorageProcessor
from .retrieval_processor import RetrievalProcessor
from ..privacy.processors.privacy_processor import PrivacyProcessor
from ..privacy.processors.gdpr_processor import GDPRProcessor


class MemoryService:
    """Main memory service orchestrator using modular processors."""

    def __init__(self):
        # Validate configuration (remove JWT validation for now)
        try:
            Config.validate()
            Config.check_optional_config()  # Check and warn about optional settings
        except ValueError as e:
            # Allow JWT-related validation errors since we're not using auth
            if "JWT" not in str(e):
                raise e

        # Initialize components
        self.redis_store = RedisStore()

        # Initialize vector store based on configuration
        self.vector_store = VectorStore(
            persist_directory=Config.CHROMA_PERSIST_DIR,
            use_pinecone=Config.USE_PINECONE,
            vector_db_type=Config.VECTOR_DB_TYPE,
        )

        self.scorer = GeminiScorer()
        self.pii_detector = PIIDetector()
        self.audit_logger = AuditLogger()

        # Initialize configuration
        self.config = MemoryConfig(**Config.get_memory_config())

        # Initialize processors
        self.memory_processor = MemoryProcessor(
            self.scorer, self.pii_detector, self.audit_logger
        )
        self.storage_processor = StorageProcessor(
            self.redis_store, self.vector_store, self.pii_detector, self.audit_logger
        )
        self.retrieval_processor = RetrievalProcessor(
            self.redis_store, self.vector_store, self.audit_logger
        )
        self.privacy_processor = PrivacyProcessor(
            self.redis_store, self.vector_store, self.pii_detector, self.audit_logger
        )
        self.gdpr_processor = GDPRProcessor(
            self.redis_store, self.vector_store, self.pii_detector, self.audit_logger
        )

    async def process_memory(
        self,
        user_id: str,
        content: str,
        type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
        user_consent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a new memory item with dual storage strategy."""
        # Create base memory
        base_memory = self.memory_processor.create_base_memory(
            user_id, content, type, metadata
        )

        # For chat messages, always store in short-term first, handle PII later
        is_chat_message = self.memory_processor.is_chat_message(type, metadata)

        # Always detect PII but handle it differently for chat vs non-chat
        pii_results = await self.pii_detector.detect_pii(base_memory)

        if is_chat_message:
            # For chat messages: store in short-term immediately, defer PII consent for long-term
            # This ensures chat flow is never interrupted
            pass  # Continue processing, PII will be handled during long-term storage
        else:
            # For non-chat memories, require immediate PII consent if detected
            if pii_results["has_pii"] and user_consent is None:
                consent_options = self.pii_detector.get_granular_consent_options(
                    pii_results
                )
                return {
                    "needs_consent": True,
                    "consent_options": consent_options,
                    "memory_id": base_memory.id,
                    "original_content": content,
                    "pii_results": pii_results,
                }

        # Process memory components
        component_results = await self.memory_processor.process_memory_components(
            base_memory, pii_results, user_consent
        )

        # If no components to store, return early
        if not component_results.get("stored"):
            return component_results

        # Store components that meet criteria
        stored_components = []
        for component_result in component_results["components"]:
            if component_result.get("stored") and component_result.get(
                "component_memory"
            ):
                component_memory = component_result["component_memory"]

                # Get the score for this component
                score = MemoryScore(
                    relevance=component_result["score"]["relevance"],
                    stability=component_result["score"]["stability"],
                    explicitness=component_result["score"]["explicitness"],
                    metadata={
                        "memory_type": component_result["memory_type"],
                        "storage_recommendation": component_result[
                            "storage_recommendation"
                        ],
                        "component_content": component_result["component_content"],
                    },
                )

                # Store using dual strategy
                storage_result = await self.storage_processor.store_with_dual_strategy(
                    user_id, component_memory, score, pii_results, user_consent or {}
                )

                # Merge storage result with component result
                component_result.update(storage_result)
                stored_components.append(component_result)

        # Update the final result
        component_results["stored_components"] = len(stored_components)
        component_results["components"] = [
            c for c in component_results["components"] if c.get("stored")
        ]

        return component_results

    async def process_memory_with_consent(
        self,
        user_id: str,
        memory_id: str,
        original_content: str,
        user_consent: Dict[str, Any],
        type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a memory that previously required consent."""
        return await self.process_memory(
            user_id=user_id,
            content=original_content,
            type=type,
            metadata=metadata,
            user_consent=user_consent,
        )

    # Retrieval methods - delegate to retrieval processor
    async def get_memory_context(
        self, user_id: str, query: Optional[str] = None
    ) -> MemoryContext:
        """Get memory context for a user."""
        return await self.retrieval_processor.get_memory_context(user_id, query)

    async def get_memory_stats(self, user_id: str) -> MemoryStats:
        """Get memory statistics for a user."""
        return await self.retrieval_processor.get_memory_stats(user_id)

    async def get_emotional_anchors(self, user_id: str) -> List[MemoryItem]:
        """Get emotional anchors (meaningful connections) for a user."""
        return await self.retrieval_processor.get_emotional_anchors(user_id)

    async def get_regular_memories(
        self, user_id: str, query: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get regular lasting memories (excluding emotional anchors) for a user."""
        return await self.retrieval_processor.get_regular_memories(user_id, query)

    async def get_user_memories(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user with optional date filtering."""
        return await self.retrieval_processor.get_user_memories(
            user_id, start_date, end_date
        )

    # Basic memory operations
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        # Try deleting from both stores
        deleted = await self.redis_store.delete_memory(user_id, memory_id)
        if not deleted:
            deleted = await self.vector_store.delete_memory(user_id, memory_id)

        if deleted:
            # Log deletion
            await self.audit_logger.log_memory_deleted(
                user_id=user_id,
                memory=MemoryItem(
                    id=memory_id,
                    userId=user_id,
                    content="[DELETED]",
                    type="deleted",
                    metadata={},
                    timestamp=datetime.utcnow(),
                ),
            )

        return deleted

    async def clear_memories(self, user_id: str) -> None:
        """Clear all memories for a user."""
        # Get count before clearing for logging
        stats = await self.get_memory_stats(user_id)

        # Clear both stores
        await self.redis_store.clear_memories(user_id)
        await self.vector_store.clear_memories(user_id)

        # Log clearing
        await self.audit_logger.log_memory_cleared(user_id=user_id, count=stats.total)

    # Privacy methods - delegate to privacy processor
    async def get_pending_consent_memories(self, user_id: str) -> Dict[str, Any]:
        """Get memories that are pending PII consent for long-term storage."""
        return await self.privacy_processor.get_pending_consent_memories(user_id)

    async def process_pending_consent(
        self,
        user_id: str,
        memory_choices: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process pending memories with user consent decisions."""
        return await self.privacy_processor.process_pending_consent(
            user_id, memory_choices
        )

    async def anonymize_memories(
        self, user_id: str, memory_ids: List[str], pii_types: List[str]
    ) -> Dict[str, Any]:
        """Anonymize specific PII types in selected memories."""
        return await self.privacy_processor.anonymize_memories(
            user_id, memory_ids, pii_types
        )

    # GDPR methods - delegate to GDPR processor
    async def delete_memories(
        self, user_id: str, memory_ids: List[str]
    ) -> Dict[str, Any]:
        """Delete specific memories."""
        return await self.gdpr_processor.delete_memories(user_id, memory_ids)

    async def export_user_data(
        self, user_id: str, memory_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export user data for GDPR compliance (Articles 15 & 20)."""
        return await self.gdpr_processor.export_user_data(
            user_id=user_id, memory_ids=memory_ids
        )

    async def delete_all_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data for GDPR compliance (right to be forgotten)."""
        return await self.gdpr_processor.delete_all_user_data(user_id)

    async def export_portable_data(
        self, user_id: str, format: str = "json"
    ) -> Dict[str, Any]:
        """Export user data in portable format for GDPR compliance."""
        return await self.gdpr_processor.export_user_data(
            user_id=user_id, format=format
        )

    async def update_consent(
        self, user_id: str, consent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user consent preferences for GDPR compliance."""
        return await self.gdpr_processor.update_consent(user_id, consent_data)

    # Consent management methods
    async def get_expired_consent_requests(self, user_id: str) -> Dict[str, Any]:
        """Get consent requests that have expired."""
        return await self.privacy_processor.get_expired_consent_requests(user_id)

    async def get_consent_audit_trail(self, user_id: str) -> Dict[str, Any]:
        """Get audit trail of consent decisions for a user."""
        return await self.privacy_processor.get_consent_audit_trail(user_id)

    async def preview_consent_choices(
        self, user_id: str, content: str, preview_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview how content will look with different consent choices."""
        return await self.privacy_processor.preview_consent_choices(
            user_id, content, preview_options
        )

    async def get_consent_recommendations(
        self, user_id: str, content: str, user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-powered consent recommendations based on user preferences."""
        return await self.privacy_processor.get_consent_recommendations(
            user_id, content, user_preferences
        )

    # Legacy methods for backward compatibility
    async def get_chat_session_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of chat memories for user review and selection."""
        # Get all short-term memories (chat session)
        short_term_memories = await self.redis_store.get_user_memories(user_id)

        # Filter for chat messages only
        chat_memories = [
            memory
            for memory in short_term_memories
            if memory.metadata.get("source") == "chat_interface"
        ]

        if not chat_memories:
            return {
                "session_summary": "No chat memories found in this session.",
                "memories": [],
                "total_count": 0,
            }

        # Analyze each memory for PII and therapeutic value
        memory_summaries = []
        for memory in chat_memories:
            # Run PII detection for review
            pii_results = await self.pii_detector.detect_pii(memory)

            # Get therapeutic score
            score = self.scorer.score_memory(memory)[0]  # Get first component

            memory_summary = {
                "id": memory.id,
                "content": memory.content,
                "type": memory.type,
                "timestamp": memory.timestamp.isoformat(),
                "therapeutic_value": {
                    "relevance": round(score.relevance, 2),
                    "stability": round(score.stability, 2),
                    "explicitness": round(score.explicitness, 2),
                    "overall_score": round(
                        (score.relevance + score.stability + score.explicitness) / 3, 2
                    ),
                },
                "privacy_info": {
                    "has_sensitive_info": pii_results["has_pii"],
                    "detected_types": list(
                        set(
                            item["type"]
                            for item in pii_results.get("detected_items", [])
                        )
                    ),
                    "sensitive_items": [
                        {
                            "text": item["text"],
                            "type": item["type"],
                            "risk_level": item["risk_level"],
                        }
                        for item in pii_results.get("detected_items", [])
                    ],
                },
                "recommended_action": self.privacy_processor.get_memory_recommendation(
                    score, pii_results
                ),
                "user_choice": "pending",  # Will be filled by user
            }
            memory_summaries.append(memory_summary)

        # Sort by timestamp (most recent first)
        memory_summaries.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "session_summary": f"Found {len(chat_memories)} memories from this chat session.",
            "memories": memory_summaries,
            "total_count": len(chat_memories),
            "instructions": {
                "keep": "Save to long-term memory for future conversations",
                "remove": "Delete completely",
                "anonymize": "Keep but remove sensitive information",
            },
        }

    async def apply_user_memory_choices(
        self,
        user_id: str,
        memory_choices: Dict[str, str],  # memory_id -> "keep"|"remove"|"anonymize"
    ) -> Dict[str, Any]:
        """Apply user choices about which memories to keep, remove, or anonymize."""
        results = {"kept": [], "removed": [], "anonymized": [], "errors": []}

        # Get current short-term memories
        short_term_memories = await self.redis_store.get_user_memories(user_id)

        for memory in short_term_memories:
            choice = memory_choices.get(memory.id, "keep")  # Default to keep

            try:
                if choice == "remove":
                    # Delete from short-term
                    await self.redis_store.delete_memory(user_id, memory.id)
                    results["removed"].append(memory.id)

                elif choice == "anonymize":
                    # Detect PII and anonymize
                    pii_results = await self.pii_detector.detect_pii(memory)
                    anonymized_content = await self.pii_detector.apply_granular_consent(
                        memory.content, "long_term", {}, pii_results
                    )

                    # Create anonymized version for long-term storage
                    if anonymized_content != memory.content:
                        long_term_memory = MemoryItem(
                            id=memory.id + "_long",
                            userId=user_id,
                            content=anonymized_content,
                            type=memory.type,
                            metadata={
                                **memory.metadata,
                                "storage_type": "long_term",
                                "anonymized": True,
                                "original_memory_id": memory.id,
                            },
                            timestamp=memory.timestamp,
                        )

                        await self.vector_store.add_memory(user_id, long_term_memory)
                        results["anonymized"].append(memory.id)
                    else:
                        # No PII found, treat as keep
                        choice = "keep"

                if choice == "keep":
                    # Move to long-term storage as-is
                    long_term_memory = MemoryItem(
                        id=memory.id + "_long",
                        userId=user_id,
                        content=memory.content,
                        type=memory.type,
                        metadata={
                            **memory.metadata,
                            "storage_type": "long_term",
                            "user_approved": True,
                            "original_memory_id": memory.id,
                        },
                        timestamp=memory.timestamp,
                    )

                    await self.vector_store.add_memory(user_id, long_term_memory)
                    results["kept"].append(memory.id)

            except Exception as e:
                results["errors"].append({"memory_id": memory.id, "error": str(e)})

        # Clear short-term memories after processing
        await self.redis_store.clear_memories(user_id)

        return results
