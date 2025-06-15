"""
Retrieval processor for memory search and context building.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .types import MemoryItem, MemoryContext, MemoryStats
from .storage.redis_store import RedisStore
from .storage.vector_store import VectorStore
from services.audit.audit_logger import AuditLogger
import dotenv

dotenv.load_dotenv("backend/.env")


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
        self,
        user_id: str,
        query: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> MemoryContext:
        """Get memory context for a user, optionally scoped to a conversation."""
        # Get short-term memories (conversation-scoped if available)
        if conversation_id:
            short_term = await self.redis_store.get_conversation_memories(
                conversation_id
            )
        else:
            short_term = await self.redis_store.get_user_memories(user_id)

        # Get long-term memories
        long_term = []
        if query:
            # Use semantic search with the provided query
            search_results = await self.vector_store.similarity_search(
                query=query, user_id=user_id, k=5
            )
            long_term = self._convert_search_results_to_memories(search_results)
        else:
            # If no query provided, use the most recent short-term memory as context
            # to find relevant long-term memories
            if short_term:
                # Use the most recent message as the query for semantic search
                recent_message = short_term[0].content  # Redis returns newest first
                search_results = await self.vector_store.similarity_search(
                    query=recent_message, user_id=user_id, k=3
                )
                long_term = self._convert_search_results_to_memories(search_results)

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
        try:
            short_term_memories = await self.redis_store.get_user_memories(user_id)
            short_term_count = len(short_term_memories)
        except Exception:
            short_term_count = 0
            short_term_memories = []

        try:
            long_term_memories = await self.vector_store.get_user_memories(user_id)
            long_term_count = len(long_term_memories)
        except Exception:
            long_term_count = 0
            long_term_memories = []

        # Count emotional anchors from both stores
        emotional_anchors_count = 0
        all_memories = []

        # Add short-term memories to all_memories and count emotional anchors
        for memory in short_term_memories:
            all_memories.append(memory)
            if memory.metadata.get("memory_category") == "emotional_anchor":
                emotional_anchors_count += 1

        # Add long-term memories to all_memories and count emotional anchors
        for memory_dict in long_term_memories:
            all_memories.append(memory_dict)
            if (
                memory_dict.get("metadata", {}).get("memory_category")
                == "emotional_anchor"
            ):
                emotional_anchors_count += 1

        # Calculate recent activity
        recent_activity = await self._calculate_recent_activity(all_memories)

        return MemoryStats(
            total=short_term_count + long_term_count,
            short_term=short_term_count,
            long_term=long_term_count,
            sensitive=await self._get_sensitive_count(user_id),
            emotional_anchors=emotional_anchors_count,
            recent_activity=recent_activity,
        )

    async def get_emotional_anchors(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> List[MemoryItem]:
        """Get emotional anchors for a user - symbolic memories that provide emotional grounding."""
        try:
            # Search both Redis and vector store for comprehensive results
            anchors = []

            # Check Redis (short-term) first
            try:
                short_term_memories = await self.redis_store.get_user_memories(user_id)
                for memory in short_term_memories:
                    # Filter by conversation_id if provided
                    if (
                        conversation_id
                        and memory.metadata.get("conversation_id") != conversation_id
                    ):
                        continue

                    if memory.metadata.get("memory_category") == "emotional_anchor":
                        anchors.append(memory)
                        logging.debug(
                            f"Found emotional anchor in Redis: {memory.content[:50]}..."
                        )
            except Exception as e:
                logging.warning(f"Error checking Redis for emotional anchors: {str(e)}")

            # Check vector store (long-term)
            try:
                all_long_term = await self.vector_store.get_user_memories(user_id)
                all_long_term = self._convert_memory_dicts_to_memories(all_long_term)

                for memory in all_long_term:
                    # Filter by conversation_id if provided
                    if (
                        conversation_id
                        and memory.metadata.get("conversation_id") != conversation_id
                    ):
                        continue

                    if memory.metadata.get("memory_category") == "emotional_anchor":
                        anchors.append(memory)
                        logging.debug(
                            f"Found emotional anchor in vector store: {memory.content[:50]}..."
                        )
            except Exception as e:
                logging.warning(
                    f"Error checking vector store for emotional anchors: {str(e)}"
                )

            logging.info(
                f"Found {len(anchors)} emotional anchors for user {user_id}"
                + (f" in conversation {conversation_id}" if conversation_id else "")
            )
            return anchors

        except Exception as e:
            logging.error(
                f"Error retrieving emotional anchors for user {user_id}: {str(e)}"
            )
            return []

    def _is_emotional_anchor(self, memory: MemoryItem) -> bool:
        """Simple check: Is this memory an emotional anchor (symbolic)?"""
        return (
            memory.metadata.get("is_emotional_anchor", False)
            or memory.metadata.get("memory_type") == "emotional_anchor"
            or memory.metadata.get("memory_nature") == "emotional_anchor"
            or "symbolic" in memory.metadata.get("memory_nature", "").lower()
            or "anchor" in memory.metadata.get("memory_type", "").lower()
        )

    async def get_regular_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """Get regular lasting memories (excluding emotional anchors) for a user."""
        try:
            if query:
                # Use semantic search
                search_results = await self.vector_store.similarity_search(
                    query=query, user_id=user_id, k=20
                )
                all_memories = self._convert_search_results_to_memories(search_results)
                logging.info(
                    f"Query search returned {len(all_memories)} memories for user {user_id}"
                )
            else:
                # Get all long-term memories
                all_memories = await self.vector_store.get_user_memories(user_id)
                logging.info(
                    f"Vector store returned {len(all_memories)} memory dicts for user {user_id}"
                )
                all_memories = self._convert_memory_dicts_to_memories(all_memories)
                logging.info(
                    f"Converted to {len(all_memories)} MemoryItem objects for user {user_id}"
                )

            # Filter by conversation_id if provided
            if conversation_id:
                filtered_memories = []
                for memory in all_memories:
                    if memory.metadata.get("conversation_id") == conversation_id:
                        filtered_memories.append(memory)
                all_memories = filtered_memories
                logging.info(
                    f"Filtered to {len(all_memories)} memories for conversation {conversation_id}"
                )

            # NO FILTERING: Return all long-term memories regardless of category
            # You should see ALL your stored memories, not just specific categories
            logging.info(
                f"Returning {len(all_memories)} memories for user {user_id}"
                + (f" in conversation {conversation_id}" if conversation_id else "")
                + " (no category filtering applied)"
            )
            return all_memories

        except Exception as e:
            logging.error(
                f"Error retrieving regular memories for user {user_id}: {str(e)}"
            )
            return []

    async def get_user_memories(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user with optional date filtering."""
        try:
            # Get memories from both stores
            short_term_memories = await self.redis_store.get_user_memories(user_id)
            long_term_memories = await self.vector_store.get_user_memories(user_id)

            all_memories = []

            # Convert short-term memories to dict format
            for memory in short_term_memories:
                memory_dict = self._memory_to_dict(memory, "short_term")
                all_memories.append(memory_dict)

            # Process long-term memories - they're already dictionaries from vector store
            for memory_dict in long_term_memories:
                # Vector store returns dictionaries, so we need to add storage_type
                memory_dict = dict(memory_dict)  # Create a copy
                memory_dict["storage_type"] = "long_term"

                # Add PII detection if available
                metadata = memory_dict.get("metadata", {})
                if metadata.get("has_pii"):
                    memory_dict["pii_detected"] = True
                    memory_dict["risk_level"] = metadata.get("risk_level", "medium")
                else:
                    memory_dict["pii_detected"] = False
                    memory_dict["risk_level"] = "low"

                all_memories.append(memory_dict)

            # Apply date filtering if provided
            if start_date or end_date:
                all_memories = self._filter_memories_by_date(
                    all_memories, start_date, end_date
                )

            return all_memories

        except Exception as e:
            await self.audit_logger.log_event(
                event_type="get_user_memories_error",
                user_id=user_id,
                level="ERROR",
                details={"error": str(e)},
            )
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

    def _convert_search_results_to_memories(
        self, search_results: List[Dict[str, Any]]
    ) -> List[MemoryItem]:
        """Convert vector store search results to MemoryItem objects."""
        memories = []
        for result in search_results:
            try:
                memory = MemoryItem(
                    id=result.get("memory_id", ""),
                    content=result.get("content", ""),
                    type=result["metadata"].get("type", "chat"),
                    timestamp=datetime.fromisoformat(
                        result["metadata"].get(
                            "timestamp", datetime.utcnow().isoformat()
                        )
                    ),
                    metadata=result.get("metadata", {}),
                )
                memories.append(memory)
            except Exception as e:
                logging.warning(f"Failed to convert search result to memory: {e}")
        return memories

    def _convert_memory_dicts_to_memories(
        self, memory_dicts: List[Dict[str, Any]]
    ) -> List[MemoryItem]:
        """Convert memory dictionaries to MemoryItem objects."""
        memories = []
        for mem_dict in memory_dicts:
            try:
                # Ensure we have the required fields
                if not mem_dict.get("memory_id") and not mem_dict.get("id"):
                    logging.warning(
                        f"Memory dict missing id/memory_id field: {mem_dict}"
                    )
                    continue

                memory_id = mem_dict.get("memory_id") or mem_dict.get("id")
                content = mem_dict.get("content", "")
                metadata = mem_dict.get("metadata", {})

                # Handle timestamp conversion more robustly
                timestamp_str = mem_dict.get("timestamp")
                if timestamp_str:
                    if isinstance(timestamp_str, str):
                        try:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            # Try parsing without timezone info
                            timestamp = datetime.fromisoformat(
                                timestamp_str.split("+")[0].split("Z")[0]
                            )
                    else:
                        timestamp = timestamp_str  # Assume it's already a datetime
                else:
                    timestamp = datetime.utcnow()

                memory = MemoryItem(
                    id=memory_id,
                    content=content,
                    type=metadata.get("type", "chat"),
                    timestamp=timestamp,
                    metadata=metadata,
                )
                memories.append(memory)
            except Exception as e:
                logging.error(
                    f"Failed to convert memory dict to memory: {e}, dict: {mem_dict}"
                )
                # Skip this memory rather than adding a broken one
                continue

        logging.info(
            f"Converted {len(memories)} out of {len(memory_dicts)} memory dicts to MemoryItem objects"
        )
        return memories

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
            short_term_memories = await self.redis_store.get_user_memories(user_id)
            sensitive_count = sum(
                1
                for memory in short_term_memories
                if memory.metadata.get("has_pii", False)
            )
            return sensitive_count
        except Exception:
            return 0

    async def _calculate_recent_activity(self, all_memories) -> Dict[str, Any]:
        """Calculate recent memory activity statistics."""
        from datetime import datetime, timedelta
        import logging

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        memories_today = 0
        memories_this_week = 0
        last_memory_timestamp = None
        latest_timestamp = None

        logging.info(f"Calculating recent activity for {len(all_memories)} memories")
        logging.info(f"Today start: {today_start}, Week start: {week_start}")

        for memory in all_memories:
            # Handle both MemoryItem objects and dictionaries
            if hasattr(memory, "timestamp"):
                timestamp = memory.timestamp
            elif isinstance(memory, dict):
                timestamp_str = memory.get("timestamp") or memory.get(
                    "metadata", {}
                ).get("timestamp")
                if timestamp_str:
                    try:
                        # Handle various timestamp formats
                        if timestamp_str.endswith("Z"):
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                        elif "+" in timestamp_str or timestamp_str.endswith("00:00"):
                            timestamp = datetime.fromisoformat(timestamp_str)
                        else:
                            # Assume UTC if no timezone info
                            timestamp = datetime.fromisoformat(timestamp_str)
                    except Exception as e:
                        logging.warning(
                            f"Failed to parse timestamp {timestamp_str}: {e}"
                        )
                        continue
                else:
                    continue
            else:
                continue

            # Track latest timestamp
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp
                last_memory_timestamp = timestamp.isoformat()

            # Count memories today and this week
            if timestamp >= today_start:
                memories_today += 1
            if timestamp >= week_start:
                memories_this_week += 1

        logging.info(
            f"Recent activity calculated: today={memories_today}, week={memories_this_week}"
        )

        return {
            "memories_added_today": memories_today,
            "memories_added_this_week": memories_this_week,
            "last_memory_timestamp": last_memory_timestamp,
        }
