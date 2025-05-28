"""
Retrieval processor for memory context, classification, and statistics.
"""

from typing import Dict, Any, List, Optional
from dataclasses import asdict

from ..types import MemoryItem, MemoryContext, MemoryStats
from ..storage.redis_store import RedisStore
from ..storage.vector_store import VectorStore
from ..audit.audit_logger import AuditLogger


class RetrievalProcessor:
    """Handles memory retrieval, context generation, and classification."""

    def __init__(
        self,
        redis_store: RedisStore,
        vector_store: VectorStore,
        audit_logger: AuditLogger,
    ):
        self.redis_store = redis_store
        self.vector_store = vector_store
        self.audit_logger = audit_logger

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

    async def get_user_memories(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user with optional date filtering."""
        try:
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

            # Apply date filtering if provided
            if start_date or end_date:
                all_memories = self._filter_memories_by_date(
                    all_memories, start_date, end_date
                )

            return all_memories

        except Exception as e:
            self.audit_logger.log_error(user_id, "get_user_memories", str(e))
            raise e

    def _memory_to_dict(self, memory: MemoryItem, storage_type: str) -> Dict[str, Any]:
        """Convert a memory item to dictionary format."""
        memory_dict = {
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

        # Add PII detection if available
        if memory.metadata.get("has_pii"):
            memory_dict["pii_detected"] = True
            memory_dict["risk_level"] = memory.metadata.get("risk_level", "medium")
        else:
            memory_dict["pii_detected"] = False
            memory_dict["risk_level"] = "low"

        return memory_dict

    def _filter_memories_by_date(
        self,
        memories: List[Dict[str, Any]],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Filter memories by date range."""
        from datetime import datetime

        filtered_memories = []

        for memory in memories:
            memory_date = memory["timestamp"]
            if isinstance(memory_date, str):
                try:
                    memory_date = datetime.fromisoformat(
                        memory_date.replace("Z", "+00:00")
                    )
                except:
                    continue

            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                if memory_date < start_dt:
                    continue

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if memory_date > end_dt:
                    continue

            filtered_memories.append(memory)

        return filtered_memories

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
