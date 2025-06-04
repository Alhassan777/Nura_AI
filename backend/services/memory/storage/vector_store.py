"""
Vector Storage Layer for Long-term Memory Management.

Handles persistent storage of processed memory items using vector databases
for semantic search and long-term retention.
"""

import os
import json
import logging
import sys
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings
import uuid
from dataclasses import asdict
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

# Import authentication systems - SIMPLIFIED for session-based auth
from ..types import MemoryItem
from ..config import Config

# Set up logging
logger = logging.getLogger(__name__)


class VectorStore:
    """
    SIMPLIFIED Vector Store for secure long-term memory storage.
    All operations are secure by default since user_id comes from validated JWT.
    """

    def __init__(
        self,
        persist_directory: str = None,
        use_pinecone: bool = False,
        vector_db_type: str = "chroma",
    ):
        # Determine which vector database to use
        self.vector_db_type = vector_db_type.lower()
        self.use_pinecone = use_pinecone or (self.vector_db_type == "pinecone")
        self.persist_directory = persist_directory or "chroma"

        # Initialize storage system
        self.client = None
        self.collection = None
        self.pinecone_client = None
        self.pinecone_index = None

        logger.info(f"Initialized VectorStore with {self.vector_db_type} backend")

    def _get_user_namespace(self, user_id: str) -> str:
        """Get user-specific namespace for vector isolation."""
        return f"user_{user_id}"

    def _get_user_metadata_filter(self, user_id: str) -> Dict[str, Any]:
        """Get metadata filter to ensure user data isolation."""
        return {"user_id": user_id}

    async def initialize(self):
        """Initialize the vector database connection."""
        try:
            if self.use_pinecone and PINECONE_AVAILABLE:
                await self._initialize_pinecone()
            else:
                await self._initialize_chroma()

            logger.info(
                f"Vector store initialized successfully with {self.vector_db_type}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    async def _initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            api_key = Config.PINECONE_API_KEY
            if not api_key:
                raise ValueError("PINECONE_API_KEY not configured")

            from pinecone import Pinecone, ServerlessSpec

            self.pinecone_client = Pinecone(api_key=api_key)

            # Create or get index
            index_name = Config.PINECONE_INDEX_NAME or "nura-memories"

            try:
                # Try to get existing index
                self.pinecone_index = self.pinecone_client.Index(index_name)
                logger.info(f"Connected to existing Pinecone index: {index_name}")

            except Exception:
                # Create new index if it doesn't exist
                logger.info(f"Creating new Pinecone index: {index_name}")
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=768,  # For text embedding models
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                self.pinecone_index = self.pinecone_client.Index(index_name)

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    async def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # Get or create collection
            collection_name = "nura_memories"
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(
                    f"Connected to existing ChromaDB collection: {collection_name}"
                )
            except Exception:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Nura user memories with user isolation"},
                )
                logger.info(f"Created new ChromaDB collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using Google AI."""
        try:
            if not Config.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not configured for embeddings")

            genai.configure(api_key=Config.GOOGLE_API_KEY)

            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document",
                )
                embeddings.append(result["embedding"])

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def store_memory(self, user_id: str, memory: MemoryItem) -> bool:
        """
        Store a memory with user isolation.

        Args:
            user_id: Validated user ID from JWT
            memory: Memory to store

        Returns:
            Success status
        """
        try:
            if not self.client and not self.pinecone_index:
                await self.initialize()

            # Generate embedding
            embeddings = await self._get_embeddings([memory.content])
            embedding = embeddings[0]

            # Create metadata with user ownership
            metadata = {
                **memory.metadata,
                "user_id": user_id,
                "memory_id": memory.id,
                "type": memory.type,
                "timestamp": memory.timestamp.isoformat(),
                "content_preview": memory.content[:100],
            }

            if self.use_pinecone and self.pinecone_index:
                # Store in Pinecone with user namespace
                vector_data = {
                    "id": f"{user_id}_{memory.id}",
                    "values": embedding,
                    "metadata": metadata,
                }

                namespace = self._get_user_namespace(user_id)
                self.pinecone_index.upsert(vectors=[vector_data], namespace=namespace)

            else:
                # Store in ChromaDB with user metadata filter
                self.collection.add(
                    ids=[f"{user_id}_{memory.id}"],
                    embeddings=[embedding],
                    documents=[memory.content],
                    metadatas=[metadata],
                )

            logger.debug(f"Stored memory {memory.id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store memory for user {user_id}: {e}")
            return False

    async def similarity_search(
        self, query: str, user_id: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user's memories by similarity.

        Args:
            query: Search query
            user_id: Validated user ID from JWT
            k: Number of results

        Returns:
            List of similar memories with scores
        """
        try:
            if not self.client and not self.pinecone_index:
                await self.initialize()

            # Generate query embedding
            query_embeddings = await self._get_embeddings([query])
            query_embedding = query_embeddings[0]

            results = []

            if self.use_pinecone and self.pinecone_index:
                # Search in user's Pinecone namespace
                namespace = self._get_user_namespace(user_id)

                search_results = self.pinecone_index.query(
                    vector=query_embedding,
                    top_k=k,
                    namespace=namespace,
                    include_metadata=True,
                )

                for match in search_results.matches:
                    results.append(
                        {
                            "content": match.metadata.get("content_preview", ""),
                            "score": float(match.score),
                            "metadata": match.metadata,
                            "memory_id": match.metadata.get("memory_id"),
                        }
                    )

            else:
                # Search in ChromaDB with user filter
                search_results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where=self._get_user_metadata_filter(user_id),
                )

                if search_results["documents"]:
                    for i, doc in enumerate(search_results["documents"][0]):
                        metadata = search_results["metadatas"][0][i]
                        distance = search_results["distances"][0][i]

                        # Convert distance to similarity score (higher = more similar)
                        score = 1.0 - distance

                        results.append(
                            {
                                "content": doc,
                                "score": score,
                                "metadata": metadata,
                                "memory_id": metadata.get("memory_id"),
                            }
                        )

            # Sort by score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)

            logger.debug(f"Found {len(results)} similar memories for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to search memories for user {user_id}: {e}")
            return []

    async def get_user_memories(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get memories for a specific user with proper isolation.

        Args:
            user_id: Validated user ID from JWT
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory dictionaries
        """
        try:
            if not self.client and not self.pinecone_index:
                await self.initialize()

            if self.use_pinecone:
                return await self._get_pinecone_memories(user_id, limit)
            else:
                return await self._get_chroma_memories(user_id, limit)

        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {e}")
            return []

    async def _get_pinecone_memories(
        self, user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get memories from Pinecone for a specific user."""
        memories = []
        namespace = self._get_user_namespace(user_id)

        try:
            # Get stats first to see if namespace exists
            stats = self.pinecone_index.describe_index_stats()

            if namespace in stats.namespaces:
                # Use a broad query to get user's memories
                # This is not ideal but Pinecone doesn't have direct "list all" functionality
                dummy_embedding = [0.1] * 768  # Small non-zero values

                results = self.pinecone_index.query(
                    vector=dummy_embedding,
                    top_k=min(limit, 1000),  # Cap at reasonable limit
                    namespace=namespace,
                    include_metadata=True,
                    include_values=False,
                )

                for match in results.matches:
                    memories.append(
                        {
                            "memory_id": match.metadata.get("memory_id"),
                            "content": match.metadata.get("content_preview", ""),
                            "metadata": match.metadata,
                            "timestamp": match.metadata.get("timestamp"),
                        }
                    )
        except Exception as e:
            logger.warning(
                f"Could not retrieve memories from Pinecone namespace {namespace}: {e}"
            )

        return memories

    async def _get_chroma_memories(
        self, user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get memories from ChromaDB for a specific user."""
        memories = []

        try:
            results = self.collection.get(
                where=self._get_user_metadata_filter(user_id), limit=limit
            )

            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    metadata = results["metadatas"][i]
                    memories.append(
                        {
                            "memory_id": metadata.get("memory_id"),
                            "content": doc,
                            "metadata": metadata,
                            "timestamp": metadata.get("timestamp"),
                        }
                    )
        except Exception as e:
            logger.warning(
                f"Could not retrieve memories from ChromaDB for user {user_id}: {e}"
            )

        return memories

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a specific memory for a user.

        Args:
            user_id: Validated user ID from JWT
            memory_id: Memory ID to delete

        Returns:
            Success status
        """
        try:
            if not self.client and not self.pinecone_index:
                await self.initialize()

            vector_id = f"{user_id}_{memory_id}"

            if self.use_pinecone and self.pinecone_index:
                # Delete from user's Pinecone namespace
                namespace = self._get_user_namespace(user_id)
                self.pinecone_index.delete(ids=[vector_id], namespace=namespace)

            else:
                # Delete from ChromaDB
                self.collection.delete(ids=[vector_id])

            logger.debug(f"Deleted memory {memory_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id} for user {user_id}: {e}")
            return False

    async def clear_user_memories(self, user_id: str) -> bool:
        """
        Clear all memories for a specific user.

        Args:
            user_id: Validated user ID from JWT

        Returns:
            Success status
        """
        try:
            if not self.client and not self.pinecone_index:
                await self.initialize()

            if self.use_pinecone and self.pinecone_index:
                # Delete entire user namespace
                namespace = self._get_user_namespace(user_id)
                self.pinecone_index.delete(delete_all=True, namespace=namespace)

            else:
                # Delete all user memories from ChromaDB
                self.collection.delete(where=self._get_user_metadata_filter(user_id))

            logger.info(f"Cleared all memories for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear memories for user {user_id}: {e}")
            return False

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get vector storage statistics for a user.

        Args:
            user_id: Validated user ID from JWT

        Returns:
            User's vector storage statistics
        """
        try:
            memories = await self.get_user_memories(user_id)

            return {
                "vector_count": len(memories),
                "storage_type": self.vector_db_type,
                "index_name": (
                    Config.PINECONE_INDEX_NAME
                    if self.use_pinecone
                    else "chroma_collection"
                ),
                "user_namespace": self._get_user_namespace(user_id),
                "embedding_model": "google-embedding-001",
            }

        except Exception as e:
            logger.error(f"Failed to get vector stats for user {user_id}: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check vector database health.

        Returns:
            Health status information
        """
        try:
            if not self.client and not self.pinecone_index:
                return {"status": "not_initialized", "available": False}

            # Test basic operations
            if self.use_pinecone and self.pinecone_index:
                # Test Pinecone connection
                stats = self.pinecone_index.describe_index_stats()
                return {
                    "status": "healthy",
                    "available": True,
                    "backend": "pinecone",
                    "total_vectors": stats.total_vector_count,
                    "namespaces": len(stats.namespaces),
                }

            else:
                # Test ChromaDB connection
                collection_count = len(self.client.list_collections())
                return {
                    "status": "healthy",
                    "available": True,
                    "backend": "chroma",
                    "collections": collection_count,
                }

        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return {"status": "unhealthy", "available": False, "error": str(e)}


# Create global instance
vector_store = VectorStore()


# Convenience functions
async def get_vector_store() -> VectorStore:
    """Get initialized vector store instance."""
    if not vector_store.client and not vector_store.pinecone_index:
        await vector_store.initialize()
    return vector_store
