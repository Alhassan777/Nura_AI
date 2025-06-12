import asyncio
from services.memory.memoryService import MemoryService
from datetime import datetime, timezone


async def test_full_pipeline():
    print("🧪 Testing full memory pipeline with simplified system...")

    service = MemoryService()
    test_user_id = "test_user_simple"

    # Clear any existing memories (skip this to avoid the Pinecone namespace error)
    try:
        await service.clear_memories(test_user_id)
    except Exception as e:
        print(f"⚠️ Could not clear memories (expected for new users): {e}")

    # User consent to bypass PII issues for testing
    user_consent = {
        "privacy_settings": {
            "allow_long_term_storage": True,
            "auto_anonymize_pii": True,
            "preserve_emotional_anchors": True,
            "require_consent_for_sensitive_stories": False,
        }
    }

    # Test 1: Store a long-term memory
    print("\n=== TEST 1: LONG-TERM MEMORY ===")
    long_term_content = "My young brother died today"
    result1 = await service.process_memory(
        user_id=test_user_id,
        content=long_term_content,
        type="conversation_turn",
        user_consent=user_consent,
    )
    print(f"✅ Storage result: {result1.get('stored', False)}")
    print(f"Storage details: {result1}")

    # Test 2: Store an emotional anchor
    print("\n=== TEST 2: EMOTIONAL ANCHOR ===")
    anchor_content = "The old oak tree in the park makes me feel connected to something bigger when I sit under it"
    result2 = await service.process_memory(
        user_id=test_user_id,
        content=anchor_content,
        type="conversation_turn",
        user_consent=user_consent,
    )
    print(f"✅ Storage result: {result2.get('stored', False)}")
    print(f"Storage details: {result2}")

    # Test 3: Store a short-term memory
    print("\n=== TEST 3: SHORT-TERM MEMORY ===")
    short_term_content = "I feel stressed about work today"
    result3 = await service.process_memory(
        user_id=test_user_id,
        content=short_term_content,
        type="conversation_turn",
        user_consent=user_consent,
    )
    print(f"✅ Storage result: {result3.get('stored', False)}")
    print(f"Storage details: {result3}")

    # Now check what was actually stored
    print("\n=== RETRIEVAL TESTS ===")

    # Get long-term memories
    long_term_memories = await service.get_regular_memories(test_user_id)
    print(f"📚 Long-term memories found: {len(long_term_memories)}")
    for memory in long_term_memories:
        print(
            f"  - {memory.content[:50]}... (category: {memory.metadata.get('memory_category')})"
        )

    # Get emotional anchors
    emotional_anchors = await service.get_emotional_anchors(test_user_id)
    print(f"❤️ Emotional anchors found: {len(emotional_anchors)}")
    for anchor in emotional_anchors:
        print(
            f"  - {anchor.content[:50]}... (category: {anchor.metadata.get('memory_category')})"
        )

    # Get memory context (should include short-term)
    context = await service.get_memory_context(test_user_id)
    print(f"⏱️ Context memories found: {len(context.short_term)}")
    for memory in context.short_term:
        print(
            f"  - {memory.content[:50]}... (category: {memory.metadata.get('memory_category')})"
        )


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
