#!/usr/bin/env python3
"""
Test script for the new vector database API endpoints.
This allows you to directly test vector database operations without going through the full chat flow.
"""

import asyncio
import aiohttp
import json


async def test_vector_api():
    """Test the vector database API endpoints directly."""

    base_url = "http://localhost:8000"
    user_id = "vector-test-user"

    print(f"🧪 Testing Vector Database API Endpoints")
    print(f"Base URL: {base_url}")
    print(f"User ID: {user_id}")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:

        # Test 1: Clear vector store first
        print("\n1️⃣ Clearing vector store...")
        try:
            async with session.delete(f"{base_url}/vector/clear/{user_id}") as response:
                result = await response.json()
                print(f"✅ {result['message']}")
        except Exception as e:
            print(f"❌ Clear failed: {e}")
            return

        # Test 2: Check initial count (should be 0)
        print("\n2️⃣ Checking initial count...")
        try:
            async with session.get(f"{base_url}/vector/count/{user_id}") as response:
                result = await response.json()
                print(f"📊 Count: {result['count']} memories")
        except Exception as e:
            print(f"❌ Count check failed: {e}")
            return

        # Test 3: Add significant memories directly to vector store
        print("\n3️⃣ Adding memories to vector store...")
        test_memories = [
            "I met the love of my life in the chat and she was my crush for years",
            "I got into Harvard today, my dream college",
            "I realized I get anxious when my mom calls because she criticizes me",
            "I had coffee this morning and it was good",
        ]

        for i, memory in enumerate(test_memories):
            try:
                data = {"user_id": user_id, "content": memory, "type": "test_memory"}
                async with session.post(
                    f"{base_url}/vector/add", json=data
                ) as response:
                    result = await response.json()
                    print(
                        f"  ✅ Memory {i+1}: {result['memory_id'][:8]}... - '{memory[:50]}...'"
                    )
            except Exception as e:
                print(f"  ❌ Memory {i+1} failed: {e}")

        # Test 4: Check count after adding
        print("\n4️⃣ Checking count after adding...")
        try:
            async with session.get(f"{base_url}/vector/count/{user_id}") as response:
                result = await response.json()
                print(f"📊 Count: {result['count']} memories")
        except Exception as e:
            print(f"❌ Count check failed: {e}")

        # Test 5: Query vector store with different queries
        print("\n5️⃣ Testing vector store queries...")
        test_queries = [
            "love relationship",
            "college education",
            "anxiety feelings",
            "coffee morning",
        ]

        for query in test_queries:
            try:
                params = {"query": query, "limit": 3}
                async with session.get(
                    f"{base_url}/vector/query/{user_id}", params=params
                ) as response:
                    result = await response.json()
                    print(f"\n🔍 Query: '{query}'")
                    print(f"   Results: {result['results_count']} memories found")
                    for memory in result["memories"]:
                        print(f"   - {memory['content'][:60]}...")
            except Exception as e:
                print(f"❌ Query '{query}' failed: {e}")

        # Test 6: Test Redis endpoints too
        print("\n6️⃣ Testing Redis endpoints...")

        # Add to Redis
        try:
            data = {
                "user_id": user_id,
                "content": "This is a Redis test message",
                "type": "redis_test",
            }
            async with session.post(f"{base_url}/redis/add", json=data) as response:
                result = await response.json()
                print(f"✅ Added to Redis: {result['memory_id'][:8]}...")
        except Exception as e:
            print(f"❌ Redis add failed: {e}")

        # Get from Redis
        try:
            async with session.get(f"{base_url}/redis/get/{user_id}") as response:
                result = await response.json()
                print(f"📊 Redis memories: {result['total_count']} total")
                for memory in result["memories"][:2]:  # Show first 2
                    print(f"   - {memory['content'][:60]}...")
        except Exception as e:
            print(f"❌ Redis get failed: {e}")

    print("\n" + "=" * 50)
    print("🎉 Vector API testing completed!")
    print("\n💡 You can now use these endpoints to:")
    print("   • POST /vector/add - Add memories directly to vector store")
    print("   • GET /vector/query/{user_id}?query=... - Search vector store")
    print("   • GET /vector/count/{user_id} - Get memory count")
    print("   • DELETE /vector/clear/{user_id} - Clear all memories")
    print("   • Similar endpoints for Redis: /redis/add, /redis/get, /redis/clear")


async def test_with_curl_examples():
    """Print curl examples for manual testing."""
    user_id = "test-user"
    base_url = "http://localhost:8000"

    print("\n🔧 CURL Examples for Manual Testing:")
    print("=" * 50)

    print("\n# Add memory to vector store:")
    print(
        f"""curl -X POST {base_url}/vector/add \\
  -H "Content-Type: application/json" \\
  -d '{{"user_id": "{user_id}", "content": "I met the love of my life today", "type": "test"}}'"""
    )

    print("\n# Query vector store:")
    print(
        f"""curl "{base_url}/vector/query/{user_id}?query=love%20relationship&limit=5" """
    )

    print("\n# Get vector store count:")
    print(f"""curl "{base_url}/vector/count/{user_id}" """)

    print("\n# Clear vector store:")
    print(f"""curl -X DELETE "{base_url}/vector/clear/{user_id}" """)

    print("\n# Add to Redis:")
    print(
        f"""curl -X POST {base_url}/redis/add \\
  -H "Content-Type: application/json" \\
  -d '{{"user_id": "{user_id}", "content": "Redis test message", "type": "test"}}'"""
    )

    print("\n# Get from Redis:")
    print(f"""curl "{base_url}/redis/get/{user_id}?limit=10" """)


if __name__ == "__main__":
    print("🚀 Vector Database API Tester")
    print("Make sure the chat interface is running: python chat_test_interface.py")
    print()

    # Run the async test
    asyncio.run(test_vector_api())

    # Show curl examples
    test_with_curl_examples()
