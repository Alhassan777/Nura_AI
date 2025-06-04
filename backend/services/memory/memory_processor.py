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
        return MemoryItem(
            id=memory_id,
            userId=user_id,
            content=content,
            type=type,
            metadata=metadata or {},
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
        """Process a single memory component."""
        score_metadata = score.metadata or {}
        component_content = score_metadata.get("component_content", base_memory.content)
        memory_type = score_metadata.get("memory_type", "temporary_state")
        storage_recommendation = score_metadata.get(
            "storage_recommendation", "probably_skip"
        )

        # Create component memory
        component_memory = MemoryItem(
            id=f"{base_memory.id}_component_{score_metadata.get('component_index', 0)}",
            userId=base_memory.userId,
            content=component_content,
            type=base_memory.type,
            metadata={
                **base_memory.metadata,
                "original_message": base_memory.content,
                "component_index": score_metadata.get("component_index", 0),
                "total_components": score_metadata.get("total_components", 1),
            },
            timestamp=base_memory.timestamp,
        )

        # Determine if we should store this component
        should_store_somewhere = self._should_store_component(
            is_chat_message, is_assistant_message, memory_type, storage_recommendation
        )

        if not should_store_somewhere:
            return {
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

        # Component meets storage criteria
        return {
            "component_content": component_content,
            "memory_type": memory_type,
            "storage_recommendation": storage_recommendation,
            "stored": True,
            "component_memory": component_memory,
            "score": {
                "relevance": float(score.relevance),
                "stability": float(score.stability),
                "explicitness": float(score.explicitness),
            },
        }

    def _should_store_component(
        self,
        is_chat_message: bool,
        is_assistant_message: bool,
        memory_type: str,
        storage_recommendation: str,
    ) -> bool:
        """Determine if a component should be stored."""
        return (
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

    def _build_processing_result(
        self,
        memory_scores: List[MemoryScore],
        stored_components: List[Dict[str, Any]],
        all_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the final processing result."""
        if not stored_components:
            return {
                "needs_consent": False,
                "stored": False,
                "reason": "No components met storage criteria",
                "components": all_results,
                "total_components": len(memory_scores),
                "stored_components": 0,
            }

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
                "emotional_anchors": sum(
                    1
                    for c in stored_components
                    if c.get("memory_type") == "meaningful_connection"
                ),
            },
        }
