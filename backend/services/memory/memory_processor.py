"""
Memory processor for extracting and scoring memories.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from .types import MemoryItem, MemoryScore
from .storage.redis_store import RedisStore
from .storage.vector_store import VectorStore
from utils.scoring.gemini_scorer import GeminiScorer
from ..privacy.security.pii_detector import PIIDetector
from services.audit.audit_logger import AuditLogger
from .config import Config


class MemoryProcessor:
    """Handles core memory processing logic."""

    def __init__(
        self, scorer: GeminiScorer, pii_detector: PIIDetector, audit_logger: AuditLogger
    ):
        self.scorer = scorer
        self.pii_detector = pii_detector
        self.audit_logger = audit_logger

    def create_base_memory(
        self,
        user_id: str,
        content: str,
        type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Create a base memory item."""
        memory_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["user_id"] = user_id  # Store user_id in metadata for security
        return MemoryItem(
            id=memory_id,
            content=content,
            type=type,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )

    def is_chat_message(
        self, memory_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if this is a chat message."""
        return memory_type in ["user_message", "assistant_message", "chat"]

    def is_assistant_message(
        self, memory_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if this is an assistant message."""
        return memory_type == "assistant_message" or (
            metadata and metadata.get("source") == "assistant"
        )

    async def process_memory_components(
        self,
        base_memory: MemoryItem,
        pii_results: Dict[str, Any],
        user_consent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process memory components and determine storage strategy."""
        is_chat_message = self.is_chat_message(base_memory.type, base_memory.metadata)
        is_assistant_message = self.is_assistant_message(
            base_memory.type, base_memory.metadata
        )

        # Score memory for therapeutic value
        memory_scores = self.scorer.score_memory(base_memory)

        # Process each component separately
        stored_components = []
        all_results = []

        for score in memory_scores:
            component_result = await self._process_single_component(
                base_memory,
                score,
                pii_results,
                user_consent or {},
                is_chat_message,
                is_assistant_message,
            )
            all_results.append(component_result)

            if component_result.get("stored"):
                stored_components.append(component_result)

        return self._build_processing_result(
            memory_scores, stored_components, all_results
        )

    async def _process_single_component(
        self,
        base_memory: MemoryItem,
        score: MemoryScore,
        pii_results: Dict[str, Any],
        user_consent: Dict[str, Any],
        is_chat_message: bool,
        is_assistant_message: bool,
    ) -> Dict[str, Any]:
        """Process a single memory component with simplified structure support."""
        score_metadata = score.metadata or {}
        component_content = score_metadata.get("component_content", base_memory.content)

        # Use new simplified structure
        memory_category = score_metadata.get("memory_category", "short_term")
        is_meaningful = score_metadata.get("is_meaningful", False)
        is_lasting = score_metadata.get("is_lasting", False)
        is_symbolic = score_metadata.get("is_symbolic", False)

        # Create component memory
        component_memory = MemoryItem(
            id=f"{base_memory.id}_component_{score_metadata.get('component_index', 0)}",
            content=component_content,
            type=base_memory.type,
            metadata={
                **base_memory.metadata,
                "original_message": base_memory.content,
                "component_index": score_metadata.get("component_index", 0),
                "total_components": score_metadata.get("total_components", 1),
                # Add the simple classification fields
                "memory_category": memory_category,
                "is_meaningful": is_meaningful,
                "is_lasting": is_lasting,
                "is_symbolic": is_symbolic,
            },
            timestamp=base_memory.timestamp,
        )

        # Determine if we should store this component using simplified logic
        should_store_somewhere = self._should_store_component_simple(
            is_chat_message,
            is_assistant_message,
            memory_category,
            is_meaningful,
            is_lasting,
        )

        if not should_store_somewhere:
            return {
                "component_content": component_content,
                "memory_category": memory_category,
                "is_meaningful": is_meaningful,
                "is_lasting": is_lasting,
                "is_symbolic": is_symbolic,
                "stored": False,
                "reason": "Story naturally fades or was assistant message",
                "score": {
                    "relevance": float(score.relevance),
                    "stability": float(score.stability),
                    "explicitness": float(score.explicitness),
                },
            }

        # Component meets storage criteria
        return {
            "component_content": component_content,
            "memory_category": memory_category,
            "is_meaningful": is_meaningful,
            "is_lasting": is_lasting,
            "is_symbolic": is_symbolic,
            "stored": True,
            "component_memory": component_memory,
            "score": {
                "relevance": float(score.relevance),
                "stability": float(score.stability),
                "explicitness": float(score.explicitness),
            },
        }

    def _should_store_component_simple(
        self,
        is_chat_message: bool,
        is_assistant_message: bool,
        memory_category: str,
        is_meaningful: bool,
        is_lasting: bool,
    ) -> bool:
        """
        SIMPLE LOGIC: Should we store this component?

        Rules:
        - Never store assistant messages
        - Always store user chat messages in short-term for context
        - For long-term: meaningful + lasting = store, incidental = skip
        """
        # Never store assistant messages
        if is_assistant_message:
            return False

        # Always store user chat messages for context (they'll go to short-term first)
        if is_chat_message and not is_assistant_message:
            return True

        # For non-chat memories, use simple meaningful/lasting logic
        is_meaningful_and_lasting = is_meaningful and is_lasting

        return is_meaningful_and_lasting

    def _build_processing_result(
        self,
        memory_scores: List[MemoryScore],
        stored_components: List[Dict[str, Any]],
        all_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the final processing result with simplified classification."""
        if not stored_components:
            return {
                "needs_consent": False,
                "stored": False,
                "reason": "No stories met preservation criteria",
                "components": all_results,
                "total_components": len(memory_scores),
                "stored_components": 0,
            }

        # Count simplified types
        emotional_anchors = sum(
            1
            for c in stored_components
            if c.get("memory_category") == "emotional_anchor"
        )

        long_term_memories = sum(
            1 for c in stored_components if c.get("memory_category") == "long_term"
        )

        short_term_memories = sum(
            1 for c in stored_components if c.get("memory_category") == "short_term"
        )

        return {
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
                "emotional_anchors": emotional_anchors,
                "long_term_memories": long_term_memories,
                "short_term_memories": short_term_memories,
                "simple_processing": True,
            },
        }
