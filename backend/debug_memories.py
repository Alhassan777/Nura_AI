#!/usr/bin/env python3
"""Debug script to check memory storage and retrieval"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.memory.storage.vector_store import VectorStore
from services.memory.config import Config


async def debug_memories():
    print("🔍 DEBUGGING MEMORY STORAGE & RETRIEVAL")
    print("=" * 50)

    config = Config()

    # Initialize vector store only
    vector_store = VectorStore(config)

    user_id = "5aad95e6-7170-411d-a983-3fba374309b3"

    print(f"Checking memories for user: {user_id}")
    print()

    # Check vector store (long-term memories)
    print("📚 VECTOR STORE (Long-term memories):")
    vector_memories = await vector_store.get_user_memories(user_id)
    print(f"Found {len(vector_memories)} memories in vector store")

    for i, memory in enumerate(vector_memories, 1):
        print(f"\n  Memory {i}:")
        print(f"    ID: {memory.get('memory_id', memory.get('id', 'NO_ID'))}")
        print(f"    Content: {memory.get('content', 'NO_CONTENT')[:100]}...")
        metadata = memory.get("metadata", {})
        memory_category = metadata.get("memory_category", "NO_CATEGORY")
        print(f"    Category: {memory_category}")
        print(f"    Storage Type: {metadata.get('storage_type', 'NO_STORAGE_TYPE')}")
        print(f"    Is Meaningful: {metadata.get('is_meaningful', 'NO_FLAG')}")
        print(f"    Is Lasting: {metadata.get('is_lasting', 'NO_FLAG')}")
        print(f"    Is Symbolic: {metadata.get('is_symbolic', 'NO_FLAG')}")

    print(f"\n🔍 FILTERING TEST:")
    print(
        "Checking which memories would be returned as 'regular memories' (long_term category):"
    )

    regular_count = 0
    emotional_anchor_count = 0
    other_count = 0

    for memory in vector_memories:
        category = memory.get("metadata", {}).get("memory_category", "short_term")
        if category == "long_term":
            regular_count += 1
            print(f"  ✅ REGULAR: {memory.get('content', '')[:50]}...")
        elif category == "emotional_anchor":
            emotional_anchor_count += 1
            print(f"  💝 ANCHOR: {memory.get('content', '')[:50]}...")
        else:
            other_count += 1
            print(f"  ❓ OTHER ({category}): {memory.get('content', '')[:50]}...")

    print(f"\n📊 SUMMARY:")
    print(f"  Regular memories (long_term): {regular_count}")
    print(f"  Emotional anchors: {emotional_anchor_count}")
    print(f"  Other categories: {other_count}")
    print(f"  Total in vector store: {len(vector_memories)}")


if __name__ == "__main__":
    asyncio.run(debug_memories())
