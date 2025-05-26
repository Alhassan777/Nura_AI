import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dataclasses import asdict

from .types import MemoryItem, MemoryScore, MemoryContext, MemoryConfig, MemoryStats
from .storage.redis_store import RedisStore
from .storage.vector_store import VectorStore
from .scoring.gemini_scorer import GeminiScorer
from .security.pii_detector import PIIDetector
from .audit.audit_logger import AuditLogger
from .config import Config


class MemoryService:
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
        self.redis_store = RedisStore(Config.REDIS_URL)

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

    async def process_memory(
        self,
        user_id: str,
        content: str,
        type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
        user_consent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a new memory item with dual storage strategy."""
        # Create memory item
        memory_id = str(uuid.uuid4())
        base_memory = MemoryItem(
            id=memory_id,
            userId=user_id,
            content=content,
            type=type,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )

        # For chat messages, always store in short-term first, handle PII later
        is_chat_message = type in ["user_message", "assistant_message", "chat"]
        is_assistant_message = type == "assistant_message" or (
            metadata and metadata.get("source") == "assistant"
        )

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
                    "memory_id": memory_id,
                    "original_content": content,
                    "pii_results": pii_results,
                }

        # Score memory for therapeutic value (separate from PII) - now returns multiple components
        memory_scores = self.scorer.score_memory(base_memory)

        # Process each component separately
        stored_components = []
        all_results = []

        for score in memory_scores:
            score_metadata = score.metadata or {}
            component_content = score_metadata.get(
                "component_content", base_memory.content
            )
            memory_type = score_metadata.get("memory_type", "temporary_state")
            storage_recommendation = score_metadata.get(
                "storage_recommendation", "probably_skip"
            )

            # Create a memory item for this specific component
            component_memory = MemoryItem(
                id=f"{base_memory.id}_component_{score_metadata.get('component_index', 0)}",
                userId=user_id,
                content=component_content,
                type=type,
                metadata={
                    **(metadata or {}),
                    "original_message": base_memory.content,
                    "component_index": score_metadata.get("component_index", 0),
                    "total_components": score_metadata.get("total_components", 1),
                },
                timestamp=base_memory.timestamp,
            )

            # Determine if we should store this component
            # Only store user messages long-term if they are significant
            should_store_somewhere = (
                (
                    is_chat_message and not is_assistant_message
                )  # Store user messages in short-term
                or (
                    not is_assistant_message
                    and memory_type in ["lasting_memory", "meaningful_connection"]
                )  # Store significant user memories
                or (
                    not is_assistant_message
                    and storage_recommendation in ["definitely_save", "probably_save"]
                )  # Store recommended user memories
            )

            # If component doesn't meet storage criteria, skip it
            if not should_store_somewhere:
                component_result = {
                    "component_content": component_content,
                    "memory_type": memory_type,
                    "storage_recommendation": storage_recommendation,
                    "stored": False,
                    "reason": "Component did not meet therapeutic value criteria or was assistant message",
                    "score": {
                        "relevance": float(score.relevance),
                        "stability": float(score.stability),
                        "explicitness": float(score.explicitness),
                    },
                }
                all_results.append(component_result)
                continue

            # Apply dual storage strategy for this component
            component_result = await self._store_with_dual_strategy(
                user_id, component_memory, score, pii_results, user_consent or {}
            )
            component_result["component_content"] = component_content
            component_result["memory_type"] = memory_type
            all_results.append(component_result)

            if component_result.get("stored"):
                stored_components.append(component_result)

        # Return summary of all components
        if not stored_components:
            return {
                "needs_consent": False,
                "stored": False,
                "reason": "No components met storage criteria",
                "components": all_results,
                "total_components": len(memory_scores),
                "stored_components": 0,
            }

        result = {
            "needs_consent": False,
            "stored": True,
            "components": all_results,
            "total_components": len(memory_scores),
            "stored_components": len(stored_components),
            "storage_summary": {
                "short_term_stored": sum(
                    1
                    for c in stored_components
                    if c.get("storage_details", {}).get("short_term")
                ),
                "long_term_stored": sum(
                    1
                    for c in stored_components
                    if c.get("storage_details", {}).get("long_term")
                ),
                "emotional_anchors": sum(
                    1
                    for c in stored_components
                    if c.get("memory_type") == "meaningful_connection"
                ),
            },
        }

        return result

    async def _store_with_dual_strategy(
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
        component_has_high_risk_pii = False

        if has_pii:
            # Check if any PII items overlap with this component's content
            for pii_item in pii_results.get("detected_items", []):
                pii_text = pii_item.get("text", "")
                if (
                    pii_text.lower() in component_content.lower()
                    and pii_item.get("risk_level") == "high"
                ):
                    component_has_high_risk_pii = True
                    break

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
            stored_memories["short_term"] = short_term_memory

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

        # STEP 2: Store in LONG-TERM (Vector DB) - more conservative with PII
        if will_store_long_term:
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
                    "significance_category": score_metadata.get(
                        "significance_category"
                    ),
                    "significance_level": score_metadata.get("significance_level"),
                    "storage_recommendation": score_metadata.get(
                        "storage_recommendation"
                    ),
                    # Special fields for meaningful connections (emotional anchors)
                    "connection_type": score_metadata.get("connection_type"),
                    "emotional_significance": score_metadata.get(
                        "emotional_significance"
                    ),
                    "personal_meaning": score_metadata.get("personal_meaning"),
                    "anchor_strength": score_metadata.get("anchor_strength"),
                    "display_category": score_metadata.get("display_category"),
                },
                timestamp=base_memory.timestamp,
            )

            await self.vector_store.add_memory(user_id, long_term_memory)
            stored_memories["long_term"] = long_term_memory

            # Log long-term storage
            await self.audit_logger.log_memory_created(
                user_id=user_id,
                memory=long_term_memory,
                score=asdict(score),
                metadata={"storage_type": "long_term", "pii_handling": "conservative"},
            )

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

    async def get_memory_context(
        self, user_id: str, query: Optional[str] = None
    ) -> MemoryContext:
        """Get memory context for a user."""
        # Get short-term memories
        short_term = await self.redis_store.get_memories(user_id)

        # Get long-term memories
        long_term = []
        if query:
            # Use semantic search with the provided query
            long_term = await self.vector_store.get_similar_memories(
                user_id=user_id, query=query
            )
        else:
            # If no query provided, use the most recent short-term memory as context
            # to find relevant long-term memories
            if short_term:
                # Use the most recent message as the query for semantic search
                recent_message = short_term[0].content  # Redis returns newest first
                long_term = await self.vector_store.get_similar_memories(
                    user_id=user_id, query=recent_message, limit=3
                )

        # Log memory access
        for memory in long_term:
            await self.audit_logger.log_memory_accessed(
                user_id=user_id, memory=memory, query=query or "context_retrieval"
            )

        # Generate digest
        digest = await self._generate_digest(short_term + long_term)

        return MemoryContext(short_term=short_term, long_term=long_term, digest=digest)

    async def get_memory_stats(self, user_id: str) -> MemoryStats:
        """Get memory statistics for a user."""
        # Get counts from both stores
        short_term_count = await self.redis_store.get_memory_count(user_id)
        long_term_count = await self.vector_store.get_memory_count(user_id)

        return MemoryStats(
            total=short_term_count + long_term_count,
            short_term=short_term_count,
            long_term=long_term_count,
            sensitive=await self._get_sensitive_count(user_id),
        )

    async def get_emotional_anchors(self, user_id: str) -> List[MemoryItem]:
        """Get emotional anchors (meaningful connections) for a user."""
        # Get all long-term memories
        all_memories = await self.vector_store.get_memories(user_id)

        # Filter for meaningful connections (emotional anchors) - be more strict
        emotional_anchors = []
        for memory in all_memories:
            memory_type = memory.metadata.get("memory_type", "")
            display_category = memory.metadata.get("display_category", "")
            connection_type = memory.metadata.get("connection_type", "")

            # Only include if explicitly marked as meaningful_connection
            # AND has connection_type (to ensure it's a proper anchor)
            is_meaningful_connection = memory_type == "meaningful_connection"
            is_emotional_anchor = display_category == "emotional_anchor"
            has_connection_type = bool(connection_type)

            # Must be meaningful_connection AND have connection_type
            # OR explicitly marked as emotional_anchor
            if (
                is_meaningful_connection and has_connection_type
            ) or is_emotional_anchor:
                emotional_anchors.append(memory)

        # Sort by anchor strength and significance
        emotional_anchors.sort(
            key=lambda m: (
                {"strong": 3, "moderate": 2, "developing": 1}.get(
                    m.metadata.get("anchor_strength", "developing"), 1
                ),
                {"critical": 4, "high": 3, "moderate": 2, "low": 1, "minimal": 0}.get(
                    m.metadata.get("significance_level", "minimal"), 0
                ),
            ),
            reverse=True,
        )

        return emotional_anchors

    async def get_regular_memories(
        self, user_id: str, query: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get regular lasting memories (excluding emotional anchors) for a user."""
        if query:
            # Use semantic search
            all_memories = await self.vector_store.get_similar_memories(
                user_id=user_id, query=query
            )
        else:
            # Get all long-term memories
            all_memories = await self.vector_store.get_memories(user_id)

        # Filter for regular lasting memories - exclude emotional anchors
        regular_memories = []
        for memory in all_memories:
            memory_type = memory.metadata.get("memory_type", "")
            display_category = memory.metadata.get("display_category", "")
            connection_type = memory.metadata.get("connection_type", "")

            # Include if:
            # 1. Explicitly marked as lasting_memory
            # 2. NOT a meaningful_connection with connection_type (that's an anchor)
            # 3. NOT marked as emotional_anchor
            is_lasting_memory = memory_type == "lasting_memory"
            is_meaningful_connection_with_type = (
                memory_type == "meaningful_connection" and bool(connection_type)
            )
            is_emotional_anchor = display_category == "emotional_anchor"

            # Include lasting memories that are NOT emotional anchors
            if (
                is_lasting_memory
                and not is_meaningful_connection_with_type
                and not is_emotional_anchor
            ):
                regular_memories.append(memory)
            # Also include long-term storage memories that don't have specific classification
            elif (
                memory.metadata.get("storage_type") == "long_term"
                and not memory_type
                and not is_emotional_anchor
            ):
                regular_memories.append(memory)

        return regular_memories

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        # Try deleting from both stores
        deleted = await self.redis_store.delete_memory(user_id, memory_id)
        if not deleted:
            deleted = await self.vector_store.delete_memory(user_id, memory_id)

        if deleted:
            # Log deletion
            await self.audit_logger.log_memory_deleted(
                user_id=user_id, memory=MemoryItem(id=memory_id, userId=user_id)
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

    async def _generate_digest(self, memories: List[MemoryItem]) -> str:
        """Generate a digest of memories."""
        if not memories:
            return "No memories available"

        # Separate short-term and long-term memories for accurate counting
        short_term_memories = [
            m for m in memories if m.metadata.get("storage_type") == "short_term"
        ]
        long_term_memories = [
            m for m in memories if m.metadata.get("storage_type") == "long_term"
        ]

        # Create digest focusing on long-term memories for context
        if long_term_memories:
            recent_long_term = [
                m.content for m in long_term_memories[-3:]
            ]  # Last 3 long-term memories
            return f"{len(long_term_memories)} long-term memories available for context: {'; '.join(recent_long_term)}"
        else:
            return "No long-term memories available yet"

    async def _get_sensitive_count(self, user_id: str) -> int:
        """Get count of sensitive memories."""
        # Count memories with PII detected
        try:
            short_term_memories = await self.redis_store.get_memories(user_id)
            sensitive_count = sum(
                1
                for memory in short_term_memories
                if memory.metadata.get("has_pii", False)
            )
            return sensitive_count
        except Exception:
            return 0

    async def get_pending_consent_memories(self, user_id: str) -> Dict[str, Any]:
        """Get memories that are pending PII consent for long-term storage."""
        # Get all short-term memories
        short_term_memories = await self.redis_store.get_memories(user_id)

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

    async def get_chat_session_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of chat memories for user review and selection."""
        # Get all short-term memories (chat session)
        short_term_memories = await self.redis_store.get_memories(user_id)

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
            score = self.scorer.score_memory(memory)

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
                "recommended_action": self._get_memory_recommendation(
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

    def _get_memory_recommendation(
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

    async def apply_user_memory_choices(
        self,
        user_id: str,
        memory_choices: Dict[str, str],  # memory_id -> "keep"|"remove"|"anonymize"
    ) -> Dict[str, Any]:
        """Apply user choices about which memories to keep, remove, or anonymize."""
        results = {"kept": [], "removed": [], "anonymized": [], "errors": []}

        # Get current short-term memories
        short_term_memories = await self.redis_store.get_memories(user_id)

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
        short_term_memories = await self.redis_store.get_memories(user_id)

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
                    # Re-run the component extraction and storage
                    memory_scores = self.scorer.score_memory(memory)

                    for score in memory_scores:
                        score_metadata = score.metadata or {}
                        memory_type = score_metadata.get(
                            "memory_type", "temporary_state"
                        )
                        storage_recommendation = score_metadata.get(
                            "storage_recommendation", "probably_skip"
                        )

                        # Only process components that should be stored long-term
                        should_store_long_term = memory_type in [
                            "lasting_memory",
                            "meaningful_connection",
                        ] and storage_recommendation in [
                            "definitely_save",
                            "probably_save",
                        ]

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
                                    "component_index": score_metadata.get(
                                        "component_index", 0
                                    ),
                                    "total_components": score_metadata.get(
                                        "total_components", 1
                                    ),
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
                            long_term_content = (
                                await self.pii_detector.apply_granular_consent(
                                    component_content,
                                    "long_term",
                                    user_consent,
                                    pii_results,
                                )
                            )
                            component_memory.content = long_term_content

                            await self.vector_store.add_memory(
                                user_id, component_memory
                            )

                            results["processed"].append(
                                {
                                    "memory_id": memory_id,
                                    "component_content": component_content,
                                    "memory_type": memory_type,
                                    "action": "approved_and_stored",
                                    "long_term_content": long_term_content,
                                }
                            )

                elif action == "deny":
                    results["processed"].append(
                        {"memory_id": memory_id, "action": "denied"}
                    )

                # Update the short-term memory to remove pending status
                memory.metadata["pending_long_term_consent"] = False
                memory.metadata["consent_processed"] = True
                memory.metadata["consent_action"] = action
                await self.redis_store.add_memory(user_id, memory)  # Update in Redis

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
