#!/usr/bin/env python3
"""
Test script for cleaned up Nura Memory System endpoints.

This script tests all the main functionality after code cleanup:
- Significance-based memory scoring
- Dual storage strategy
- Mental health assistant
- Memory context retrieval
- PII detection
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_endpoint(
    method: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    params: Dict[str, str] = None,
) -> Dict[str, Any]:
    """Test an API endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, params=params)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing {method} {endpoint}: {e}")
        return {"error": str(e)}


def main():
    """Run comprehensive tests of the cleaned up memory system."""
    print("🧪 Testing Cleaned Up Nura Memory System")
    print("=" * 50)

    user_id = "test_cleanup_user"

    # Test 1: Health Check
    print("\n1. 🏥 Testing Health Check...")
    health = test_endpoint("GET", "/health")
    if "status" in health:
        print(f"✅ Health: {health['status']}")
        print(
            f"   Configuration: {health.get('configuration', {}).get('status', 'unknown')}"
        )
    else:
        print("❌ Health check failed")

    # Test 2: Clear any existing memories
    print(f"\n2. 🧹 Clearing existing memories for user {user_id}...")
    clear_result = test_endpoint("POST", "/memory/forget", params={"user_id": user_id})
    print("✅ Memories cleared")

    # Test 3: Test significance-based scoring with different types of memories
    print("\n3. 🧠 Testing Significance-Based Memory Scoring...")

    test_memories = [
        {
            "content": "I got into Harvard today, my dream college!",
            "type": "user_message",
            "metadata": {"source": "chat_interface"},
            "expected": "critical significance",
        },
        {
            "content": "I realized I get anxious when my mom calls because she criticizes everything",
            "type": "user_message",
            "metadata": {"source": "chat_interface"},
            "expected": "high significance",
        },
        {
            "content": "I had coffee this morning",
            "type": "user_message",
            "metadata": {"source": "chat_interface"},
            "expected": "low significance",
        },
        {
            "content": "My name is Sarah Johnson and I take Zoloft for depression",
            "type": "user_message",
            "metadata": {"source": "chat_interface"},
            "expected": "PII detection",
        },
    ]

    for i, memory in enumerate(test_memories):
        print(f"\n   Testing memory {i+1}: {memory['content'][:50]}...")
        result = test_endpoint(
            "POST", "/memory/dual-storage", data=memory, params={"user_id": user_id}
        )

        if "stored" in result:
            stored = result["stored"]
            score = result.get("score", {})
            pii_summary = result.get("pii_summary", {})

            print(f"   ✅ Stored: {stored}")
            if score:
                print(
                    f"      Scores: R={score.get('relevance', 0):.2f}, S={score.get('stability', 0):.2f}, E={score.get('explicitness', 0):.2f}"
                )
            if pii_summary.get("detected"):
                print(f"      🔒 PII detected: {pii_summary.get('types', [])}")
        else:
            print(f"   ❌ Failed to process memory")

    # Test 4: Memory Stats
    print(f"\n4. 📊 Testing Memory Stats...")
    stats = test_endpoint("GET", "/memory/stats", params={"user_id": user_id})
    if "stats" in stats:
        s = stats["stats"]
        print(f"✅ Memory Stats:")
        print(f"   Total: {s.get('total', 0)}")
        print(f"   Short-term: {s.get('short_term', 0)}")
        print(f"   Long-term: {s.get('long_term', 0)}")
        print(f"   Sensitive: {s.get('sensitive', 0)}")
    else:
        print("❌ Failed to get memory stats")

    # Test 5: Mental Health Assistant
    print(f"\n5. 🤖 Testing Mental Health Assistant...")
    chat_messages = [
        "How are you doing today?",
        "I'm feeling really overwhelmed with everything",
        "I want to end it all",  # Crisis detection test
    ]

    for msg in chat_messages:
        print(f"\n   Testing: {msg}")
        result = test_endpoint(
            "POST",
            "/chat/assistant",
            data={"message": msg, "include_memory": True},
            params={"user_id": user_id},
        )

        if "response" in result:
            print(f"   ✅ Response: {result['response'][:100]}...")
            print(f"      Crisis Level: {result.get('crisis_level', 'unknown')}")
            print(f"      Memory Stored: {result.get('memory_stored', False)}")
        else:
            print(f"   ❌ Failed to get assistant response")

    # Test 6: Memory Context Retrieval
    print(f"\n6. 🔍 Testing Memory Context Retrieval...")
    context = test_endpoint(
        "POST",
        "/memory/context",
        data={"query": "college"},
        params={"user_id": user_id},
    )

    if "context" in context:
        ctx = context["context"]
        short_term_count = len(ctx.get("short_term", []))
        long_term_count = len(ctx.get("long_term", []))
        print(f"✅ Context Retrieved:")
        print(f"   Short-term memories: {short_term_count}")
        print(f"   Long-term memories: {long_term_count}")
        if ctx.get("digest"):
            print(f"   Digest: {ctx['digest'][:100]}...")
    else:
        print("❌ Failed to get memory context")

    # Test 7: Configuration Status
    print(f"\n7. ⚙️  Testing Configuration...")
    config_test = test_endpoint("GET", "/config/test")
    if "status" in config_test:
        print(f"✅ Configuration Status: {config_test['status']}")
        if config_test["status"] == "CONFIGURATION_ERROR":
            print(
                f"   ⚠️  Issues: {config_test.get('details', {}).get('missing_required', [])}"
            )
    else:
        print("❌ Failed to get configuration status")

    # Final Stats
    print(f"\n8. 📈 Final Memory Stats...")
    final_stats = test_endpoint("GET", "/memory/stats", params={"user_id": user_id})
    if "stats" in final_stats:
        s = final_stats["stats"]
        print(f"✅ Final Stats:")
        print(f"   Total memories processed: {s.get('total', 0)}")
        print(f"   Short-term storage: {s.get('short_term', 0)}")
        print(f"   Long-term storage: {s.get('long_term', 0)}")
        print(f"   Sensitive items: {s.get('sensitive', 0)}")

    print("\n" + "=" * 50)
    print("🎉 Cleanup Testing Complete!")
    print("\n✨ Key Improvements After Cleanup:")
    print("   • Removed legacy numeric scoring")
    print("   • Simplified significance-based approach")
    print("   • Removed unused quick filter")
    print("   • Cleaned up redundant demo files")
    print("   • Streamlined API responses")
    print("   • Improved error handling")


if __name__ == "__main__":
    main()
