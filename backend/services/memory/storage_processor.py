"""
Storage processor for memory persistence and retrieval.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict
import logging
import uuid

from .types import MemoryItem, MemoryScore
from .storage.redis_store import RedisStore
from .storage.vector_store import VectorStore
from ..privacy.security.pii_detector import PIIDetector
from services.audit.audit_logger import AuditLogger
from .config import Config
from ..privacy.processors.privacy_processor import PrivacyProcessor


class StorageProcessor:
    """Handles dual storage strategy for memories."""

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

    async def store_with_dual_strategy(
        self,
        user_id: str,
        base_memory: MemoryItem,
        score: MemoryScore,
        pii_results: Dict[str, Any],
        user_consent: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Store memory using basic dual strategy - simple long-term vs short-term storage.

        Basic rule:
        - Store everything in short-term (Redis) for immediate conversation context
        - Store in long-term (vector store) if classified as "long_term" or "emotional_anchor"
        """
        stored_memories = {}
        pending_consent = False

        # Get memory classification from the score metadata
        score_metadata = score.metadata or {}

        # Use simple structure only
        memory_category = score_metadata.get("memory_category", "short_term")
        is_meaningful = score_metadata.get("is_meaningful", False)
        is_lasting = score_metadata.get("is_lasting", False)
        is_symbolic = score_metadata.get("is_symbolic", False)

        # Simple storage decision - if classified as long-term or emotional anchor, store it
        will_store_long_term = memory_category in ["long_term", "emotional_anchor"]

        # Check user privacy preferences for long-term storage
        user_privacy_settings = self._get_user_privacy_settings(user_consent, user_id)
        if not user_privacy_settings["allow_long_term_storage"]:
            will_store_long_term = False
            logging.getLogger(__name__).info(
                f"User {user_id} has disabled long-term storage"
            )

        # Create basic metadata
        memory_metadata = self._create_memory_metadata(
            base_memory,
            user_id,
            score,
            memory_category,
            is_meaningful,
            is_lasting,
            is_symbolic,
            storage_type="short_term",
        )

        # Always create a short-term memory for immediate conversation context
        short_term_memory = MemoryItem(
            id=base_memory.id,
            content=base_memory.content,
            type=base_memory.type,
            metadata=memory_metadata,
            timestamp=base_memory.timestamp,
        )

        # Store in Redis for immediate context
        await self.redis_store.store_memory(user_id, short_term_memory)
        stored_memories["short_term"] = short_term_memory

        # Long-term storage logic
        if will_store_long_term:
            if pii_results["has_pii"]:
                # Handle PII with care while preserving meaning
                await self._handle_pii_for_long_term_storage(
                    user_id,
                    base_memory,
                    score,
                    pii_results,
                    user_consent,
                    user_privacy_settings,
                    stored_memories,
                    score_metadata,
                )
            else:
                # No PII - store the memory as-is
                await self._store_long_term(
                    user_id, base_memory, score_metadata, stored_memories
                )

        # Log the basic storage decision
        await self._log_storage_decision(
            user_id, base_memory, memory_category, will_store_long_term, pii_results
        )

        return {
            "stored": True,
            "storage_details": {
                "short_term": bool(stored_memories.get("short_term")),
                "long_term": bool(stored_memories.get("long_term")),
                "memory_category": memory_category,
                "will_be_stored_long_term": will_store_long_term,
                "pending_consent": pending_consent,
            },
            "stored_memories": stored_memories,
        }

    def _is_low_risk_pii(self, pii_results: Dict[str, Any]) -> bool:
        """Check if detected PII is low-risk and safe for therapeutic storage."""
        if not pii_results.get("has_pii", False):
            return True  # No PII is always safe

        # Define low-risk PII types that are safe for therapeutic conversations
        low_risk_types = {
            "LOCATION",
            "MISC",
            "ORG",
            "DATE_TIME",
        }  # Cities, organizations, dates/times etc.
        high_risk_types = {
            "PERSON",
            "PHONE",
            "EMAIL",
            "SSN",
            "CREDIT_CARD",
        }  # Personal identifiers

        has_high_risk_pii = False

        for pii_item in pii_results.get("detected_items", []):
            pii_type = pii_item.get("type", "").upper()
            risk_level = pii_item.get("risk_level", "high")
            confidence = pii_item.get("confidence", 1.0)

            # Check if this specific PII item is high-risk
            if pii_type in high_risk_types:
                # For therapeutic context, be more permissive with person names
                if pii_type == "PERSON":
                    pii_text = pii_item.get("text", "").lower()
                    # Allow common assistant names, nicknames, or low-confidence names
                    if (
                        pii_text in ["nura", "assistant", "ai", "bot", "chatbot"]
                        or confidence < 0.90
                    ):
                        continue
                has_high_risk_pii = True
                break

            # High-risk level with high confidence is not auto-approved
            if risk_level == "high" and confidence > 0.8:
                has_high_risk_pii = True
                break

        # Return True if no high-risk PII found
        return not has_high_risk_pii

    def _check_high_risk_pii(
        self, component_content: str, pii_results: Dict[str, Any]
    ) -> bool:
        """Check if component content has high-risk PII."""
        if not pii_results.get("has_pii", False):
            return False

        for pii_item in pii_results.get("detected_items", []):
            pii_text = pii_item.get("text", "")
            if (
                pii_text.lower() in component_content.lower()
                and pii_item.get("risk_level") == "high"
            ):
                return True
        return False

    def _get_user_privacy_settings(
        self, user_consent: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Get user privacy preferences with gentle defaults that preserve healing stories."""
        # Default to story-preserving settings
        default_settings = {
            "allow_long_term_storage": True,
            "auto_anonymize_pii": False,  # Let users decide on meaningful connections
            "preserve_emotional_anchors": True,
            "require_consent_for_sensitive_stories": True,
        }

        # In a full implementation, this would fetch from user preferences database
        # For now, use consent data and sensible defaults
        return {**default_settings, **user_consent.get("privacy_settings", {})}

    async def _handle_pii_for_long_term_storage(
        self,
        user_id: str,
        base_memory: MemoryItem,
        score: MemoryScore,
        pii_results: Dict[str, Any],
        user_consent: Dict[str, Any],
        user_privacy_settings: Dict[str, Any],
        stored_memories: Dict[str, MemoryItem],
        score_metadata: Dict[str, Any],
    ):
        """Handle PII in stories that want to be treasured long-term."""
        memory_category = score_metadata.get("memory_category", "short_term")

        # Check if PII is low-risk and can be auto-approved
        is_low_risk_pii = self._is_low_risk_pii(pii_results)

        if user_privacy_settings["auto_anonymize_pii"] or is_low_risk_pii:
            if is_low_risk_pii and memory_category == "emotional_anchor":
                # For emotional anchors with low-risk PII, preserve therapeutic value
                await self._store_long_term(
                    user_id,
                    base_memory,
                    score_metadata,
                    stored_memories,
                    pii_handling="low_risk_preserved",
                )
                logging.getLogger(__name__).info(
                    f"Preserved low-risk PII in emotional anchor for user {user_id} - therapeutic value maintained"
                )
            else:
                # Auto-anonymize PII while preserving story essence
                anonymized_content = await self._anonymize_while_preserving_meaning(
                    base_memory.content, pii_results, memory_category
                )

                await self._store_long_term(
                    user_id,
                    base_memory,
                    score_metadata,
                    stored_memories,
                    content_override=anonymized_content,
                    pii_handling="auto_anonymized",
                )
                logging.getLogger(__name__).info(
                    f"Auto-anonymized story while preserving meaning for user {user_id}"
                )
        else:
            # User wants manual control - defer to consent
            stored_memories["short_term"].metadata["pending_long_term_consent"] = True
            stored_memories["short_term"].metadata["pii_detected"] = True
            stored_memories["short_term"].metadata["requires_consent"] = True
            await self.redis_store.store_memory(user_id, stored_memories["short_term"])

            logging.getLogger(__name__).info(
                f"Deferred treasuring story for user {user_id} - manual PII consent needed"
            )

    async def _store_long_term(
        self,
        user_id: str,
        base_memory: MemoryItem,
        score_metadata: Dict[str, Any],
        stored_memories: Dict[str, MemoryItem],
        content_override: str = None,
        pii_handling: str = "no_pii_detected",
    ):
        """Store a meaningful memory in long-term storage with same metadata as short-term."""

        # Get the simple classification from Gemini
        memory_category = score_metadata.get("memory_category", "short_term")
        is_meaningful = score_metadata.get("is_meaningful", False)
        is_lasting = score_metadata.get("is_lasting", False)
        is_symbolic = score_metadata.get("is_symbolic", False)

        # Get the score from the short-term memory to maintain consistency
        short_term_metadata = stored_memories["short_term"].metadata
        mock_score = type(
            "MockScore",
            (),
            {
                "relevance": short_term_metadata.get("relevance_score", 0.5),
                "stability": short_term_metadata.get("stability_score", 0.5),
                "explicitness": short_term_metadata.get("explicitness_score", 0.5),
            },
        )()

        # Create identical metadata, just changing storage_type
        long_term_metadata = self._create_memory_metadata(
            base_memory,
            user_id,
            mock_score,
            memory_category,
            is_meaningful,
            is_lasting,
            is_symbolic,
            storage_type="long_term",
        )

        # Add PII handling info
        long_term_metadata["pii_handling"] = pii_handling

        long_term_memory = MemoryItem(
            id=base_memory.id + "_treasured",
            content=content_override or base_memory.content,
            type=base_memory.type,
            metadata=long_term_metadata,
            timestamp=base_memory.timestamp,
        )

        await self.vector_store.store_memory(user_id, long_term_memory)
        stored_memories["long_term"] = long_term_memory

        logging.getLogger(__name__).info(
            f"Stored long-term memory for user {user_id}: {long_term_memory.metadata['memory_category']}"
        )

    async def _anonymize_while_preserving_meaning(
        self, content: str, pii_results: Dict[str, Any], memory_category: str
    ) -> str:
        """Anonymize PII while preserving the emotional and therapeutic essence of the story."""
        # For emotional anchors and meaningful stories, use gentler anonymization
        if memory_category == "emotional_anchor":
            # Use descriptive replacements for places and names to preserve emotional connection
            auto_consent = {}
            for item in pii_results.get("detected_items", []):
                if item["type"] in ["person_name", "location"]:
                    auto_consent[item["id"]] = (
                        "descriptive"  # "My hometown" instead of "[LOCATION REMOVED]"
                    )
                else:
                    auto_consent[item["id"]] = "anonymize"
        else:
            # Standard anonymization for other story types
            auto_consent = {}
            for item in pii_results.get("detected_items", []):
                auto_consent[item["id"]] = "anonymize"

        return await self.pii_detector.apply_granular_consent(
            content, "long_term", auto_consent, pii_results
        )

    async def _log_storage_decision(
        self,
        user_id: str,
        base_memory: MemoryItem,
        memory_category: str,
        will_store_long_term: bool,
        pii_results: Dict[str, Any],
    ):
        """Log storage decisions using basic, story-centered language."""
        decision_summary = {
            "user_id": user_id,
            "memory_category": memory_category,
            "stored_long_term": will_store_long_term,
            "story_length": len(base_memory.content),
            "has_sensitive_info": pii_results["has_pii"],
            "basic_processing": True,
        }

        if pii_results["has_pii"]:
            await self.audit_logger.log_pii_detected(
                user_id=user_id,
                memory=base_memory,
                pii_types=[
                    item["type"] for item in pii_results.get("detected_items", [])
                ],
                metadata={
                    **decision_summary,
                    "detected_items": pii_results.get("detected_items", []),
                },
            )

        # Log the basic decision
        await self.audit_logger.log_event(
            event_type="basic_memory_processing",
            user_id=user_id,
            level="INFO",
            details=decision_summary,
        )

    def _is_meaningful(
        self, is_meaningful: bool, is_lasting: bool, is_symbolic: bool
    ) -> bool:
        """Check if memory is meaningful - simplified"""
        return is_meaningful

    def _is_lasting(self, is_lasting: bool) -> bool:
        """Check if memory is lasting - simplified"""
        return is_lasting

    def _is_symbolic(self, is_symbolic: bool) -> bool:
        """Check if memory is symbolic - simplified"""
        return is_symbolic

    def _is_meaningful_for_classification(
        self, is_meaningful: bool, is_lasting: bool
    ) -> bool:
        """Simplified meaningful check for classification"""
        return is_meaningful

    def _is_lasting_for_classification(self, memory_category: str) -> bool:
        """Simplified lasting check for classification"""
        return memory_category != "short_term"

    def _create_memory_metadata(
        self,
        base_memory: MemoryItem,
        user_id: str,
        score: MemoryScore,
        memory_category: str,
        is_meaningful: bool,
        is_lasting: bool,
        is_symbolic: bool,
        storage_type: str,
    ) -> Dict[str, Any]:
        """Create a common metadata for both short-term and long-term memories."""
        metadata = {
            **base_memory.metadata,
            "user_id": user_id,
            "storage_type": storage_type,
            "created_at": datetime.utcnow().isoformat(),
            # SIMPLE CLASSIFICATION - use Gemini's classification directly
            "memory_category": memory_category,
            "is_meaningful": is_meaningful,
            "is_lasting": is_lasting,
            "is_symbolic": is_symbolic,
            # Clean scores
            "relevance_score": float(score.relevance),
            "stability_score": float(score.stability),
            "explicitness_score": float(score.explicitness),
        }
        return metadata
