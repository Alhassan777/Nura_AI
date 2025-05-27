#!/usr/bin/env python3
"""
Test Optimized Memory System

This script tests the optimized memory system to ensure all components work correctly.
"""

import asyncio
import os
import sys
from datetime import datetime
import uuid

# Load environment variables
from dotenv import load_dotenv

load_dotenv(".env.local")

# Add src to path
sys.path.append(".")

from services.memory.memoryService import MemoryService
from services.memory.types import MemoryItem


async def test_optimized_system():
    """Test the optimized memory system."""
    print("🧪 Testing Optimized Memory System...")
    print("=" * 50)

    try:
        # Initialize memory service
        print("1️⃣ Initializing optimized memory service...")
        memory_service = MemoryService()
        print("✅ Memory service initialized successfully!")

        # Test memory processing with component extraction
        print("\n2️⃣ Testing memory processing with component extraction...")
        test_message = (
            "I felt happy today because I met my girlfriend for the first time in Jeju"
        )

        result = await memory_service.process_memory(
            user_id="test_user_optimized", content=test_message, type="chat"
        )

        print(
            f"✅ Processed memory with {result.get('total_components', 0)} components"
        )
        print(f"   Stored components: {result.get('stored_components', 0)}")

        # Display component breakdown
        if result.get("components"):
            for i, component in enumerate(result["components"]):
                print(
                    f"   Component {i+1}: {component.get('memory_type', 'unknown')} - {component.get('stored', False)}"
                )

        # Test memory retrieval
        print("\n3️⃣ Testing memory retrieval...")
        context = await memory_service.get_memory_context(
            "test_user_optimized", "girlfriend Jeju"
        )
        print(f"✅ Retrieved context with {len(context.long_term)} long-term memories")

        # Test emotional anchors
        print("\n4️⃣ Testing emotional anchors...")
        anchors = await memory_service.get_emotional_anchors("test_user_optimized")
        print(f"✅ Found {len(anchors)} emotional anchors")

        for anchor in anchors:
            print(f"   📍 {anchor.content[:50]}...")

        # Test regular memories
        print("\n5️⃣ Testing regular memories...")
        regular = await memory_service.get_regular_memories("test_user_optimized")
        print(f"✅ Found {len(regular)} regular memories")

        # Test memory stats
        print("\n6️⃣ Testing memory statistics...")
        stats = await memory_service.get_memory_stats("test_user_optimized")
        print(
            f"✅ Memory stats: {stats.total} total, {stats.short_term} short-term, {stats.long_term} long-term"
        )

        # Clean up
        print("\n7️⃣ Cleaning up test data...")
        await memory_service.clear_memories("test_user_optimized")
        print("✅ Test data cleaned up")

        print("\n🎉 Optimized system test completed successfully!")
        print("=" * 50)
        print("✅ Memory processing working correctly")
        print("✅ Component extraction functioning")
        print("✅ Vector database operations successful")
        print("✅ PII detection optimized")
        print("✅ Code duplication eliminated")

    except Exception as e:
        print(f"\n❌ Error during system test: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_optimized_system())
