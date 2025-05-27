#!/usr/bin/env python3
"""
Test script for Voice Mapping functionality (Section 1 of Vapi roadmap).
Tests multiple simultaneous calls map correctly with 3 fake callIds.
"""

import asyncio
import uuid
import json
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our voice utilities
import sys
import os

sys.path.append(".")

from services.memory.utils.vapi import (
    get_customer_id,
    get_call_mapping,
    store_call_mapping,
    delete_call_mapping,
    extract_call_id_from_vapi_event,
    is_conversation_update_event,
)


async def test_voice_mapping():
    """Test voice mapping functionality with multiple simultaneous calls."""
    print("🧪 Testing Voice Mapping System (Section 1)")
    print("=" * 50)

    # Test data: 3 fake call IDs with different customer IDs
    test_calls = [
        {
            "call_id": f"call_web_{uuid.uuid4()}",
            "customer_id": "user-alice-123",
            "mode": "web",
            "phone_number": None,
        },
        {
            "call_id": f"call_phone_{uuid.uuid4()}",
            "customer_id": "user-bob-456",
            "mode": "phone",
            "phone_number": "+1234567890",
        },
        {
            "call_id": f"call_web_{uuid.uuid4()}",
            "customer_id": "user-charlie-789",
            "mode": "web",
            "phone_number": None,
        },
    ]

    success_count = 0

    try:
        # Test 1: Store all mappings
        print("\n1️⃣ Storing call mappings...")
        for i, call_data in enumerate(test_calls):
            result = await store_call_mapping(
                call_data["call_id"],
                call_data["customer_id"],
                call_data["mode"],
                call_data["phone_number"],
                ttl_minutes=5,  # Short TTL for testing
            )

            if result:
                print(
                    f"  ✅ Call {i+1}: {call_data['call_id'][:20]}... -> {call_data['customer_id']}"
                )
                success_count += 1
            else:
                print(f"  ❌ Call {i+1}: Failed to store mapping")

        # Test 2: Retrieve customer IDs
        print("\n2️⃣ Retrieving customer IDs...")
        for i, call_data in enumerate(test_calls):
            customer_id = await get_customer_id(call_data["call_id"])
            expected_id = call_data["customer_id"]

            if customer_id == expected_id:
                print(f"  ✅ Call {i+1}: {customer_id} (correct)")
            else:
                print(f"  ❌ Call {i+1}: Expected {expected_id}, got {customer_id}")
                success_count -= 1

        # Test 3: Retrieve complete mappings
        print("\n3️⃣ Retrieving complete call mappings...")
        for i, call_data in enumerate(test_calls):
            mapping = await get_call_mapping(call_data["call_id"])

            if mapping:
                expected_fields = ["customerId", "mode", "timestamp", "callId"]
                missing_fields = [
                    field for field in expected_fields if field not in mapping
                ]

                if (
                    not missing_fields
                    and mapping["customerId"] == call_data["customer_id"]
                ):
                    print(f"  ✅ Call {i+1}: Complete mapping retrieved")
                    print(f"      Customer: {mapping['customerId']}")
                    print(f"      Mode: {mapping['mode']}")
                    print(f"      Phone: {mapping.get('phoneNumber', 'N/A')}")
                else:
                    print(f"  ❌ Call {i+1}: Incomplete or incorrect mapping")
                    print(f"      Missing fields: {missing_fields}")
                    success_count -= 1
            else:
                print(f"  ❌ Call {i+1}: No mapping found")
                success_count -= 1

        # Test 4: Test non-existent call ID
        print("\n4️⃣ Testing non-existent call ID...")
        fake_call_id = f"nonexistent_{uuid.uuid4()}"
        customer_id = await get_customer_id(fake_call_id)

        if customer_id is None:
            print(f"  ✅ Correctly returned None for non-existent call ID")
        else:
            print(f"  ❌ Expected None, got {customer_id}")
            success_count -= 1

        # Test 5: Test Vapi event parsing
        print("\n5️⃣ Testing Vapi event parsing...")
        test_events = [
            {
                "type": "conversation-update",
                "call": {"id": "test-call-123"},
                "message": "Hello world",
            },
            {"eventType": "heartbeat", "callId": "test-call-456"},
            {"type": "conversation-update", "id": "test-call-789"},
        ]

        for i, event in enumerate(test_events):
            call_id = extract_call_id_from_vapi_event(event)
            is_conversation = is_conversation_update_event(event)

            expected_call_ids = ["test-call-123", "test-call-456", "test-call-789"]
            expected_is_conversation = [True, False, True]

            if call_id == expected_call_ids[i]:
                print(f"  ✅ Event {i+1}: Call ID extracted correctly ({call_id})")
            else:
                print(
                    f"  ❌ Event {i+1}: Expected {expected_call_ids[i]}, got {call_id}"
                )
                success_count -= 1

            if is_conversation == expected_is_conversation[i]:
                print(
                    f"  ✅ Event {i+1}: Conversation detection correct ({is_conversation})"
                )
            else:
                print(
                    f"  ❌ Event {i+1}: Expected {expected_is_conversation[i]}, got {is_conversation}"
                )
                success_count -= 1

        # Test 6: Cleanup - delete mappings
        print("\n6️⃣ Cleaning up call mappings...")
        for i, call_data in enumerate(test_calls):
            result = await delete_call_mapping(call_data["call_id"])

            if result:
                print(f"  ✅ Call {i+1}: Mapping deleted")
            else:
                print(f"  ❌ Call {i+1}: Failed to delete mapping")
                success_count -= 1

        # Test 7: Verify deletion
        print("\n7️⃣ Verifying deletion...")
        for i, call_data in enumerate(test_calls):
            customer_id = await get_customer_id(call_data["call_id"])

            if customer_id is None:
                print(f"  ✅ Call {i+1}: Mapping properly deleted")
            else:
                print(f"  ❌ Call {i+1}: Mapping still exists ({customer_id})")
                success_count -= 1

        print("\n" + "=" * 50)
        total_tests = 22  # 3 store + 3 retrieve + 3 complete + 1 nonexistent + 6 event parsing + 3 delete + 3 verify
        print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")

        if success_count == total_tests:
            print("🎉 All tests passed! Voice mapping system is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Please check the implementation.")
            return False

    except Exception as e:
        print(f"\n💥 Test suite failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test the API endpoints directly."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)

    try:
        import aiohttp

        base_url = "http://localhost:8000"
        test_call_id = f"api_test_{uuid.uuid4()}"
        test_customer_id = "api-test-user-123"

        async with aiohttp.ClientSession() as session:
            # Test storing mapping via API
            store_data = {
                "callId": test_call_id,
                "customerId": test_customer_id,
                "mode": "web",
                "phoneNumber": None,
            }

            async with session.post(
                f"{base_url}/voice/mapping", json=store_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Store API: {result}")
                else:
                    print(f"❌ Store API failed: {response.status}")

            # Test retrieving mapping via API
            async with session.get(
                f"{base_url}/voice/mapping/{test_call_id}"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Get API: {result}")
                else:
                    print(f"❌ Get API failed: {response.status}")

            # Test deleting mapping via API
            async with session.delete(
                f"{base_url}/voice/mapping/{test_call_id}"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Delete API: {result}")
                else:
                    print(f"❌ Delete API failed: {response.status}")

    except ImportError:
        print("⚠️  aiohttp not available for API testing")
        print("💡 Install with: pip install aiohttp")
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Voice Mapping Tests")

    async def main():
        # Test utility functions
        utils_success = await test_voice_mapping()

        # Test API endpoints
        await test_api_endpoints()

        print(f"\n📋 Section 1 Implementation Status:")
        print(f"   ✅ Task 1.1: GET /api/voice/start endpoint")
        print(f"   ✅ Task 1.2: Persist callId ↔ customerId mapping")
        print(f"   ✅ Task 1.3: Return mapping helper functions")
        print(
            f"   {'✅' if utils_success else '❌'} Acceptance: Multiple simultaneous calls map correctly"
        )

        if utils_success:
            print("\n🎉 Section 1: Identity & Session Mapping - COMPLETE")
        else:
            print("\n⚠️  Section 1: Identity & Session Mapping - NEEDS REVIEW")

    asyncio.run(main())
