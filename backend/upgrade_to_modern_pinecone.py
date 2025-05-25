#!/usr/bin/env python3
"""
Upgrade Nura to Modern Pinecone Features

This script demonstrates how to use the latest Pinecone features:
1. Integrated embedding models
2. Reranking for better search results
3. Simplified API usage
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

try:
    from pinecone import Pinecone

    def test_modern_pinecone():
        """Test modern Pinecone features."""
        print("🚀 Testing Modern Pinecone Features...")
        print("=" * 50)

        # Get API key
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("❌ PINECONE_API_KEY not found")
            return

        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)

        # Modern index creation with integrated embeddings
        index_name = "nura-modern-test"

        print("1️⃣ Creating modern index with integrated embeddings...")

        # Check if index exists
        if pc.has_index(index_name):
            print(f"   Index {index_name} already exists, deleting...")
            pc.delete_index(index_name)
            import time

            time.sleep(5)  # Wait for deletion

        # Create index with integrated embedding model
        try:
            pc.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",  # Pinecone's integrated model
                    "field_map": {"text": "content"},  # Map our content field
                },
            )
            print(f"✅ Created modern index: {index_name}")
        except Exception as e:
            print(f"❌ Failed to create modern index: {str(e)}")
            print(
                "   This might be because your account doesn't have access to integrated models yet"
            )
            return

        # Get the index
        index = pc.Index(index_name)

        print("\n2️⃣ Adding mental health memories with automatic embeddings...")

        # Sample mental health memories
        mental_health_records = [
            {
                "_id": "mem1",
                "content": "I feel anxious about my upcoming presentation at work. I keep worrying about what people will think.",
                "category": "anxiety",
                "emotion": "worried",
            },
            {
                "_id": "mem2",
                "content": "Had a great therapy session today. We talked about coping strategies for stress.",
                "category": "therapy",
                "emotion": "positive",
            },
            {
                "_id": "mem3",
                "content": "My sleep has been terrible lately. I keep waking up at 3 AM with racing thoughts.",
                "category": "sleep",
                "emotion": "stressed",
            },
            {
                "_id": "mem4",
                "content": "Practiced mindfulness meditation for 10 minutes. Felt more centered afterwards.",
                "category": "mindfulness",
                "emotion": "calm",
            },
            {
                "_id": "mem5",
                "content": "Work deadline is causing me a lot of stress. Feel overwhelmed with everything.",
                "category": "work_stress",
                "emotion": "overwhelmed",
            },
        ]

        # Upsert records (Pinecone handles embeddings automatically)
        try:
            index.upsert_records("mental-health", mental_health_records)
            print("✅ Added mental health memories with automatic embeddings")

            # Wait for indexing
            import time

            time.sleep(10)

            # Check stats
            stats = index.describe_index_stats()
            print(f"   Vector count: {stats.get('total_vector_count', 0)}")

        except Exception as e:
            print(f"❌ Failed to upsert records: {str(e)}")
            return

        print("\n3️⃣ Testing semantic search...")

        # Search without reranking
        query = "I'm feeling stressed about work"
        try:
            results = index.search(
                namespace="mental-health", query={"top_k": 3, "inputs": {"text": query}}
            )

            print(f"   Query: '{query}'")
            print("   Results without reranking:")
            for hit in results["result"]["hits"]:
                print(
                    f"     Score: {hit['_score']:.3f} | {hit['fields']['content'][:60]}..."
                )

        except Exception as e:
            print(f"❌ Search failed: {str(e)}")

        print("\n4️⃣ Testing search with reranking...")

        # Search with reranking for better accuracy
        try:
            reranked_results = index.search(
                namespace="mental-health",
                query={"top_k": 3, "inputs": {"text": query}},
                rerank={
                    "model": "bge-reranker-v2-m3",
                    "top_n": 3,
                    "rank_fields": ["content"],
                },
            )

            print("   Results with reranking:")
            for hit in reranked_results["result"]["hits"]:
                print(
                    f"     Score: {hit['_score']:.3f} | {hit['fields']['content'][:60]}..."
                )

        except Exception as e:
            print(f"❌ Reranking failed: {str(e)}")
            print("   This might not be available on your plan yet")

        print("\n5️⃣ Testing metadata filtering...")

        # Search with metadata filter
        try:
            filtered_results = index.search(
                namespace="mental-health",
                query={"top_k": 5, "inputs": {"text": "anxiety stress"}},
                filter={"category": {"$in": ["anxiety", "work_stress"]}},
            )

            print("   Filtered results (anxiety + work_stress only):")
            for hit in filtered_results["result"]["hits"]:
                print(
                    f"     Category: {hit['fields']['category']} | {hit['fields']['content'][:50]}..."
                )

        except Exception as e:
            print(f"❌ Filtering failed: {str(e)}")

        print("\n6️⃣ Cleaning up test index...")
        try:
            pc.delete_index(index_name)
            print("✅ Deleted test index")
        except Exception as e:
            print(f"❌ Failed to delete index: {str(e)}")

        print("\n🎉 Modern Pinecone features test completed!")
        print("\n💡 Key Benefits:")
        print("   ✅ No need to manage embeddings yourself")
        print("   ✅ Better search accuracy with reranking")
        print("   ✅ Simplified API - just send text")
        print("   ✅ Advanced filtering capabilities")

except ImportError:
    print("❌ Pinecone not installed. Run: pip install pinecone")
except Exception as e:
    print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_modern_pinecone()
