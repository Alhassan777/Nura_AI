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
            project_id=Config.GOOGLE_CLOUD_PROJECT,
            use_vertex=Config.USE_VERTEX_AI,
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
        is_chat_message = (
            type in ["user_message", "assistant_message", "chat"]
            and metadata
            and metadata.get("source") == "chat_interface"
        )

        if is_chat_message:
            # Store immediately in short-term for chat continuity
            # PII will be handled when user reviews memories at end of session
            pii_results = {
                "has_pii": False,
                "detected_items": [],
                "needs_consent": False,
            }
        else:
            # For non-chat memories, use normal PII detection
            pii_results = await self.pii_detector.detect_pii(base_memory)

            # If PII detected and no consent provided, return consent options
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

        # Score memory for therapeutic value (separate from PII)
        score = self.scorer.score_memory(base_memory)

        # Check if memory should be stored based on therapeutic value
        should_store = self.scorer.should_store_memory(
            score,
            {
                "relevance": self.config.relevance_threshold,
                "stability": self.config.stability_threshold,
                "explicitness": self.config.explicitness_threshold,
                "min_score": self.config.min_score_threshold,
            },
        )

        # Always store chat messages for conversation continuity
        if not should_store and not is_chat_message:
            return {
                "needs_consent": False,
                "stored": False,
                "reason": "Memory did not meet therapeutic value criteria",
                "score": {
                    "relevance": float(score.relevance),
                    "stability": float(score.stability),
                    "explicitness": float(score.explicitness),
                },
            }

        # Apply dual storage strategy
        result = await self._store_with_dual_strategy(
            user_id, base_memory, score, pii_results, user_consent or {}
        )

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

        # Determine storage destinations based on stability score
        will_store_short_term = True  # Almost always store in short-term for context
        will_store_long_term = score.stability > self.config.stability_threshold

        stored_memories = {}

        # STEP 1: Store in SHORT-TERM (Redis) - more permissive with PII
        if will_store_short_term:
            short_term_content = await self.pii_detector.apply_granular_consent(
                base_memory.content, "short_term", user_consent, pii_results
            )

            short_term_memory = MemoryItem(
                id=base_memory.id + "_short",
                userId=user_id,
                content=short_term_content,
                type=base_memory.type,
                metadata={
                    **base_memory.metadata,
                    "storage_type": "short_term",
                    "has_pii": pii_results["has_pii"],
                    "detected_items": [
                        item["id"] for item in pii_results.get("detected_items", [])
                    ],
                    "score": {
                        "relevance": float(score.relevance),
                        "stability": float(score.stability),
                        "explicitness": float(score.explicitness),
                    },
                    "pii_strategy": "permissive_for_personalization",
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
                metadata={"storage_type": "short_term", "pii_handling": "permissive"},
            )

        # STEP 2: Store in LONG-TERM (Vector DB) - more conservative with PII
        if will_store_long_term:
            long_term_content = await self.pii_detector.apply_granular_consent(
                base_memory.content, "long_term", user_consent, pii_results
            )

            long_term_memory = MemoryItem(
                id=base_memory.id + "_long",
                userId=user_id,
                content=long_term_content,
                type=base_memory.type,
                metadata={
                    **base_memory.metadata,
                    "storage_type": "long_term",
                    "has_pii": pii_results["has_pii"],
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
            return ""

        # Create a simple digest from recent memories
        recent_contents = [m.content for m in memories[-5:]]  # Last 5 memories
        return f"Recent context: {'; '.join(recent_contents)}"

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
