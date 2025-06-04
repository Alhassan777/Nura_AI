#!/usr/bin/env python3
"""
Detailed Privacy and Data Isolation Test - Shows actual data flow

This version prints out the actual data being stored and retrieved
to demonstrate that user isolation is working correctly.
"""

import asyncio
import json
import logging
import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Import our memory systems
from services.memory.storage.redis_store import RedisStore
from services.memory.storage.vector_store import VectorStore
from services.memory.types import MemoryItem

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


async def detailed_privacy_test():
    """Run detailed privacy test showing actual data flow."""

    print("🔒 DETAILED PRIVACY TEST - Showing actual data flow")
    print("=" * 60)

    # Initialize systems
    redis_store = RedisStore()
    vector_store = VectorStore()

    await redis_store.initialize()
    await vector_store.initialize()

    # Create 2 test users with very different data
    user_alice = "alice_12345"
    user_bob = "bob_67890"

    print(f"\n👥 Creating test users:")
    print(f"   • User Alice: {user_alice}")
    print(f"   • User Bob: {user_bob}")

    # Create Alice's sensitive data
    alice_memories = []
    alice_data = [
        "Alice's secret diary: I went to the doctor about my anxiety today.",
        "Alice's bank account: Chase Bank, account #123-456-789, balance $5,230",
        "Alice's personal note: My mother's maiden name is Thompson.",
        "Alice confidential: Meeting with therapist Dr. Johnson at 3pm tomorrow.",
    ]

    print(f"\n📝 Storing Alice's sensitive data:")
    for i, content in enumerate(alice_data):
        memory = MemoryItem(
            id=f"alice_memory_{i}_{uuid.uuid4().hex[:8]}",
            content=content,
            type=f"personal_data_{i}",
            timestamp=datetime.now() + timedelta(minutes=i),
            metadata={
                "user_id": user_alice,
                "privacy_level": "high",
                "sensitive": True,
                "category": f"alice_category_{i}",
            },
        )

        # Store in both systems
        redis_success = await redis_store.store_memory(user_alice, memory)
        vector_success = await vector_store.store_memory(user_alice, memory)

        print(f"   ✓ Stored: {content[:50]}...")
        print(
            f"     Redis: {'✓' if redis_success else '✗'}, Vector: {'✓' if vector_success else '✗'}"
        )

        alice_memories.append(memory)

    # Create Bob's completely different sensitive data
    bob_memories = []
    bob_data = [
        "Bob's confidential: Just got fired from TechCorp, need new job ASAP.",
        "Bob's banking: Wells Fargo account #987-654-321, balance $1,850",
        "Bob's personal: Relationship problems with Sarah, considering breakup.",
        "Bob medical: Prescription for depression medication from Dr. Martinez.",
    ]

    print(f"\n📝 Storing Bob's sensitive data:")
    for i, content in enumerate(bob_data):
        memory = MemoryItem(
            id=f"bob_memory_{i}_{uuid.uuid4().hex[:8]}",
            content=content,
            type=f"personal_data_{i}",
            timestamp=datetime.now() + timedelta(minutes=i + 10),
            metadata={
                "user_id": user_bob,
                "privacy_level": "high",
                "sensitive": True,
                "category": f"bob_category_{i}",
            },
        )

        # Store in both systems
        redis_success = await redis_store.store_memory(user_bob, memory)
        vector_success = await vector_store.store_memory(user_bob, memory)

        print(f"   ✓ Stored: {content[:50]}...")
        print(
            f"     Redis: {'✓' if redis_success else '✗'}, Vector: {'✓' if vector_success else '✗'}"
        )

        bob_memories.append(memory)

    print(f"\n🔍 PRIVACY ISOLATION TESTING:")
    print("=" * 60)

    # Test 1: Alice retrieves her own data
    print(f"\n1️⃣ Alice retrieves her own Redis data:")
    alice_redis_data = await redis_store.get_user_memories(user_alice)
    print(f"   Found {len(alice_redis_data)} memories for Alice:")
    for memory in alice_redis_data:
        print(f"   ✓ {memory.content[:50]}...")
        if memory.user_id != user_alice:
            print(f"   ❌ ERROR: Memory belongs to {memory.user_id}, not Alice!")

    print(f"\n2️⃣ Alice retrieves her own Vector data:")
    alice_vector_data = await vector_store.get_user_memories(user_alice)
    print(f"   Found {len(alice_vector_data)} memories for Alice:")
    for memory in alice_vector_data:
        print(f"   ✓ {memory['content'][:50]}...")
        if memory["metadata"].get("user_id") != user_alice:
            print(
                f"   ❌ ERROR: Memory belongs to {memory['metadata'].get('user_id')}, not Alice!"
            )

    # Test 2: Bob retrieves his own data
    print(f"\n3️⃣ Bob retrieves his own Redis data:")
    bob_redis_data = await redis_store.get_user_memories(user_bob)
    print(f"   Found {len(bob_redis_data)} memories for Bob:")
    for memory in bob_redis_data:
        print(f"   ✓ {memory.content[:50]}...")
        if memory.user_id != user_bob:
            print(f"   ❌ ERROR: Memory belongs to {memory.user_id}, not Bob!")

    print(f"\n4️⃣ Bob retrieves his own Vector data:")
    bob_vector_data = await vector_store.get_user_memories(user_bob)
    print(f"   Found {len(bob_vector_data)} memories for Bob:")
    for memory in bob_vector_data:
        print(f"   ✓ {memory['content'][:50]}...")
        if memory["metadata"].get("user_id") != user_bob:
            print(
                f"   ❌ ERROR: Memory belongs to {memory['metadata'].get('user_id')}, not Bob!"
            )

    # Test 3: Cross-contamination check
    print(f"\n🚨 CROSS-CONTAMINATION TESTS:")
    print("=" * 60)

    contamination_found = False

    # Check if Alice can see Bob's data
    print(f"\n5️⃣ Checking if Alice can see Bob's sensitive data:")
    for alice_memory in alice_redis_data:
        for bob_keyword in ["TechCorp", "Wells Fargo", "Sarah", "Dr. Martinez"]:
            if bob_keyword in alice_memory.content:
                print(f"   ❌ PRIVACY BREACH: Alice can see Bob's data: {bob_keyword}")
                contamination_found = True

    if not contamination_found:
        print("   ✅ No contamination: Alice cannot see Bob's sensitive data")

    # Check if Bob can see Alice's data
    print(f"\n6️⃣ Checking if Bob can see Alice's sensitive data:")
    for bob_memory in bob_redis_data:
        for alice_keyword in ["Chase Bank", "Thompson", "Dr. Johnson", "anxiety"]:
            if alice_keyword in bob_memory.content:
                print(
                    f"   ❌ PRIVACY BREACH: Bob can see Alice's data: {alice_keyword}"
                )
                contamination_found = True

    if not contamination_found:
        print("   ✅ No contamination: Bob cannot see Alice's sensitive data")

    # Test 4: Vector search isolation
    print(f"\n7️⃣ Testing vector search isolation:")

    # Alice searches for Bob's sensitive terms
    print(f"   Alice searches for 'bank account':")
    alice_search = await vector_store.similarity_search("bank account", user_alice, k=5)
    print(f"   Found {len(alice_search)} results for Alice:")
    for result in alice_search:
        print(f"   ✓ {result['content'][:50]}...")
        if "Wells Fargo" in result["content"]:  # Bob's bank
            print(f"   ❌ PRIVACY BREACH: Alice found Bob's bank info!")
            contamination_found = True
        elif "Chase Bank" in result["content"]:  # Alice's bank
            print(f"   ✅ Correct: Alice found her own bank info")

    # Bob searches for Alice's sensitive terms
    print(f"\n   Bob searches for 'doctor appointment':")
    bob_search = await vector_store.similarity_search(
        "doctor appointment", user_bob, k=5
    )
    print(f"   Found {len(bob_search)} results for Bob:")
    for result in bob_search:
        print(f"   ✓ {result['content'][:50]}...")
        if "Dr. Johnson" in result["content"]:  # Alice's doctor
            print(f"   ❌ PRIVACY BREACH: Bob found Alice's doctor info!")
            contamination_found = True
        elif "Dr. Martinez" in result["content"]:  # Bob's doctor
            print(f"   ✅ Correct: Bob found his own doctor info")

    # Summary
    print(f"\n🎯 PRIVACY TEST SUMMARY:")
    print("=" * 60)
    print(f"✅ Alice's Redis memories: {len(alice_redis_data)}")
    print(f"✅ Alice's Vector memories: {len(alice_vector_data)}")
    print(f"✅ Bob's Redis memories: {len(bob_redis_data)}")
    print(f"✅ Bob's Vector memories: {len(bob_vector_data)}")

    if contamination_found:
        print(f"❌ PRIVACY BREACH DETECTED!")
        print(f"   Users can see each other's sensitive data")
    else:
        print(f"✅ PRIVACY PROTECTION VERIFIED!")
        print(f"   Perfect user data isolation maintained")
        print(f"   No cross-user data leakage detected")

    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    await redis_store.clear_user_memories(user_alice)
    await redis_store.clear_user_memories(user_bob)
    await vector_store.clear_user_memories(user_alice)
    await vector_store.clear_user_memories(user_bob)
    print(f"✅ Cleanup completed")

    return not contamination_found


if __name__ == "__main__":
    try:
        result = asyncio.run(detailed_privacy_test())
        if result:
            print(f"\n🎉 PRIVACY TEST PASSED - Data isolation working perfectly!")
            sys.exit(0)
        else:
            print(f"\n⚠️ PRIVACY TEST FAILED - Data isolation issues detected!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
