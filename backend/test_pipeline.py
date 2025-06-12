#!/usr/bin/env python3
"""
Test script to verify the simplified memory pipeline works correctly
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.memory.memoryService import MemoryService


async def test_memory_pipeline():
    """Test the complete memory pipeline with simplified metadata"""
    memory_service = MemoryService()

    # Test processing a meaningful memory
    test_memory = "My young brother died today"
    user_id = "test-user-123"

    print("🧪 Testing memory pipeline with simplified metadata...")

    try:
        # Process the memory
        result = await memory_service.process_memory(
            user_id=user_id, content=test_memory, type="chat"
        )

        print(f'✅ Memory processed: {result.get("stored", False)}')

        # Test retrieval
        print("🔍 Testing retrieval...")
        regular_memories = await memory_service.get_regular_memories(user_id)
        emotional_anchors = await memory_service.get_emotional_anchors(user_id)

        print(f"📚 Regular memories found: {len(regular_memories)}")
        print(f"❤️ Emotional anchors found: {len(emotional_anchors)}")

        # Show memory categories
        print("\n📋 Memory categorization:")
        for memory in regular_memories + emotional_anchors:
            category = memory.metadata.get("memory_category", "unknown")
            is_meaningful = memory.metadata.get("is_meaningful", False)
            is_lasting = memory.metadata.get("is_lasting", False)
            is_symbolic = memory.metadata.get("is_symbolic", False)

            print(f"   - Category: {category}")
            print(f"     Content: {memory.content[:50]}...")
            print(
                f"     Meaningful: {is_meaningful}, Lasting: {is_lasting}, Symbolic: {is_symbolic}"
            )
            print()

        # Test the API endpoints that frontend calls
        print("🌐 Testing API endpoint compatibility...")
        context = await memory_service.get_memory_context(user_id)
        stats = await memory_service.get_memory_stats(user_id)

        print(
            f"✅ Context retrieved: {len(context.short_term)} short-term, {len(context.long_term)} long-term"
        )
        print(f"✅ Stats retrieved: {stats.total} total memories")

        return True

    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_memory_pipeline())
    if success:
        print("\n🎉 Memory pipeline test completed successfully!")
    else:
        print("\n💥 Memory pipeline test failed!")
        sys.exit(1)
