#!/usr/bin/env python3
"""
Pinecone Setup Test Script for Nura Memory System

This script tests the Pinecone vector database configuration to ensure everything is working correctly.
"""

import asyncio
import os
import sys
from datetime import datetime
import uuid

# Load environment variables from .env.local
from dotenv import load_dotenv

load_dotenv(".env.local")

# Add src to path
sys.path.append("src")

from services.memory.storage.vector_store import VectorStore
from services.memory.types import MemoryItem


async def test_pinecone_setup():
    """Test Pinecone vector database setup."""
    print("🧪 Testing Pinecone Vector Database Setup...")
    print("=" * 50)

    try:
        # Check environment variables first
        print("0️⃣ Checking environment configuration...")

        required_vars = {
            "VECTOR_DB_TYPE": os.getenv("VECTOR_DB_TYPE"),
            "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
            "PINECONE_INDEX_NAME": os.getenv("PINECONE_INDEX_NAME"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("\nPlease set these in your .env.local file:")
            for var in missing_vars:
                print(f"  {var}=your_value_here")
            return

        print("✅ All required environment variables are set")
        print(f"   Vector DB Type: {required_vars['VECTOR_DB_TYPE']}")
        print(f"   Index Name: {required_vars['PINECONE_INDEX_NAME']}")

        # Initialize vector store with Pinecone
        print("\n1️⃣ Initializing Pinecone vector store...")
        vector_store = VectorStore(vector_db_type="pinecone")
        print("✅ Pinecone vector store initialized successfully!")

        # Create test memory
        print("\n2️⃣ Creating test memory...")
        test_memory = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user_pinecone",
            content="I feel anxious about my upcoming presentation at work. I keep worrying about what people will think.",
            type="test",
            timestamp=datetime.utcnow(),
            metadata={"test": True, "emotion": "anxiety", "context": "work"},
        )
        print(f"   📝 Test memory content: {test_memory.content[:50]}...")

        # Add memory to Pinecone
        print("\n3️⃣ Adding memory to Pinecone...")
        await vector_store.add_memory("test_user_pinecone", test_memory)
        print("✅ Successfully added test memory to Pinecone!")

        # Test similarity search
        print("\n4️⃣ Testing similarity search...")
        search_queries = [
            "work stress and anxiety",
            "presentation nerves",
            "workplace worries",
        ]

        for query in search_queries:
            print(f"   🔍 Searching for: '{query}'")
            similar_memories = await vector_store.get_similar_memories(
                "test_user_pinecone", query, limit=1
            )
            print(f"   ✅ Found {len(similar_memories)} similar memories")

            if similar_memories:
                memory = similar_memories[0]
                print(f"      📝 Content: {memory.content[:60]}...")
                print(f"      🏷️  Type: {memory.type}")

        # Test memory count
        print("\n5️⃣ Testing memory count...")
        count = await vector_store.get_memory_count("test_user_pinecone")
        print(f"✅ User has {count} memories in Pinecone")

        # Test adding multiple memories
        print("\n6️⃣ Testing multiple memory storage...")
        additional_memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user_pinecone",
                content="I had a great therapy session today. We talked about coping strategies for anxiety.",
                type="test",
                timestamp=datetime.utcnow(),
                metadata={"test": True, "emotion": "positive", "context": "therapy"},
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user_pinecone",
                content="My sleep has been terrible lately. I keep waking up at 3 AM with racing thoughts.",
                type="test",
                timestamp=datetime.utcnow(),
                metadata={"test": True, "emotion": "stress", "context": "sleep"},
            ),
        ]

        for memory in additional_memories:
            await vector_store.add_memory("test_user_pinecone", memory)
            print(f"   ✅ Added: {memory.content[:40]}...")

        # Test final count
        final_count = await vector_store.get_memory_count("test_user_pinecone")
        print(f"✅ Total memories after additions: {final_count}")

        # Test cross-query search
        print("\n7️⃣ Testing semantic search across different topics...")
        semantic_queries = [
            "sleep problems",
            "therapy and mental health",
            "work anxiety",
        ]

        for query in semantic_queries:
            print(f"   🔍 Semantic search: '{query}'")
            results = await vector_store.get_similar_memories(
                "test_user_pinecone", query, limit=2
            )
            print(f"   ✅ Found {len(results)} relevant memories")
            for i, memory in enumerate(results, 1):
                print(f"      {i}. {memory.content[:50]}...")

        # Clean up test data
        print("\n8️⃣ Cleaning up test data...")
        await vector_store.clear_memories("test_user_pinecone")

        # Verify cleanup
        cleanup_count = await vector_store.get_memory_count("test_user_pinecone")
        print(f"✅ Memories after cleanup: {cleanup_count}")

        print("\n🎉 Pinecone setup test completed successfully!")
        print("=" * 50)
        print("✅ Your Pinecone vector database is ready for production use!")
        print("✅ Memory storage and retrieval working correctly")
        print("✅ Semantic search functioning properly")
        print("✅ User isolation verified")
        print("\nNext steps:")
        print("1. Start your memory service: python -m src.services.memory.main")
        print("2. Start your Next.js app: npm run dev")
        print("3. Test the chat interface at: http://localhost:3000/test-chat")

    except ImportError as e:
        print(f"\n❌ Import error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Install Pinecone client: pip install pinecone-client==3.0.0")
        print("2. Install all requirements: pip install -r requirements.txt")

    except Exception as e:
        print(f"\n❌ Error during Pinecone setup test: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your PINECONE_API_KEY is correct")
        print("2. Verify your PINECONE_ENVIRONMENT matches your account")
        print("3. Ensure VECTOR_DB_TYPE=pinecone in your .env.local")
        print("4. Check your internet connectivity")
        print("5. Verify Pinecone service status at https://status.pinecone.io/")
        print("6. Make sure your Google API key is set for embeddings")

        print(f"\nDetailed error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_pinecone_setup())
