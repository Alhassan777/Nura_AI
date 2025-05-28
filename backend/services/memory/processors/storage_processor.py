"""
Storage processor for dual storage strategy.
Handles short-term and long-term storage with PII considerations.
"""

from typing import Dict, Any
from dataclasses import asdict

from ..types import MemoryItem, MemoryScore
from ..storage.redis_store import RedisStore
from ..storage.vector_store import VectorStore
from ..security.pii_detector import PIIDetector
from ..audit.audit_logger import AuditLogger
from ..config import Config


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
        """Store memory using dual strategy (different handling for short-term vs long-term)."""

        # Determine storage destinations based on memory type classification
        will_store_short_term = True  # Almost always store in short-term for context

        # Check if this is a lasting memory or meaningful connection that should be stored long-term
        score_metadata = score.metadata or {}
        memory_type = score_metadata.get("memory_type", "temporary_state")
        storage_recommendation = score_metadata.get(
            "storage_recommendation", "probably_skip"
        )

        # Only store in long-term if it's explicitly a lasting memory or meaningful connection
        should_store_long_term = memory_type in [
            "lasting_memory",
            "meaningful_connection",
        ] and storage_recommendation in ["definitely_save", "probably_save"]

        # For chat messages with PII: be more granular about consent requirements
        is_chat_message = base_memory.type in [
            "user_message",
            "assistant_message",
            "chat",
        ]
        has_pii = pii_results.get("has_pii", False)

        # Check if this specific component content has high-risk PII that requires consent
        component_content = score_metadata.get("component_content", base_memory.content)
        component_has_high_risk_pii = self._check_high_risk_pii(
            component_content, pii_results
        )

        # Determine if we need to defer long-term storage for this specific component
        if (
            is_chat_message
            and component_has_high_risk_pii
            and should_store_long_term
            and not user_consent
        ):
            # Only defer if this component actually contains high-risk PII
            will_store_long_term = False  # Defer until consent
            pending_consent = True
        else:
            # Store normally - either no PII, low-risk PII, or consent provided
            will_store_long_term = should_store_long_term
            pending_consent = False

        stored_memories = {}

        # STEP 1: Store in SHORT-TERM (Redis) - more permissive with PII
        if will_store_short_term:
            short_term_memory = await self._store_short_term(
                user_id,
                base_memory,
                score,
                pii_results,
                user_consent,
                component_content,
                has_pii,
                component_has_high_risk_pii,
                pending_consent,
                should_store_long_term,
                memory_type,
                storage_recommendation,
            )
            stored_memories["short_term"] = short_term_memory

        # STEP 2: Store in LONG-TERM (Vector DB) - more conservative with PII
        if will_store_long_term:
            long_term_memory = await self._store_long_term(
                user_id,
                base_memory,
                score,
                pii_results,
                user_consent,
                component_content,
                has_pii,
                component_has_high_risk_pii,
                score_metadata,
            )
            stored_memories["long_term"] = long_term_memory

        # Log PII detection and handling
        if pii_results["has_pii"]:
            await self.audit_logger.log_pii_detected(
                user_id=user_id,
                memory=base_memory,
                pii_types=[
                    item["type"] for item in pii_results.get("detected_items", [])
                ],
                metadata={
                    "dual_storage_strategy": True,
                    "short_term_stored": will_store_short_term,
                    "long_term_stored": will_store_long_term,
                    "user_consent": user_consent,
                    "detected_items": pii_results.get("detected_items", []),
                },
            )

        return {
            "needs_consent": False,
            "stored": True,
            "storage_details": {
                "short_term": will_store_short_term,
                "long_term": will_store_long_term,
                "privacy_strategy": "dual_storage",
                "vector_database": Config.VECTOR_DB_TYPE,
                "pending_consent": pending_consent,
                "consent_reason": (
                    "PII detected in chat message - long-term storage deferred"
                    if pending_consent
                    else None
                ),
            },
            "stored_memories": {k: asdict(v) for k, v in stored_memories.items()},
            "score": {
                "relevance": float(score.relevance),
                "stability": float(score.stability),
                "explicitness": float(score.explicitness),
            },
            "pii_summary": {
                "detected": pii_results["has_pii"],
                "types": list(
                    set(item["type"] for item in pii_results.get("detected_items", []))
                ),
                "items": len(pii_results.get("detected_items", [])),
                "handling": "granular_per_item",
                "consent_deferred": pending_consent,
            },
        }

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

    async def _store_short_term(
        self,
        user_id: str,
        base_memory: MemoryItem,
        score: MemoryScore,
        pii_results: Dict[str, Any],
        user_consent: Dict[str, Any],
        component_content: str,
        has_pii: bool,
        component_has_high_risk_pii: bool,
        pending_consent: bool,
        should_store_long_term: bool,
        memory_type: str,
        storage_recommendation: str,
    ) -> MemoryItem:
        """Store memory in short-term storage (Redis)."""
        short_term_content = await self.pii_detector.apply_granular_consent(
            component_content, "short_term", user_consent, pii_results
        )

        short_term_memory = MemoryItem(
            id=base_memory.id + "_short",
            userId=user_id,
            content=short_term_content,
            type=base_memory.type,
            metadata={
                **base_memory.metadata,
                "storage_type": "short_term",
                "has_pii": has_pii,
                "component_has_high_risk_pii": component_has_high_risk_pii,
                "detected_items": [
                    item["id"] for item in pii_results.get("detected_items", [])
                ],
                "score": {
                    "relevance": float(score.relevance),
                    "stability": float(score.stability),
                    "explicitness": float(score.explicitness),
                },
                "pii_strategy": "permissive_for_personalization",
                # Add pending consent information
                "pending_long_term_consent": pending_consent,
                "should_store_long_term": should_store_long_term,
                "memory_type": memory_type,
                "storage_recommendation": storage_recommendation,
            },
            timestamp=base_memory.timestamp,
        )

        await self.redis_store.add_memory(user_id, short_term_memory)

        # Log short-term storage
        await self.audit_logger.log_memory_created(
            user_id=user_id,
            memory=short_term_memory,
            score=asdict(score),
            metadata={
                "storage_type": "short_term",
                "pii_handling": "permissive",
                "pending_consent": pending_consent,
            },
        )

        return short_term_memory

    async def _store_long_term(
        self,
        user_id: str,
        base_memory: MemoryItem,
        score: MemoryScore,
        pii_results: Dict[str, Any],
        user_consent: Dict[str, Any],
        component_content: str,
        has_pii: bool,
        component_has_high_risk_pii: bool,
        score_metadata: Dict[str, Any],
    ) -> MemoryItem:
        """Store memory in long-term storage (Vector DB)."""
        long_term_content = await self.pii_detector.apply_granular_consent(
            component_content, "long_term", user_consent, pii_results
        )

        long_term_memory = MemoryItem(
            id=base_memory.id + "_long",
            userId=user_id,
            content=long_term_content,
            type=base_memory.type,
            metadata={
                **base_memory.metadata,
                "storage_type": "long_term",
                "has_pii": has_pii,
                "component_has_high_risk_pii": component_has_high_risk_pii,
                "detected_items": [
                    item["id"] for item in pii_results.get("detected_items", [])
                ],
                "score": {
                    "relevance": float(score.relevance),
                    "stability": float(score.stability),
                    "explicitness": float(score.explicitness),
                },
                "pii_strategy": "conservative_for_privacy",
                "original_memory_id": base_memory.id,
                # Add new memory classification fields
                "memory_type": score_metadata.get("memory_type", "lasting_memory"),
                "significance_category": score_metadata.get("significance_category"),
                "significance_level": score_metadata.get("significance_level"),
                "storage_recommendation": score_metadata.get("storage_recommendation"),
                # Special fields for meaningful connections (emotional anchors)
                "connection_type": score_metadata.get("connection_type"),
                "emotional_significance": score_metadata.get("emotional_significance"),
                "personal_meaning": score_metadata.get("personal_meaning"),
                "anchor_strength": score_metadata.get("anchor_strength"),
                "display_category": score_metadata.get("display_category"),
            },
            timestamp=base_memory.timestamp,
        )

        await self.vector_store.add_memory(user_id, long_term_memory)

        # Log long-term storage
        await self.audit_logger.log_memory_created(
            user_id=user_id,
            memory=long_term_memory,
            score=asdict(score),
            metadata={"storage_type": "long_term", "pii_handling": "conservative"},
        )

        return long_term_memory
