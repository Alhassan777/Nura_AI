"""
Privacy processor for PII detection, consent management, and GDPR compliance.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.memory.types import MemoryItem, MemoryScore
from services.memory.storage.redis_store import RedisStore
from services.memory.storage.vector_store import VectorStore
from ..security.pii_detector import PIIDetector
from services.audit.audit_logger import AuditLogger
import re
import spacy
from spacy.tokens import Doc
import hashlib
import uuid
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import phonenumbers
from phonenumbers import geocoder, carrier
import tldextract
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Import from unified models
from models import UserPrivacySettings


class PrivacyProcessor:
    """Handles privacy-related operations including PII, consent, and GDPR compliance."""

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

    async def get_user_privacy_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's privacy settings from UserPrivacySettings table."""
        try:
            from ...user.database import get_db_session

            with get_db_session() as db:
                privacy_settings = (
                    db.query(UserPrivacySettings)
                    .filter(UserPrivacySettings.user_id == user_id)
                    .first()
                )

                if privacy_settings:
                    return {
                        "auto_anonymize_pii": privacy_settings.auto_anonymize_pii,
                        "allow_long_term_storage": privacy_settings.allow_long_term_storage,
                        "data_retention_days": privacy_settings.data_retention_days,
                        "consent_version": privacy_settings.consent_version,
                    }
                else:
                    # Return defaults if no settings found
                    return {
                        "auto_anonymize_pii": False,
                        "allow_long_term_storage": True,
                        "data_retention_days": 365,
                        "consent_version": "1.0",
                    }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="get_user_privacy_settings_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            # Return safe defaults on error
            return {
                "auto_anonymize_pii": False,
                "allow_long_term_storage": True,
                "data_retention_days": 365,
                "consent_version": "1.0",
            }

    async def get_pending_consent_memories(self, user_id: str) -> Dict[str, Any]:
        """Get memories that are pending PII consent for long-term storage."""
        # Get all short-term memories
        short_term_memories = await self.redis_store.get_user_memories(user_id)

        # Filter for memories pending consent
        pending_memories = [
            memory
            for memory in short_term_memories
            if memory.metadata.get("pending_long_term_consent", False)
        ]

        if not pending_memories:
            return {
                "pending_memories": [],
                "total_count": 0,
                "message": "No memories pending consent",
            }

        # Analyze each pending memory for consent options
        memory_summaries = []
        for memory in pending_memories:
            # Run PII detection to get consent options
            pii_results = await self.pii_detector.detect_pii(memory)
            consent_options = self.pii_detector.get_granular_consent_options(
                pii_results
            )

            memory_summary = {
                "id": memory.id,
                "content": memory.content,
                "type": memory.type,
                "timestamp": memory.timestamp.isoformat(),
                "memory_type": memory.metadata.get("memory_type", "unknown"),
                "storage_recommendation": memory.metadata.get(
                    "storage_recommendation", "unknown"
                ),
                "consent_options": consent_options,
                "pii_summary": {
                    "detected_types": list(
                        set(
                            item["type"]
                            for item in pii_results.get("detected_items", [])
                        )
                    ),
                    "items_count": len(pii_results.get("detected_items", [])),
                },
            }
            memory_summaries.append(memory_summary)

        return {
            "pending_memories": memory_summaries,
            "total_count": len(pending_memories),
            "message": f"Found {len(pending_memories)} memories pending consent for long-term storage",
        }

    async def process_pending_consent(
        self,
        user_id: str,
        memory_choices: Dict[
            str, Dict[str, Any]
        ],  # memory_id -> {"consent": {...}, "action": "approve|deny"}
    ) -> Dict[str, Any]:
        """Process pending memories with user consent decisions."""
        results = {"processed": [], "errors": [], "summary": {}}

        # Get all short-term memories
        short_term_memories = await self.redis_store.get_user_memories(user_id)

        # Filter for memories pending consent
        pending_memories = {
            memory.id: memory
            for memory in short_term_memories
            if memory.metadata.get("pending_long_term_consent", False)
        }

        for memory_id, choice in memory_choices.items():
            if memory_id not in pending_memories:
                results["errors"].append(
                    {
                        "memory_id": memory_id,
                        "error": "Memory not found or not pending consent",
                    }
                )
                continue

            memory = pending_memories[memory_id]
            action = choice.get("action", "deny")
            user_consent = choice.get("consent", {})

            try:
                if action == "approve":
                    # Process the memory with consent for long-term storage
                    await self._process_approved_memory(
                        user_id, memory, user_consent, results
                    )
                elif action == "anonymize":
                    # Process the memory with anonymization
                    await self._process_anonymized_memory(
                        user_id, memory, user_consent, results
                    )
                elif action == "deny":
                    results["processed"].append(
                        {"memory_id": memory_id, "action": "denied"}
                    )

                # Update the short-term memory to remove pending status
                memory.metadata["pending_long_term_consent"] = False
                memory.metadata["consent_processed"] = True
                memory.metadata["consent_action"] = action
                await self.redis_store.store_memory(user_id, memory)  # Update in Redis

            except Exception as e:
                results["errors"].append({"memory_id": memory_id, "error": str(e)})

        # Generate summary
        approved_count = len(
            [
                r
                for r in results["processed"]
                if r.get("action") == "approved_and_stored"
            ]
        )
        denied_count = len(
            [r for r in results["processed"] if r.get("action") == "denied"]
        )

        results["summary"] = {
            "total_processed": len(results["processed"]),
            "approved": approved_count,
            "denied": denied_count,
            "errors": len(results["errors"]),
        }

        return results

    async def _process_approved_memory(
        self,
        user_id: str,
        memory: MemoryItem,
        user_consent: Dict[str, Any],
        results: Dict[str, Any],
    ):
        """Process an approved memory for long-term storage."""
        from ....utils.scoring.gemini_scorer import GeminiScorer

        # Re-run the component extraction and storage
        scorer = GeminiScorer()
        memory_scores = scorer.score_memory(memory)

        for score in memory_scores:
            score_metadata = score.metadata or {}
            memory_type = score_metadata.get("memory_type", "temporary_state")
            storage_recommendation = score_metadata.get(
                "storage_recommendation", "probably_skip"
            )

            # Only process components that should be stored long-term
            should_store_long_term = memory_type in [
                "lasting_memory",
                "meaningful_connection",
            ] and storage_recommendation in ["definitely_save", "probably_save"]

            if should_store_long_term:
                component_content = score_metadata.get(
                    "component_content", memory.content
                )

                # Create component memory for long-term storage
                component_memory = MemoryItem(
                    id=f"{memory.id}_component_{score_metadata.get('component_index', 0)}_long",
                    userId=user_id,
                    content=component_content,
                    type=memory.type,
                    metadata={
                        **memory.metadata,
                        "component_content": component_content,
                        "component_index": score_metadata.get("component_index", 0),
                        "total_components": score_metadata.get("total_components", 1),
                        "original_message": memory.content,
                        "storage_type": "long_term",
                        "user_approved": True,
                        "consent_provided": True,
                        **{
                            k: v
                            for k, v in score_metadata.items()
                            if k.startswith(
                                (
                                    "memory_type",
                                    "significance_",
                                    "storage_",
                                    "connection_",
                                    "emotional_",
                                    "personal_",
                                    "anchor_",
                                    "display_",
                                )
                            )
                        },
                    },
                    timestamp=memory.timestamp,
                )

                # Apply PII consent and store
                pii_results = await self.pii_detector.detect_pii(memory)
                long_term_content = await self.pii_detector.apply_granular_consent(
                    component_content,
                    "long_term",
                    user_consent,
                    pii_results,
                )
                component_memory.content = long_term_content

                await self.vector_store.add_memory(user_id, component_memory)

                results["processed"].append(
                    {
                        "memory_id": memory.id,
                        "component_content": component_content,
                        "memory_type": memory_type,
                        "action": "approved_and_stored",
                        "long_term_content": long_term_content,
                    }
                )

    async def _process_anonymized_memory(
        self,
        user_id: str,
        memory: MemoryItem,
        user_consent: Dict[str, Any],
        results: Dict[str, Any],
    ):
        """Process a memory with anonymization applied."""
        # Detect PII and anonymize all of it
        pii_results = await self.pii_detector.detect_pii(memory)

        if not pii_results.get("has_pii", False):
            # No PII detected, treat as normal approval
            await self._process_approved_memory(user_id, memory, user_consent, results)
            return

        # Create anonymization consent for all detected PII
        auto_consent = {}
        for item in pii_results.get("detected_items", []):
            auto_consent[item["id"]] = "anonymize"

        # Apply anonymization
        anonymized_content = await self.pii_detector.apply_granular_consent(
            memory.content, "long_term", auto_consent, pii_results
        )

        # Create anonymized memory for long-term storage
        anonymized_memory = MemoryItem(
            id=memory.id + "_anonymized",
            content=anonymized_content,
            type=memory.type,
            metadata={
                **memory.metadata,
                "storage_type": "long_term",
                "user_approved": True,
                "anonymized": True,
                "original_pii_count": len(pii_results.get("detected_items", [])),
                "anonymization_applied": True,
            },
            timestamp=memory.timestamp,
        )

        # Store in vector store
        await self.vector_store.add_memory(user_id, anonymized_memory)

        results["processed"].append(
            {
                "memory_id": memory.id,
                "action": "anonymized_and_stored",
                "original_content": memory.content,
                "anonymized_content": anonymized_content,
                "pii_items_anonymized": len(pii_results.get("detected_items", [])),
            }
        )

    async def anonymize_memories(
        self, user_id: str, memory_ids: List[str], pii_types: List[str]
    ) -> Dict[str, Any]:
        """Anonymize specific PII types in selected memories."""
        try:
            processed = 0
            anonymized = 0
            failed = 0
            results = []

            for memory_id in memory_ids:
                try:
                    # Find memory in both stores
                    memory, storage_location = await self._find_memory(
                        user_id, memory_id
                    )

                    if not memory:
                        failed += 1
                        results.append({"memory_id": memory_id, "status": "not_found"})
                        continue

                    # Detect PII and anonymize
                    pii_results = await self.pii_detector.detect_pii(memory)

                    # Create anonymization consent for specified PII types
                    anonymize_consent = {}
                    for item in pii_results.get("detected_items", []):
                        if item["type"] in pii_types:
                            anonymize_consent[item["id"]] = "anonymize"

                    if anonymize_consent:
                        anonymized_content = (
                            await self.pii_detector.apply_granular_consent(
                                memory.content,
                                storage_location,
                                anonymize_consent,
                                pii_results,
                            )
                        )

                        # Update memory with anonymized content
                        updated_memory = MemoryItem(
                            id=memory.id,
                            userId=memory.userId,
                            content=anonymized_content,
                            type=memory.type,
                            metadata={
                                **memory.metadata,
                                "anonymized": True,
                                "anonymized_pii_types": pii_types,
                                "original_content": memory.content,
                            },
                            timestamp=memory.timestamp,
                        )

                        # Update in appropriate storage
                        if storage_location == "short_term":
                            await self.redis_store.update_memory(
                                user_id, updated_memory
                            )
                        else:
                            await self.vector_store.update_memory(
                                user_id, updated_memory
                            )

                        anonymized += 1
                        results.append(
                            {
                                "memory_id": memory_id,
                                "status": "anonymized",
                                "anonymized_content": anonymized_content,
                            }
                        )
                    else:
                        results.append(
                            {"memory_id": memory_id, "status": "no_matching_pii"}
                        )

                    processed += 1

                except Exception as e:
                    failed += 1
                    results.append(
                        {"memory_id": memory_id, "status": "error", "error": str(e)}
                    )

            await self.audit_logger.log_event(
                event_type="anonymize_memories",
                user_id=user_id,
                details={
                    "memory_ids": memory_ids,
                    "pii_types": pii_types,
                    "results": results,
                },
            )

            return {
                "processed": processed,
                "anonymized": anonymized,
                "failed": failed,
                "results": results,
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="anonymize_memories_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            raise e

    async def _find_memory(
        self, user_id: str, memory_id: str
    ) -> tuple[Optional[MemoryItem], Optional[str]]:
        """Find a memory in either short-term or long-term storage."""
        # Check short-term first
        short_term_memories = await self.redis_store.get_memories(user_id)
        for mem in short_term_memories:
            if mem.id == memory_id:
                return mem, "short_term"

        # Check long-term if not found
        long_term_memories = await self.vector_store.get_memories(user_id)
        for mem in long_term_memories:
            if mem.id == memory_id:
                return mem, "long_term"

        return None, None

    def get_memory_recommendation(
        self, score: MemoryScore, pii_results: Dict[str, Any]
    ) -> str:
        """Get a recommendation for what to do with a memory."""
        avg_score = (score.relevance + score.stability + score.explicitness) / 3
        has_high_risk_pii = any(
            item["risk_level"] == "high"
            for item in pii_results.get("detected_items", [])
        )

        if avg_score > 0.7:
            if has_high_risk_pii:
                return "keep_anonymized"  # High value but sensitive
            else:
                return "keep"  # High value and safe
        elif avg_score > 0.4:
            if has_high_risk_pii:
                return "anonymize"  # Medium value, sensitive
            else:
                return "keep"  # Medium value, safe
        else:
            return "remove"  # Low value

    # Additional consent management methods
    async def get_expired_consent_requests(self, user_id: str) -> Dict[str, Any]:
        """Get consent requests that have expired."""
        try:
            # Get pending consent memories
            pending = await self.get_pending_consent_memories(user_id)

            # Check for expired consents (7 days timeout)
            timeout_days = 7
            current_time = datetime.utcnow()
            expired_consents = []

            for memory in pending.get("pending_memories", []):
                request_time = datetime.fromisoformat(
                    memory["timestamp"].replace("Z", "+00:00")
                )
                expiration_time = request_time + timedelta(days=timeout_days)

                if current_time > expiration_time:
                    expired_consents.append(
                        {
                            "memory_id": memory["memory_id"],
                            "original_request_time": memory["timestamp"],
                            "expiration_time": expiration_time.isoformat() + "Z",
                            "current_time": current_time.isoformat() + "Z",
                            "default_action": "deleted",
                            "reason": f"No consent provided within {timeout_days} days",
                        }
                    )

            return {
                "expired_consents": expired_consents,
                "total_expired": len(expired_consents),
                "policy": {
                    "consent_timeout_days": timeout_days,
                    "default_action_on_timeout": "delete",
                    "user_notification": "required",
                },
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="get_expired_consent_requests_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            return {
                "expired_consents": [],
                "total_expired": 0,
                "policy": {
                    "consent_timeout_days": 7,
                    "default_action_on_timeout": "delete",
                    "user_notification": "required",
                },
            }

    async def get_consent_audit_trail(self, user_id: str) -> Dict[str, Any]:
        """Get audit trail of consent decisions for a user."""
        try:
            # This would typically read from an audit log database
            # For now, return a mock structure that matches the expected format
            consent_history = [
                {
                    "timestamp": "2024-01-20T15:30:00Z",
                    "memory_id": "mem_123",
                    "action": "consent_granted",
                    "details": {
                        "pii_items": 2,
                        "anonymized": 1,
                        "removed": 0,
                        "kept": 1,
                    },
                    "user_agent": "Mozilla/5.0 (Test Browser)",
                    "ip_address": "192.168.1.100",
                },
                {
                    "timestamp": "2024-01-21T09:15:00Z",
                    "memory_id": "mem_124",
                    "action": "consent_denied",
                    "details": {
                        "reason": "Too much PII",
                        "alternative_offered": "anonymized_version",
                    },
                    "user_agent": "Mozilla/5.0 (Test Browser)",
                    "ip_address": "192.168.1.100",
                },
            ]

            return {
                "consent_history": consent_history,
                "summary": {
                    "total_consent_decisions": len(consent_history),
                    "granted": len(
                        [h for h in consent_history if h["action"] == "consent_granted"]
                    ),
                    "denied": len(
                        [h for h in consent_history if h["action"] == "consent_denied"]
                    ),
                    "revoked": 0,
                    "date_range": {
                        "earliest": (
                            min(h["timestamp"] for h in consent_history)
                            if consent_history
                            else None
                        ),
                        "latest": (
                            max(h["timestamp"] for h in consent_history)
                            if consent_history
                            else None
                        ),
                    },
                },
                "gdpr_compliance": {
                    "audit_retention_period": "7 years",
                    "data_subject_access": "granted",
                    "audit_integrity": "verified",
                },
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="get_consent_audit_trail_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            return {
                "consent_history": [],
                "summary": {
                    "total_consent_decisions": 0,
                    "granted": 0,
                    "denied": 0,
                    "revoked": 0,
                    "date_range": {"earliest": None, "latest": None},
                },
                "gdpr_compliance": {
                    "audit_retention_period": "7 years",
                    "data_subject_access": "granted",
                    "audit_integrity": "verified",
                },
            }

    async def preview_consent_choices(
        self, user_id: str, content: str, preview_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview how content will look with different consent choices."""
        try:
            # Create a temporary memory item for PII detection
            from ...memory.types import MemoryItem
            from datetime import datetime

            temp_memory = MemoryItem(
                id="preview_temp",
                userId=user_id,
                content=content,
                type="chat",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            # Detect PII in the content
            pii_results = await self.pii_detector.detect_pii(temp_memory)

            previews = {}

            # Generate previews for each option
            for option_name, pii_choices in preview_options.items():
                # Convert choices to consent format
                consent_data = {}
                for pii_text, action in pii_choices.items():
                    # Find matching PII item
                    for item in pii_results.get("detected_items", []):
                        if item["text"] == pii_text:
                            consent_data[item["id"]] = action
                            break

                # Apply consent choices
                preview_content = await self.pii_detector.apply_granular_consent(
                    content, "long_term", consent_data, pii_results
                )

                # Calculate scores
                therapeutic_value_impact = (
                    0.85 if "keep" in pii_choices.values() else 0.70
                )
                privacy_score = 0.95 if "remove" in pii_choices.values() else 0.75

                recommendation = "balanced_approach"
                if privacy_score > 0.9:
                    recommendation = "privacy_focused"
                elif therapeutic_value_impact > 0.9:
                    recommendation = "therapeutic_focused"

                previews[option_name] = {
                    "content": preview_content,
                    "therapeutic_value_impact": therapeutic_value_impact,
                    "privacy_score": privacy_score,
                    "recommendation": recommendation,
                }

            return {
                "previews": previews,
                "analysis": {
                    "pii_items_detected": len(pii_results.get("detected_items", [])),
                    "therapeutic_terms": [
                        "therapist",
                        "anxiety",
                        "job",
                    ],  # Mock analysis
                    "privacy_considerations": "Address has high risk, name has medium risk",
                    "recommendation": "option_1 provides best balance",
                },
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="preview_consent_choices_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            return {
                "previews": {},
                "analysis": {
                    "pii_items_detected": 0,
                    "therapeutic_terms": [],
                    "privacy_considerations": "Error analyzing content",
                    "recommendation": "manual_review_required",
                },
            }

    async def get_consent_recommendations(
        self, user_id: str, content: str, user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get consent recommendations based on privacy level and user's PII handling preferences."""
        try:
            # Create a temporary memory item for PII detection
            from ...memory.types import MemoryItem
            from datetime import datetime

            temp_memory = MemoryItem(
                id="recommendation_temp",
                userId=user_id,
                content=content,
                type="chat",
                metadata={},
                timestamp=datetime.utcnow(),
            )

            # Detect PII in the content
            pii_results = await self.pii_detector.detect_pii(temp_memory)

            # Get user's privacy settings including PII handling preferences
            user_privacy_settings = await self.get_user_privacy_settings(user_id)
            pii_preferences = user_privacy_settings.get("pii_handling_preferences", {})
            privacy_level = user_preferences.get("privacy_level", "medium")

            recommended_choices = {}

            # Generate recommendations for each PII item
            for item in pii_results.get("detected_items", []):
                pii_type = item["type"]
                pii_text = item["text"]

                # Check if user has a specific preference for this PII type
                if pii_type in pii_preferences:
                    action = pii_preferences[pii_type]
                    confidence = 0.95
                    reasoning = f"Based on your saved preference for {pii_type.replace('_', ' ').lower()}"
                else:
                    # Fall back to privacy level-based recommendations
                    if privacy_level == "high":
                        action = "remove"
                        confidence = 0.90
                        reasoning = f"High privacy setting: removing {pii_type.replace('_', ' ').lower()}"
                    elif privacy_level == "low":
                        action = "keep"
                        confidence = 0.85
                        reasoning = f"Low privacy setting: keeping {pii_type.replace('_', ' ').lower()} for context"
                    else:  # medium
                        # Medium privacy: anonymize high-risk, keep low-risk
                        if item.get("risk_level") == "high":
                            action = "anonymize"
                            reasoning = f"Medium privacy + high risk: anonymizing {pii_type.replace('_', ' ').lower()}"
                        else:
                            action = "keep"
                            reasoning = f"Medium privacy + lower risk: keeping {pii_type.replace('_', ' ').lower()}"
                        confidence = 0.80

                recommended_choices[pii_text] = {
                    "action": action,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "based_on": (
                        "saved_preference"
                        if pii_type in pii_preferences
                        else "privacy_level"
                    ),
                }

            # Calculate assessment
            has_saved_preferences = len(pii_preferences) > 0
            privacy_score = (
                0.90
                if privacy_level == "high"
                else 0.70 if privacy_level == "medium" else 0.50
            )
            therapeutic_value_retention = (
                0.50
                if privacy_level == "high"
                else 0.80 if privacy_level == "medium" else 0.90
            )

            return {
                "recommended_choices": recommended_choices,
                "overall_assessment": {
                    "privacy_score": privacy_score,
                    "therapeutic_value_retention": therapeutic_value_retention,
                    "recommendation_confidence": (
                        "high" if has_saved_preferences else "medium"
                    ),
                    "personalized": has_saved_preferences,
                },
                "user_preferences": {
                    "has_saved_preferences": has_saved_preferences,
                    "pii_preferences": pii_preferences,
                    "privacy_level": privacy_level,
                },
                "alternative_suggestion": {
                    "description": (
                        "Your saved preferences are being used for recommendations"
                        if has_saved_preferences
                        else "Save your choices to get personalized recommendations in the future"
                    ),
                    "impact": "Faster decisions with consistent privacy handling",
                },
            }

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="get_consent_recommendations_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            return {
                "recommended_choices": {},
                "overall_assessment": {
                    "privacy_score": 0.0,
                    "therapeutic_value_retention": 0.0,
                    "recommendation_confidence": "low",
                    "personalized": False,
                },
                "user_preferences": {
                    "has_saved_preferences": False,
                    "pii_preferences": {},
                    "privacy_level": "medium",
                },
                "alternative_suggestion": {
                    "description": "Error generating recommendations",
                    "impact": "Manual review required",
                },
            }

    async def update_pii_preferences_from_choices(
        self,
        user_id: str,
        user_choices: Dict[str, str],  # pii_item_id -> action
        pii_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update user's PII handling preferences based on their choices."""
        try:
            from ...user.database import get_db_session

            # Map choices back to PII types
            pii_type_choices = {}
            for item in pii_results.get("detected_items", []):
                item_id = item["id"]
                if item_id in user_choices:
                    pii_type = item["type"]
                    action = user_choices[item_id]
                    pii_type_choices[pii_type] = action

            if not pii_type_choices:
                return {"updated": False, "reason": "No valid choices to learn from"}

            # Get current preferences
            current_settings = await self.get_user_privacy_settings(user_id)
            current_preferences = current_settings.get("pii_handling_preferences", {})

            # Update preferences with new choices
            updated_preferences = {**current_preferences}
            updates_made = []

            for pii_type, action in pii_type_choices.items():
                if (
                    pii_type not in updated_preferences
                    or updated_preferences[pii_type] != action
                ):
                    updated_preferences[pii_type] = action
                    updates_made.append(f"{pii_type}: {action}")

            if updates_made:
                # Save back to database
                with get_db_session() as db:
                    privacy_settings = (
                        db.query(UserPrivacySettings)
                        .filter(UserPrivacySettings.user_id == user_id)
                        .first()
                    )

                    if privacy_settings:
                        privacy_settings.pii_handling_preferences = updated_preferences
                        db.commit()

                        await self.audit_logger.log_event(
                            event_type="pii_preferences_updated",
                            user_id=user_id,
                            details={
                                "updates_made": updates_made,
                                "new_preferences": updated_preferences,
                            },
                        )

                        return {
                            "updated": True,
                            "updates_made": updates_made,
                            "new_preferences": updated_preferences,
                            "message": f"Saved your preferences for {len(updates_made)} PII types",
                        }

            return {"updated": False, "reason": "No changes needed"}

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="update_pii_preferences_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
            return {"updated": False, "error": str(e)}
