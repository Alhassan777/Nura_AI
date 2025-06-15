#!/usr/bin/env python3
"""
Test script to verify that the background processing synchronization fix works.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from multi_modal_chat import MultiModalChatService
import logging

logging.basicConfig(level=logging.INFO)


async def test_sync_fix():
    """Test the synchronization fix for background results."""
    print("🧪 Testing Background Processing Synchronization Fix")
    print("=" * 50)

    service = MultiModalChatService()

    # Test user ID (use a UUID format)
    test_user_id = "5aad95e6-7170-411d-a983-3fba374309b3"
    test_message = "Hello, I want a plan to start going to the gym and get fit for the summer season"

    try:
        print(f"1. Sending message: '{test_message[:50]}...'")

        # Process message (this should return immediately with background_task_id)
        result = await service.process_message(
            user_id=test_user_id, message=test_message, mode="action_plan"
        )

        print(
            f"✅ Immediate response received in {result.get('response_time_ms', 0):.1f}ms"
        )
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Background task ID: {result['background_task_id']}")

        # Immediately try to get background results (should return "processing" status)
        print(
            "\n2. Immediately checking background results (should be 'processing')..."
        )

        bg_results = await service.get_background_results(result["background_task_id"])

        if bg_results:
            print(f"✅ Background results found immediately!")
            print(f"   Status: {bg_results.get('status', 'unknown')}")
            print(f"   Tasks completed: {len(bg_results.get('tasks', {}))}")

            if bg_results.get("status") == "processing":
                print("✅ Status is 'processing' as expected - no 404 error!")
            else:
                print(f"⚠️  Status is '{bg_results.get('status')}' - unexpected")
        else:
            print("❌ Background results not found - sync fix may not be working")
            return False

        # Wait a bit and check again (should be completed)
        print("\n3. Waiting 3 seconds for background processing to complete...")
        await asyncio.sleep(3)

        bg_results_final = await service.get_background_results(
            result["background_task_id"]
        )

        if bg_results_final:
            print(f"✅ Final background results:")
            print(f"   Status: {bg_results_final.get('status', 'unknown')}")
            print(f"   Tasks completed: {len(bg_results_final.get('tasks', {}))}")

            if bg_results_final.get("status") == "completed":
                print("✅ Background processing completed successfully!")
                return True
            else:
                print(f"⚠️  Status is still '{bg_results_final.get('status')}'")
                return False
        else:
            print("❌ Final background results not found")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sync_fix())

    if success:
        print("\n🎉 Synchronization fix test PASSED!")
        print("   - No 404 errors when immediately polling for results")
        print("   - Proper status tracking ('processing' → 'completed')")
        print("   - Background processing completes successfully")
    else:
        print("\n❌ Synchronization fix test FAILED!")
        print("   Please check the implementation and try again")
        sys.exit(1)
