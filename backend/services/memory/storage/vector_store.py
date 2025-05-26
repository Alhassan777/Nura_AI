import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

# Import Pinecone
try:
    from pinecone import Pinecone, ServerlessSpec

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning(
        "Pinecone not available - install with: pip install pinecone-client"
    )

from ..types import MemoryItem
from ..config import Config

# Set up logging
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        persist_directory: str = None,
        use_pinecone: bool = False,
        vector_db_type: str = "chroma",
    ):
        # Determine which vector database to use
        self.vector_db_type = vector_db_type.lower()
        self.use_pinecone = use_pinecone or (self.vector_db_type == "pinecone")
        self.persist_directory = persist_directory

        # Initialize embedding model (always needed)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        try:
            if self.use_pinecone:
                self._initialize_pinecone()
            else:
                self._initialize_chroma(persist_directory)
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {str(e)}")
            raise

    def _initialize_pinecone(self):
        """Initialize Pinecone vector database."""
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "Pinecone not available. Install with: pip install pinecone-client"
            )

        api_key = Config.PINECONE_API_KEY
        index_name = Config.PINECONE_INDEX_NAME

        if not api_key:
            raise ValueError("PINECONE_API_KEY must be set")

        # Initialize Pinecone client
        self.pinecone_client = Pinecone(api_key=api_key)

        # Check if index exists, create if not
        existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]

        if index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {index_name}")

            try:
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=768,  # Gemini embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1",
                    ),
                )
                logger.info(f"Created Pinecone index: {index_name}")
            except Exception as e:
                # If default fails, try GCP
                try:
                    self.pinecone_client.create_index(
                        name=index_name,
                        dimension=768,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="gcp", region="us-central1"),
                    )
                    logger.info(f"Created Pinecone index: {index_name} on GCP")
                except Exception as e2:
                    raise Exception(
                        f"Could not create Pinecone index {index_name}. Please create it manually in the Pinecone console at https://app.pinecone.io/. Error: {str(e2)}"
                    )

        # Connect to the index
        self.pinecone_index = self.pinecone_client.Index(index_name)
        logger.info(f"Initialized VectorStore with Pinecone index: {index_name}")

    def _initialize_chroma(self, persist_directory: str):
        """Initialize ChromaDB vector database."""
        # Initialize Chroma
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="memories", metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized VectorStore with ChromaDB at {persist_directory}")

    def _convert_timestamp_to_datetime(self, timestamp_str) -> datetime:
        """Convert timestamp string back to datetime object."""
        if not timestamp_str:
            return None

        try:
            # Handle both ISO format with and without timezone
            if isinstance(timestamp_str, str):
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                return timestamp_str
        except ValueError:
            logger.warning(
                f"Could not parse timestamp {timestamp_str}, using current time"
            )
            return datetime.utcnow()

    async def add_memory(self, user_id: str, memory: MemoryItem) -> None:
        """Add a memory to the vector store."""
        try:
            # Generate embedding
            embedding = await self._get_embedding(memory.content)
            memory.embedding = embedding

            if self.use_pinecone:
                await self._add_memory_pinecone(user_id, memory, embedding)
            else:
                await self._add_memory_chroma(user_id, memory, embedding)

        except Exception as e:
            logger.error(
                f"Failed to add memory {memory.id} for user {user_id}: {str(e)}"
            )
            raise

    async def update_memory(self, user_id: str, memory: MemoryItem) -> bool:
        """Update an existing memory or add it if it doesn't exist."""
        try:
            # Generate embedding
            embedding = await self._get_embedding(memory.content)
            memory.embedding = embedding

            if self.use_pinecone:
                # Pinecone upsert automatically handles updates
                await self._add_memory_pinecone(user_id, memory, embedding)
            else:
                # For ChromaDB, we need to delete and re-add
                await self._delete_memory_chroma(user_id, memory.id)
                await self._add_memory_chroma(user_id, memory, embedding)

            logger.info(f"Updated memory {memory.id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update memory {memory.id} for user {user_id}: {str(e)}"
            )
            return False

    async def _add_memory_pinecone(
        self, user_id: str, memory: MemoryItem, embedding: List[float]
    ) -> None:
        """Add memory to Pinecone."""
        metadata = {
            "user_id": user_id,
            "content": memory.content,
            "type": memory.type,
            "timestamp": memory.timestamp.isoformat(),
            **{
                k: str(v) for k, v in memory.metadata.items()
            },  # Pinecone requires string values
        }

        # Upsert to Pinecone
        self.pinecone_index.upsert(vectors=[(memory.id, embedding, metadata)])
        logger.info(f"Added memory {memory.id} for user {user_id} to Pinecone")

    async def _add_memory_chroma(
        self, user_id: str, memory: MemoryItem, embedding: List[float]
    ) -> None:
        """Add memory to ChromaDB."""
        # Add to Chroma
        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            metadatas=[
                {
                    "user_id": user_id,
                    "content": memory.content,
                    "type": memory.type,
                    "timestamp": memory.timestamp.isoformat(),
                    **memory.metadata,
                }
            ],
        )
        logger.info(f"Added memory {memory.id} for user {user_id} to ChromaDB")

    async def get_similar_memories(
        self, user_id: str, query: str, limit: int = 5
    ) -> List[MemoryItem]:
        """Get similar memories for a query."""
        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)

            if self.use_pinecone:
                return await self._get_similar_memories_pinecone(
                    user_id, query_embedding, limit
                )
            else:
                return await self._get_similar_memories_chroma(
                    user_id, query_embedding, limit
                )

        except Exception as e:
            logger.error(f"Failed to get similar memories for user {user_id}: {str(e)}")
            return []

    async def _get_similar_memories_pinecone(
        self, user_id: str, query_embedding: List[float], limit: int
    ) -> List[MemoryItem]:
        """Get similar memories from Pinecone."""
        # Query Pinecone with user filter
        results = self.pinecone_index.query(
            vector=query_embedding,
            top_k=limit,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
        )

        # Convert results to MemoryItems
        memories = []
        for match in results.matches:
            metadata = match.metadata

            # Convert timestamp back to datetime object
            timestamp_str = metadata.get("timestamp")
            timestamp = None
            if timestamp_str:
                try:
                    # Handle both ISO format with and without timezone
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str
                except ValueError:
                    logger.warning(
                        f"Could not parse timestamp {timestamp_str}, using current time"
                    )
                    timestamp = datetime.utcnow()

            memory = MemoryItem(
                id=match.id,
                userId=user_id,
                content=metadata["content"],
                type=metadata["type"],
                timestamp=timestamp,
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k not in ["user_id", "content", "type", "timestamp"]
                },
                embedding=None,  # Don't store embedding in memory object
            )
            memories.append(memory)

        logger.info(
            f"Retrieved {len(memories)} similar memories for user {user_id} from Pinecone"
        )
        return memories

    async def _get_similar_memories_chroma(
        self, user_id: str, query_embedding: List[float], limit: int
    ) -> List[MemoryItem]:
        """Get similar memories from ChromaDB."""
        # Query Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"user_id": user_id},
        )

        # Convert results to MemoryItems
        memories = []
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]

            # Convert timestamp back to datetime object
            timestamp_str = metadata.get("timestamp")
            timestamp = None
            if timestamp_str:
                try:
                    # Handle both ISO format with and without timezone
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str
                except ValueError:
                    logger.warning(
                        f"Could not parse timestamp {timestamp_str}, using current time"
                    )
                    timestamp = datetime.utcnow()

            memory = MemoryItem(
                id=results["ids"][0][i],
                userId=user_id,
                content=metadata["content"],
                type=metadata["type"],
                timestamp=timestamp,
                metadata=metadata,
                embedding=(
                    results["embeddings"][0][i] if results["embeddings"] else None
                ),
            )
            memories.append(memory)

        logger.info(
            f"Retrieved {len(memories)} similar memories for user {user_id} from ChromaDB"
        )
        return memories

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a memory from the vector store."""
        try:
            if self.use_pinecone:
                return await self._delete_memory_pinecone(user_id, memory_id)
            else:
                return await self._delete_memory_chroma(user_id, memory_id)

        except Exception as e:
            logger.error(
                f"Failed to delete memory {memory_id} for user {user_id}: {str(e)}"
            )
            return False

    async def _delete_memory_pinecone(self, user_id: str, memory_id: str) -> bool:
        """Delete memory from Pinecone."""
        self.pinecone_index.delete(ids=[memory_id])
        logger.info(f"Deleted memory {memory_id} for user {user_id} from Pinecone")
        return True

    async def _delete_memory_chroma(self, user_id: str, memory_id: str) -> bool:
        """Delete memory from ChromaDB."""
        self.collection.delete(ids=[memory_id], where={"user_id": user_id})
        logger.info(f"Deleted memory {memory_id} for user {user_id} from ChromaDB")
        return True

    async def clear_memories(self, user_id: str) -> None:
        """Clear all memories for a user."""
        try:
            if self.use_pinecone:
                await self._clear_memories_pinecone(user_id)
            else:
                await self._clear_memories_chroma(user_id)

        except Exception as e:
            logger.error(f"Failed to clear memories for user {user_id}: {str(e)}")
            raise

    async def _clear_memories_pinecone(self, user_id: str) -> None:
        """Clear all memories for a user from Pinecone."""
        # Query all memories for user first
        results = self.pinecone_index.query(
            vector=[0.0] * 768,  # Dummy vector
            top_k=10000,  # Large number to get all
            filter={"user_id": {"$eq": user_id}},
            include_metadata=False,
        )

        if results.matches:
            # Delete all found memories
            memory_ids = [match.id for match in results.matches]
            self.pinecone_index.delete(ids=memory_ids)
            logger.info(
                f"Cleared {len(memory_ids)} memories for user {user_id} from Pinecone"
            )
        else:
            logger.info(f"No memories found to clear for user {user_id} in Pinecone")

    async def _clear_memories_chroma(self, user_id: str) -> None:
        """Clear all memories for a user from ChromaDB."""
        # Get count before deletion
        existing = self.collection.get(where={"user_id": user_id})
        count = len(existing["ids"]) if existing["ids"] else 0

        # Delete from Chroma
        self.collection.delete(where={"user_id": user_id})
        logger.info(f"Cleared {count} memories for user {user_id} from ChromaDB")

    async def get_memory_count(self, user_id: str) -> int:
        """Get the number of memories for a user."""
        try:
            if self.use_pinecone:
                return await self._get_memory_count_pinecone(user_id)
            else:
                return await self._get_memory_count_chroma(user_id)

        except Exception as e:
            logger.error(f"Failed to get memory count for user {user_id}: {str(e)}")
            return 0

    async def _get_memory_count_pinecone(self, user_id: str) -> int:
        """Get memory count from Pinecone."""
        # Query with dummy vector to get count
        results = self.pinecone_index.query(
            vector=[0.0] * 768,
            top_k=10000,  # Large number to get all
            filter={"user_id": {"$eq": user_id}},
            include_metadata=False,
        )
        count = len(results.matches)
        logger.debug(f"User {user_id} has {count} memories in Pinecone")
        return count

    async def _get_memory_count_chroma(self, user_id: str) -> int:
        """Get memory count from ChromaDB."""
        # Get count from Chroma
        existing = self.collection.get(where={"user_id": user_id})
        count = len(existing["ids"]) if existing["ids"] else 0
        logger.debug(f"User {user_id} has {count} memories in ChromaDB")
        return count

    async def get_memories(self, user_id: str, limit: int = 1000) -> List[MemoryItem]:
        """Get all memories for a user."""
        try:
            if self.use_pinecone:
                return await self._get_memories_pinecone(user_id, limit)
            else:
                return await self._get_memories_chroma(user_id, limit)

        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {str(e)}")
            return []

    async def _get_memories_pinecone(
        self, user_id: str, limit: int
    ) -> List[MemoryItem]:
        """Get all memories from Pinecone."""
        # Query with dummy vector to get all memories
        results = self.pinecone_index.query(
            vector=[0.0] * 768,  # Dummy vector
            top_k=limit,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
        )

        # Convert results to MemoryItems
        memories = []
        for match in results.matches:
            metadata = match.metadata

            # Convert timestamp back to datetime object
            timestamp_str = metadata.get("timestamp")
            timestamp = None
            if timestamp_str:
                try:
                    # Handle both ISO format with and without timezone
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str
                except ValueError:
                    logger.warning(
                        f"Could not parse timestamp {timestamp_str}, using current time"
                    )
                    timestamp = datetime.utcnow()

            memory = MemoryItem(
                id=match.id,
                userId=user_id,
                content=metadata["content"],
                type=metadata["type"],
                timestamp=timestamp,
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k not in ["user_id", "content", "type", "timestamp"]
                },
                embedding=None,  # Don't store embedding in memory object
            )
            memories.append(memory)

        logger.info(
            f"Retrieved {len(memories)} memories for user {user_id} from Pinecone"
        )
        return memories

    async def _get_memories_chroma(self, user_id: str, limit: int) -> List[MemoryItem]:
        """Get all memories from ChromaDB."""
        # Get all memories from Chroma
        results = self.collection.get(
            where={"user_id": user_id},
            limit=limit,
        )

        # Convert results to MemoryItems
        memories = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]

            # Convert timestamp back to datetime object
            timestamp_str = metadata.get("timestamp")
            timestamp = None
            if timestamp_str:
                try:
                    # Handle both ISO format with and without timezone
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str
                except ValueError:
                    logger.warning(
                        f"Could not parse timestamp {timestamp_str}, using current time"
                    )
                    timestamp = datetime.utcnow()

            memory = MemoryItem(
                id=results["ids"][i],
                userId=user_id,
                content=metadata["content"],
                type=metadata["type"],
                timestamp=timestamp,
                metadata=metadata,
                embedding=None,  # Don't include embeddings by default
            )
            memories.append(memory)

        logger.info(
            f"Retrieved {len(memories)} memories for user {user_id} from ChromaDB"
        )
        return memories

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini."""
        try:
            # Use Gemini for embeddings (works for all vector databases)
            response = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document",
            )
            logger.debug(f"Generated embedding for text of length {len(text)}")
            return response["embedding"]

        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {str(e)}")
            raise
