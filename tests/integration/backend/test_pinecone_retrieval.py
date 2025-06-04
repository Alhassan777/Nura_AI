"""
Test script to verify Pinecone vector database retrieval functionality.
This test validates that our embedding model consistency fixes are working properly.
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

from services.memory.storage.vector_store import VectorStore
from services.memory.types import MemoryItem


class PineconeRetrievalTest:
    """Test class to validate Pinecone retrieval functionality."""

    def __init__(self):
        # Initialize VectorStore with Pinecone configuration
        self.vector_store = VectorStore(vector_db_type="pinecone", use_pinecone=True)

        self.test_user_id = "test_user_pinecone_retrieval"

    async def setup_test_data(self):
        """Add test memories to Pinecone for retrieval testing."""
        print("🔧 Setting up test data in Pinecone...")

        # Create diverse test memories
        test_memories = [
            {
                "content": "I feel very anxious about my upcoming job interview tomorrow. My heart is racing and I can't sleep.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "emotional_state",
                    "emotion": "anxiety",
                    "topic": "job_interview",
                },
            },
            {
                "content": "I love spending time in my grandmother's garden with the beautiful roses and lavender. It always makes me feel peaceful.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "meaningful_connection",
                    "emotion": "peaceful",
                    "topic": "family_memory",
                },
            },
            {
                "content": "Had a terrible fight with my partner today about money. I'm feeling really frustrated and sad.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "emotional_state",
                    "emotion": "frustrated",
                    "topic": "relationship",
                },
            },
            {
                "content": "Went for a morning run by the lake. The sunrise was absolutely breathtaking and I felt so alive and energized.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "positive_experience",
                    "emotion": "energized",
                    "topic": "exercise",
                },
            },
            {
                "content": "My therapist suggested I try meditation when I feel overwhelmed. I should practice breathing exercises.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "coping_strategy",
                    "emotion": "neutral",
                    "topic": "therapy_advice",
                },
            },
            {
                "content": "I keep thinking about my childhood home and how safe I felt there. Missing those simple times.",
                "type": "user_message",
                "metadata": {
                    "memory_type": "nostalgic_memory",
                    "emotion": "nostalgic",
                    "topic": "childhood",
                },
            },
        ]

        # Add memories to Pinecone
        for i, memory_data in enumerate(test_memories):
            memory_item = MemoryItem(
                id=f"test_memory_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                userId=self.test_user_id,
                content=memory_data["content"],
                type=memory_data["type"],
                metadata=memory_data["metadata"],
                timestamp=datetime.utcnow(),
            )

            await self.vector_store.add_memory(self.test_user_id, memory_item)
            print(f"✅ Added memory: {memory_data['content'][:50]}...")

        print(f"📊 Added {len(test_memories)} test memories to Pinecone")

    async def test_similarity_search(
        self, query: str, expected_topics: List[str] = None
    ) -> Dict[str, Any]:
        """Test similarity search and analyze results."""
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 60)

        # Perform similarity search
        results = await self.vector_store.get_similar_memories(
            user_id=self.test_user_id, query=query, limit=3
        )

        print(f"📊 Found {len(results)} similar memories:")

        # Analyze and display results
        for i, memory in enumerate(results, 1):
            print(f"\n{i}. Memory ID: {memory.id}")
            print(f"   Content: {memory.content}")
            print(f"   Type: {memory.type}")
            print(f"   Emotion: {memory.metadata.get('emotion', 'N/A')}")
            print(f"   Topic: {memory.metadata.get('topic', 'N/A')}")
            print(f"   Memory Type: {memory.metadata.get('memory_type', 'N/A')}")

        # Check if expected topics were found
        found_topics = [m.metadata.get("topic", "") for m in results]
        found_emotions = [m.metadata.get("emotion", "") for m in results]

        analysis = {
            "query": query,
            "results_count": len(results),
            "found_topics": found_topics,
            "found_emotions": found_emotions,
            "memories": [
                {
                    "content": m.content,
                    "emotion": m.metadata.get("emotion"),
                    "topic": m.metadata.get("topic"),
                    "memory_type": m.metadata.get("memory_type"),
                }
                for m in results
            ],
        }

        if expected_topics:
            matches = any(topic in found_topics for topic in expected_topics)
            print(f"\n✅ Expected topics {expected_topics} found: {matches}")
            analysis["expected_match"] = matches

        return analysis

    async def test_emotional_queries(self):
        """Test various emotional and contextual queries."""
        print("\n" + "🧠" * 20)
        print("EMOTIONAL QUERY TESTING")
        print("🧠" * 20)

        test_queries = [
            {
                "query": "I'm feeling very anxious and stressed",
                "expected_topics": ["job_interview", "therapy_advice"],
                "description": "Should find anxiety-related memories and coping strategies",
            },
            {
                "query": "I want to feel peaceful and calm",
                "expected_topics": ["family_memory", "therapy_advice"],
                "description": "Should find peaceful memories and calming strategies",
            },
            {
                "query": "Tell me about beautiful outdoor experiences",
                "expected_topics": ["exercise", "family_memory"],
                "description": "Should find nature and outdoor memories",
            },
            {
                "query": "I'm having relationship problems",
                "expected_topics": ["relationship"],
                "description": "Should find relationship-related memories",
            },
            {
                "query": "I miss my childhood and family",
                "expected_topics": ["childhood", "family_memory"],
                "description": "Should find nostalgic and family memories",
            },
        ]

        all_results = []

        for test_case in test_queries:
            print(f"\n📝 Test Case: {test_case['description']}")
            result = await self.test_similarity_search(
                test_case["query"], test_case["expected_topics"]
            )
            all_results.append(result)

        return all_results

    async def test_embedding_consistency(self):
        """Test that embeddings are being generated consistently."""
        print("\n" + "🔬" * 20)
        print("EMBEDDING CONSISTENCY TEST")
        print("🔬" * 20)

        test_text = "I feel anxious about my future"

        # Generate embedding directly
        embedding1 = await self.vector_store._get_embedding(test_text)
        embedding2 = await self.vector_store._get_embedding(test_text)

        print(f"📊 Embedding dimensions: {len(embedding1)}")
        print(f"🔄 Consistency check: {len(embedding1) == len(embedding2)}")
        print(f"🎯 Expected dimension: {self.vector_store.embedding_dimension}")

        # Check if embeddings are consistent
        if embedding1 == embedding2:
            print("✅ Embeddings are perfectly consistent")
        else:
            # Check similarity (they might have small numerical differences)
            import numpy as np

            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            print(f"📈 Embedding similarity: {similarity:.4f}")

        return {
            "embedding_dimension": len(embedding1),
            "expected_dimension": self.vector_store.embedding_dimension,
            "consistency": embedding1 == embedding2,
        }

    async def cleanup_test_data(self):
        """Clean up test data from Pinecone."""
        print("\n🧹 Cleaning up test data...")
        try:
            await self.vector_store.clear_memories(self.test_user_id)
            print("✅ Test data cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test data: {e}")

    async def run_complete_test(self):
        """Run the complete Pinecone retrieval test suite."""
        print("\n" + "🚀" * 30)
        print("PINECONE VECTOR DATABASE RETRIEVAL TEST")
        print("🚀" * 30)

        try:
            # Setup test data
            await self.setup_test_data()

            # Wait a moment for Pinecone to index
            print("\n⏳ Waiting for Pinecone to index data...")
            await asyncio.sleep(10)

            # Test embedding consistency
            embedding_results = await self.test_embedding_consistency()

            # Test emotional queries
            query_results = await self.test_emotional_queries()

            # Summary
            print("\n" + "📋" * 20)
            print("TEST SUMMARY")
            print("📋" * 20)

            print(
                f"🔧 Embedding Model: {'NVIDIA llama-text-embed-v2' if self.vector_store.use_pinecone else 'Gemini'}"
            )
            print(f"📏 Embedding Dimension: {embedding_results['embedding_dimension']}")
            print(
                f"✅ Dimension Consistency: {embedding_results['embedding_dimension'] == embedding_results['expected_dimension']}"
            )

            successful_queries = sum(
                1 for r in query_results if r.get("expected_match", False)
            )
            print(
                f"🎯 Successful Query Matches: {successful_queries}/{len(query_results)}"
            )

            for result in query_results:
                match_status = "✅" if result.get("expected_match", False) else "❌"
                print(
                    f"   {match_status} '{result['query'][:40]}...' - Found {result['results_count']} results"
                )

            return {
                "embedding_results": embedding_results,
                "query_results": query_results,
                "test_success": successful_queries
                > len(query_results) * 0.6,  # 60% success rate
            }

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback

            traceback.print_exc()
            return {"test_success": False, "error": str(e)}

        finally:
            # Always try to clean up
            await self.cleanup_test_data()


# Standalone execution
async def main():
    """Run the Pinecone retrieval test."""
    test = PineconeRetrievalTest()
    results = await test.run_complete_test()

    if results.get("test_success"):
        print("\n🎉 PINECONE RETRIEVAL TEST PASSED!")
    else:
        print("\n💥 PINECONE RETRIEVAL TEST FAILED!")

    return results


if __name__ == "__main__":
    asyncio.run(main())
