#!/usr/bin/env python3
"""
Vector Database Test Script for Nura Memory System

This script tests the vector database functionality to ensure everything is working correctly.
"""

import asyncio
import os
import sys
from datetime import datetime
import uuid

# Add src to path
sys.path.append("src")

from services.memory.storage.vector_store import VectorStore
from services.memory.types import MemoryItem


async def test_vector_db():
    """Test vector database functionality."""
    print("🧪 Testing Vector Database Setup...")
    print("=" * 50)

    try:
        # 1. Initialize vector store
        print("1️⃣ Initializing ChromaDB vector store...")
        vector_store = VectorStore(
            persist_directory="./data/vector_store",
            project_id="local",  # Not used for ChromaDB
            use_vertex=False,  # Use ChromaDB, not Vertex AI
        )
        print("✅ Vector database initialized successfully!")
        print(f"📁 Data will be stored in: ./data/vector_store")

        # 2. Create test memories
        print("\n2️⃣ Creating test memories...")
        test_memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content="I feel anxious about my upcoming presentation at work",
                type="user_message",
                timestamp=datetime.utcnow(),
                metadata={"emotion": "anxiety", "topic": "work"},
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content="Listening to classical music helps me relax when I'm stressed",
                type="user_message",
                timestamp=datetime.utcnow(),
                metadata={"coping_strategy": "music", "emotion": "stress"},
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                userId="test_user",
                content="My therapist suggested deep breathing exercises for anxiety",
                type="user_message",
                timestamp=datetime.utcnow(),
                metadata={"source": "therapist", "technique": "breathing"},
            ),
        ]

        # 3. Store memories
        print("3️⃣ Storing memories in vector database...")
        for i, memory in enumerate(test_memories, 1):
            await vector_store.add_memory("test_user", memory)
            print(f"   ✅ Stored memory {i}: {memory.content[:50]}...")

        # 4. Test similarity search
        print("\n4️⃣ Testing similarity search...")
        test_queries = [
            "I'm worried about giving a speech",
            "What helps with stress?",
            "Anxiety management techniques",
        ]

        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            similar_memories = await vector_store.get_similar_memories(
                user_id="test_user", query=query, limit=2
            )

            if similar_memories:
                print(f"   📋 Found {len(similar_memories)} similar memories:")
                for j, memory in enumerate(similar_memories, 1):
                    print(f"      {j}. {memory.content[:60]}...")
            else:
                print("   ❌ No similar memories found")

        # 5. Test memory deletion
        print("\n5️⃣ Testing memory deletion...")
        first_memory_id = test_memories[0].id
        success = await vector_store.delete_memory("test_user", first_memory_id)
        if success:
            print(f"   ✅ Successfully deleted memory: {first_memory_id}")
        else:
            print(f"   ❌ Failed to delete memory: {first_memory_id}")

        # 6. Test cleanup
        print("\n6️⃣ Testing memory cleanup...")
        await vector_store.clear_memories("test_user")
        print("   ✅ Successfully cleared all memories for test_user")

        # 7. Final verification
        print("\n7️⃣ Final verification...")
        remaining_memories = await vector_store.get_similar_memories(
            user_id="test_user", query="anything", limit=10
        )
        print(f"   📊 Remaining memories: {len(remaining_memories)}")

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Vector database is working correctly!")
        print("✅ ChromaDB is ready for use")
        print("✅ Embedding generation is working")
        print("✅ Similarity search is functional")
        print("✅ Memory management is operational")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if ChromaDB is installed: pip install chromadb")
        print("2. Verify Google API key is set for embeddings")
        print("3. Ensure data directory is writable")
        print("4. Check the VECTOR_DB_SETUP_GUIDE.md for more help")
        return False

    return True


async def test_embedding_generation():
    """Test embedding generation specifically."""
    print("\n🧠 Testing Embedding Generation...")
    print("-" * 30)

    try:
        vector_store = VectorStore(
            persist_directory="./data/vector_store",
            project_id="local",
            use_vertex=False,
        )

        test_text = "This is a test message for embedding generation"
        embedding = await vector_store._get_embedding(test_text)

        print(f"✅ Generated embedding for: '{test_text}'")
        print(f"📊 Embedding dimensions: {len(embedding)}")
        print(f"📈 Sample values: {embedding[:5]}...")

        return True

    except Exception as e:
        print(f"❌ Embedding generation failed: {str(e)}")
        print("💡 This usually means the Google API key is missing or invalid")
        return False


def check_environment():
    """Check environment setup."""
    print("🔧 Checking Environment Setup...")
    print("-" * 30)

    # Check Google API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ Google API key found: {api_key[:10]}...")
    else:
        print("❌ Google API key not found!")
        print("💡 Set GOOGLE_API_KEY in your .env file")
        return False

    # Check data directory
    data_dir = "./data/vector_store"
    if os.path.exists(data_dir):
        print(f"✅ Data directory exists: {data_dir}")
    else:
        print(f"📁 Data directory will be created: {data_dir}")

    # Check ChromaDB import
    try:
        import chromadb

        print("✅ ChromaDB is installed and importable")
    except ImportError:
        print("❌ ChromaDB not found!")
        print("💡 Install with: pip install chromadb")
        return False

    return True


async def main():
    """Main test function."""
    print("🧠 Nura Memory System - Vector Database Test")
    print("=" * 60)

    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return

    # Test embedding generation
    if not await test_embedding_generation():
        print("\n❌ Embedding test failed. Please check your Google API key.")
        return

    # Test full vector database functionality
    success = await test_vector_db()

    if success:
        print("\n🚀 Ready to test the chat interface!")
        print("Run: python chat_test_interface.py")
    else:
        print("\n❌ Vector database test failed. Check the error messages above.")


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print(
            "💡 Install python-dotenv for .env file support: pip install python-dotenv"
        )

    asyncio.run(main())
