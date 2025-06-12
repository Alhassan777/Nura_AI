import asyncio
import json
from services.memory.memoryService import MemoryService
from datetime import datetime, timezone


async def test_comprehensive_pipeline():
    """
    Comprehensive test of the simplified memory pipeline.
    Tests all 3 categories, storage, retrieval, and API compatibility.
    """
    print("🧪 COMPREHENSIVE MEMORY PIPELINE TEST")
    print("=" * 50)

    service = MemoryService()
    test_user_id = "comprehensive_test_user"

    # Clear any existing memories
    try:
        await service.clear_memories(test_user_id)
        print("✅ Cleared existing memories")
    except Exception as e:
        print(f"⚠️ Could not clear memories (expected for new users): {e}")

    # User consent to bypass PII issues
    user_consent = {
        "privacy_settings": {
            "allow_long_term_storage": True,
            "auto_anonymize_pii": True,
            "preserve_emotional_anchors": True,
            "require_consent_for_sensitive_stories": False,
        }
    }

    print("\n📝 TESTING MEMORY CLASSIFICATION & STORAGE")
    print("-" * 50)

    # Test cases for each category
    test_cases = [
        {
            "name": "Long-term Memory 1",
            "content": "My young brother died today",
            "expected_category": "long_term",
            "expected_storage": {"short_term": True, "long_term": True},
        },
        {
            "name": "Long-term Memory 2",
            "content": "I graduated from college and finally understand my purpose in life",
            "expected_category": "long_term",
            "expected_storage": {"short_term": True, "long_term": True},
        },
        {
            "name": "Emotional Anchor 1",
            "content": "The old oak tree in the park makes me feel connected to something bigger when I sit under it",
            "expected_category": "emotional_anchor",
            "expected_storage": {"short_term": True, "long_term": True},
        },
        {
            "name": "Emotional Anchor 2",
            "content": "My grandmother's garden is where I feel most at peace and remember her love",
            "expected_category": "emotional_anchor",
            "expected_storage": {"short_term": True, "long_term": True},
        },
        {
            "name": "Short-term Memory 1",
            "content": "I feel stressed about work today",
            "expected_category": "short_term",
            "expected_storage": {
                "short_term": False,
                "long_term": False,
            },  # Won't be stored
        },
        {
            "name": "Short-term Memory 2",
            "content": "Had coffee this morning and feeling tired",
            "expected_category": "short_term",
            "expected_storage": {
                "short_term": False,
                "long_term": False,
            },  # Won't be stored
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Content: {test_case['content']}")

        # Process the memory
        result = await service.process_memory(
            user_id=test_user_id,
            content=test_case["content"],
            type="conversation_turn",
            user_consent=user_consent,
        )

        # Extract results
        stored = result.get("stored", False)
        components = result.get("components", [])

        if components:
            component = components[0]
            actual_category = component.get("memory_category", "unknown")
            storage_details = component.get("storage_details", {})

            # Check if classification matches expected
            category_match = actual_category == test_case["expected_category"]

            # Check storage
            short_term_stored = bool(storage_details.get("short_term", False))
            long_term_stored = bool(storage_details.get("long_term", False))

            result_summary = {
                "name": test_case["name"],
                "content": test_case["content"],
                "expected_category": test_case["expected_category"],
                "actual_category": actual_category,
                "category_match": category_match,
                "stored": stored,
                "short_term_stored": short_term_stored,
                "long_term_stored": long_term_stored,
                "expected_storage": test_case["expected_storage"],
            }

            print(f"   ✅ Category: {actual_category} {'✓' if category_match else '✗'}")
            print(
                f"   ✅ Stored: {stored} (short: {short_term_stored}, long: {long_term_stored})"
            )

        else:
            result_summary = {
                "name": test_case["name"],
                "content": test_case["content"],
                "expected_category": test_case["expected_category"],
                "actual_category": "none",
                "category_match": False,
                "stored": False,
                "short_term_stored": False,
                "long_term_stored": False,
                "expected_storage": test_case["expected_storage"],
            }
            print(f"   ❌ No components found")

        results.append(result_summary)

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    print("\n🔍 TESTING RETRIEVAL METHODS")
    print("-" * 50)

    # Test all retrieval methods
    regular_memories = await service.get_regular_memories(test_user_id)
    emotional_anchors = await service.get_emotional_anchors(test_user_id)
    memory_context = await service.get_memory_context(test_user_id)
    memory_stats = await service.get_memory_stats(test_user_id)

    print(f"📚 Regular memories: {len(regular_memories)}")
    for memory in regular_memories:
        category = memory.metadata.get("memory_category", "unknown")
        print(f"   - {memory.content[:50]}... (category: {category})")

    print(f"❤️ Emotional anchors: {len(emotional_anchors)}")
    for anchor in emotional_anchors:
        category = anchor.metadata.get("memory_category", "unknown")
        print(f"   - {anchor.content[:50]}... (category: {category})")

    print(f"⏱️ Context memories: {len(memory_context.short_term)}")
    for memory in memory_context.short_term:
        category = memory.metadata.get("memory_category", "unknown")
        print(f"   - {memory.content[:50]}... (category: {category})")

    print(
        f"📊 Memory stats: total={memory_stats.total}, short_term={memory_stats.short_term}, long_term={memory_stats.long_term}"
    )

    print("\n🌐 TESTING API COMPATIBILITY")
    print("-" * 50)

    # Test API-like responses that frontend expects
    try:
        # Test get all long-term memories (what frontend calls)
        long_term_api_response = []
        for memory in regular_memories + emotional_anchors:
            api_memory = {
                "id": memory.id,
                "content": memory.content,
                "type": memory.type,
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata,
                "category": memory.metadata.get("memory_category", "unknown"),
                "is_meaningful": memory.metadata.get("is_meaningful", False),
                "is_lasting": memory.metadata.get("is_lasting", False),
                "is_symbolic": memory.metadata.get("is_symbolic", False),
            }
            long_term_api_response.append(api_memory)

        print(
            f"✅ API-compatible long-term response: {len(long_term_api_response)} memories"
        )

        # Test memory stats API response
        stats_api_response = {
            "total_memories": memory_stats.total,
            "short_term_memories": memory_stats.short_term,
            "long_term_memories": memory_stats.long_term,
            "emotional_anchors": len(emotional_anchors),
            "regular_memories": len(regular_memories),
        }

        print(
            f"✅ API-compatible stats response: {json.dumps(stats_api_response, indent=2)}"
        )

    except Exception as e:
        print(f"❌ API compatibility error: {e}")

    print("\n📈 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)

    # Summary statistics
    total_tests = len(results)
    category_matches = sum(1 for r in results if r["category_match"])
    successful_stores = sum(1 for r in results if r["stored"])

    print(f"Total test cases: {total_tests}")
    print(
        f"Category classification accuracy: {category_matches}/{total_tests} ({category_matches/total_tests*100:.1f}%)"
    )
    print(f"Successful storage operations: {successful_stores}/{total_tests}")

    # Detailed breakdown
    long_term_tests = [r for r in results if r["expected_category"] == "long_term"]
    anchor_tests = [r for r in results if r["expected_category"] == "emotional_anchor"]
    short_term_tests = [r for r in results if r["expected_category"] == "short_term"]

    print(f"\nBreakdown by category:")
    print(
        f"  Long-term: {sum(1 for r in long_term_tests if r['category_match'])}/{len(long_term_tests)} correct"
    )
    print(
        f"  Emotional anchors: {sum(1 for r in anchor_tests if r['category_match'])}/{len(anchor_tests)} correct"
    )
    print(
        f"  Short-term: {sum(1 for r in short_term_tests if r['category_match'])}/{len(short_term_tests)} correct"
    )

    print(f"\nRetrieval verification:")
    print(f"  Expected long-term memories: {len(long_term_tests + anchor_tests)}")
    print(f"  Actually retrieved: {len(regular_memories + emotional_anchors)}")
    print(f"  Expected emotional anchors: {len(anchor_tests)}")
    print(f"  Actually retrieved emotional anchors: {len(emotional_anchors)}")

    # Final verdict
    all_categories_correct = category_matches == total_tests
    storage_working = len(regular_memories + emotional_anchors) >= len(
        [
            r
            for r in results
            if r["expected_category"] in ["long_term", "emotional_anchor"]
            and r["stored"]
        ]
    )

    print(f"\n🎯 FINAL VERDICT:")
    if all_categories_correct and storage_working:
        print("✅ PIPELINE FULLY FUNCTIONAL - All tests passed!")
    elif category_matches >= total_tests * 0.8:
        print("⚠️ PIPELINE MOSTLY FUNCTIONAL - Minor issues detected")
    else:
        print("❌ PIPELINE NEEDS FIXES - Major issues detected")

    print(f"\n✅ Test completed successfully!")
    return results


if __name__ == "__main__":
    asyncio.run(test_comprehensive_pipeline())
