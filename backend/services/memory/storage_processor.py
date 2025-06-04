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
        """Store memory using dual strategy (different handling for short-term vs long-term)."""
        # Get user's privacy preferences from database
        audit_logger = AuditLogger()
        privacy_processor = PrivacyProcessor(
            redis_store=self.redis_store,
            vector_store=self.vector_store,
            pii_detector=self.pii_detector,
            audit_logger=audit_logger,
        )

        user_privacy_settings = await privacy_processor.get_user_privacy_settings(
            user_id
        )

        stored_memories = {}
        will_store_short_term = True  # Always store short-term for chat context
        will_store_long_term = score.relevance >= 0.7  # Default threshold
        pending_consent = False

        # Check user's global privacy settings
        if not user_privacy_settings["allow_long_term_storage"]:
            will_store_long_term = False
            self.logger.info(f"User {user_id} has disabled long-term storage")

        # Store short-term memory (always for immediate chat context)
        short_term_memory = MemoryItem(
            id=base_memory.id,
            userId=user_id,
            content=base_memory.content,
            type=base_memory.type,
            metadata={
                **base_memory.metadata,
                "storage_type": "short_term",
                "pii_handling": "original_for_context",
                "score": {
                    "relevance": float(score.relevance),
                    "stability": float(score.stability),
                    "explicitness": float(score.explicitness),
                },
            },
            timestamp=base_memory.timestamp,
        )

        # Store in Redis
        await self.redis_store.add_memory(user_id, short_term_memory)
        stored_memories["short_term"] = short_term_memory

        # Long-term storage logic with privacy settings integration
        if will_store_long_term:
            if pii_results["has_pii"]:
                # Check if user wants auto-anonymization
                if user_privacy_settings["auto_anonymize_pii"]:
                    # Auto-anonymize all PII for long-term storage
                    auto_consent = {}
                    for item in pii_results.get("detected_items", []):
                        auto_consent[item["id"]] = "anonymize"

                    anonymized_content = await self.pii_detector.apply_granular_consent(
                        base_memory.content, "long_term", auto_consent, pii_results
                    )

                    long_term_memory = MemoryItem(
                        id=base_memory.id + "_long",
                        userId=user_id,
                        content=anonymized_content,
                        type=base_memory.type,
                        metadata={
                            **base_memory.metadata,
                            "storage_type": "long_term",
                            "pii_handling": "auto_anonymized",
                            "auto_anonymize_applied": True,
                            "user_privacy_setting": "auto_anonymize_pii",
                            "original_had_pii": True,
                        },
                        timestamp=base_memory.timestamp,
                    )

                    await self.vector_store.add_memory(user_id, long_term_memory)
                    stored_memories["long_term"] = long_term_memory

                    self.logger.info(
                        f"Auto-anonymized PII for user {user_id} based on privacy settings"
                    )

                else:
                    # User wants manual control - defer to consent
                    pending_consent = True
                    short_term_memory.metadata["pending_long_term_consent"] = True
                    await self.redis_store.add_memory(user_id, short_term_memory)

                    self.logger.info(
                        f"Deferred long-term storage for user {user_id} - manual PII consent required"
                    )

            else:
                # No PII detected - store normally
                long_term_memory = MemoryItem(
                    id=base_memory.id + "_long",
                    userId=user_id,
                    content=base_memory.content,
                    type=base_memory.type,
                    metadata={
                        **base_memory.metadata,
                        "storage_type": "long_term",
                        "pii_handling": "no_pii_detected",
                    },
                    timestamp=base_memory.timestamp,
                )

                await self.vector_store.add_memory(user_id, long_term_memory)
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
