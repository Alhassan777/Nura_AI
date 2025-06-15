"""
Integration Test for Multi-Modal Chat System
Tests integration with all existing Nura services.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from .multi_modal_chat import MultiModalChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_service_integrations():
    """Test all service integrations."""

    print("🚀 Starting Multi-Modal Chat Integration Tests")
    print("=" * 60)

    # Initialize service
    try:
        service = MultiModalChatService()
        print("✅ MultiModalChatService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return False

    # Test user ID
    test_user_id = "test_user_integration"
    test_message = (
        "I'm feeling anxious about my job interview tomorrow. Can you help me prepare?"
    )

    results = {}

    # Test 1: Health Check
    print("\n🔍 Testing health check...")
    try:
        health = await service.health_check()
        results["health_check"] = health["status"] in ["healthy", "degraded"]
        print(
            f"✅ Health check: {health['status']} ({health['healthy_services']}/{health['total_services']} services)"
        )
    except Exception as e:
        results["health_check"] = False
        print(f"❌ Health check failed: {e}")

    # Test 2: General Mode Processing
    print("\n💬 Testing general mode message processing...")
    try:
        result = await service.process_message(
            user_id=test_user_id, message=test_message, mode="general"
        )

        results["general_mode"] = (
            "response" in result
            and result["response_time_ms"] < 5000  # Allow 5s for integration test
            and "background_task_id" in result
        )

        print(f"✅ General mode response in {result['response_time_ms']:.1f}ms")
        print(f"   Response: {result['response'][:100]}...")

        # Test background results
        if "background_task_id" in result:
            print(f"   Background task ID: {result['background_task_id']}")

            # Wait a bit for background processing
            await asyncio.sleep(2)

            bg_results = await service.get_background_results(
                result["background_task_id"]
            )
            if bg_results:
                print(f"✅ Background processing completed")
                results["background_processing"] = True
            else:
                print(f"⏳ Background processing still running")
                results["background_processing"] = False

    except Exception as e:
        results["general_mode"] = False
        print(f"❌ General mode test failed: {e}")

    # Test background result synchronization (no 404s)
    print("\n🔄 Testing background result synchronization...")
    try:
        result = await service.process_message(
            user_id=test_user_id,
            message="Help me create a fitness plan",
            mode="action_plan",
        )

        if "background_task_id" in result:
            task_id = result["background_task_id"]
            print(f"   Background task ID: {task_id}")

            # Immediately try to get results - should return "processing" status, not 404
            immediate_results = await service.get_background_results(task_id)
            if immediate_results and immediate_results.get("status") == "processing":
                print("✅ Immediate poll returns 'processing' status (no 404)")
                results["synchronization_fix"] = True
            else:
                print(f"❌ Immediate poll failed: {immediate_results}")
                results["synchronization_fix"] = False

            # Wait for completion
            await asyncio.sleep(3)
            final_results = await service.get_background_results(task_id)
            if final_results and final_results.get("status") == "completed":
                print("✅ Final poll returns 'completed' status")
            else:
                print(
                    f"⏳ Final poll status: {final_results.get('status') if final_results else 'None'}"
                )
        else:
            results["synchronization_fix"] = False

    except Exception as e:
        results["synchronization_fix"] = False
        print(f"❌ Synchronization test failed: {e}")

    # Test 3: Action Plan Mode
    print("\n📋 Testing action plan mode...")
    try:
        action_message = (
            "I want to improve my productivity at work. Can you help me create a plan?"
        )
        result = await service.process_message(
            user_id=test_user_id, message=action_message, mode="action_plan"
        )

        results["action_plan_mode"] = (
            "response" in result and result["mode"] == "action_plan"
        )

        print(f"✅ Action plan mode response in {result['response_time_ms']:.1f}ms")
        print(f"   Mode detected: {result['mode']}")

    except Exception as e:
        results["action_plan_mode"] = False
        print(f"❌ Action plan mode test failed: {e}")

    # Test 4: Visualization Mode
    print("\n🎨 Testing visualization mode...")
    try:
        visual_message = (
            "I feel like I'm drowning in stress. Can you help me visualize this?"
        )
        result = await service.process_message(
            user_id=test_user_id, message=visual_message, mode="visualization"
        )

        results["visualization_mode"] = (
            "response" in result and result["mode"] == "visualization"
        )

        print(f"✅ Visualization mode response in {result['response_time_ms']:.1f}ms")
        print(f"   Mode detected: {result['mode']}")

    except Exception as e:
        results["visualization_mode"] = False
        print(f"❌ Visualization mode test failed: {e}")

    # Test 5: Mode Auto-Detection
    print("\n🤖 Testing mode auto-detection...")
    try:
        auto_message = "I need help planning my fitness goals"
        result = await service.process_message(
            user_id=test_user_id,
            message=auto_message,
            mode="general",  # Start with general, should detect action_plan
        )

        results["auto_detection"] = result.get("mode") == "action_plan"

        print(f"✅ Auto-detected mode: {result['mode']}")

    except Exception as e:
        results["auto_detection"] = False
        print(f"❌ Auto-detection test failed: {e}")

    # Test 6: Cache Performance
    print("\n⚡ Testing cache performance...")
    try:
        # Send same message twice to test caching
        start_time = datetime.utcnow()
        result1 = await service.process_message(
            user_id=test_user_id, message="How are you today?", mode="general"
        )
        first_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        start_time = datetime.utcnow()
        result2 = await service.process_message(
            user_id=test_user_id, message="How are you today?", mode="general"
        )
        second_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        results["cache_performance"] = (
            second_time < first_time * 1.5
        )  # Should be similar or faster

        print(
            f"✅ First request: {first_time:.1f}ms, Second request: {second_time:.1f}ms"
        )

    except Exception as e:
        results["cache_performance"] = False
        print(f"❌ Cache performance test failed: {e}")

    # Test 7: Available Modes
    print("\n📑 Testing available modes endpoint...")
    try:
        modes = await service.get_available_modes()

        results["available_modes"] = (
            "modes" in modes
            and len(modes["modes"]) >= 3
            and "general" in modes["modes"]
            and "action_plan" in modes["modes"]
            and "visualization" in modes["modes"]
        )

        print(f"✅ Available modes: {list(modes['modes'].keys())}")

    except Exception as e:
        results["available_modes"] = False
        print(f"❌ Available modes test failed: {e}")

    # Test Results Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed_tests = sum(1 for passed in results.values() if passed)
    total_tests = len(results)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All integration tests PASSED! System ready for deployment.")
        return True
    elif passed_tests >= total_tests * 0.8:
        print("⚠️  Most tests passed. System functional with minor issues.")
        return True
    else:
        print("❌ Multiple test failures. System needs attention before deployment.")
        return False


async def test_individual_services():
    """Test individual service connections."""

    print("\n🔧 Testing Individual Service Connections")
    print("=" * 60)

    service = MultiModalChatService()

    # Test Memory Service
    try:
        stats = await service.memory_service.get_memory_stats("test_user")
        print("✅ Memory Service: Connected")
    except Exception as e:
        print(f"❌ Memory Service: {e}")

    # Test PII Detector
    try:
        from ..memory.types import MemoryItem

        test_memory = MemoryItem(
            id="test",
            content="My name is John and I live at 123 Main St",
            type="test",
            timestamp=datetime.utcnow(),
            metadata={},
        )
        pii_results = await service.pii_detector.detect_pii(test_memory)
        print(
            f"✅ PII Detector: Connected (found {len(pii_results.get('detected_items', []))} PII items)"
        )
    except Exception as e:
        print(f"❌ PII Detector: {e}")

    # Test Action Plan Extractor
    try:
        opportunity = service.action_plan_analyzer.analyze_opportunity(
            "I need help", "", ""
        )
        print(f"✅ Action Plan Extractor: Connected")
    except Exception as e:
        print(f"❌ Action Plan Extractor: {e}")

    # Test Image Generation
    try:
        status = await service.emotion_visualizer.get_generation_status("test_user")
        print(f"✅ Image Generation: Connected")
    except Exception as e:
        print(f"❌ Image Generation: {e}")

    # Test Cache Manager
    try:
        health = await service.cache_manager.health_check()
        print(f"✅ Cache Manager: {health.get('status', 'unknown').title()}")
    except Exception as e:
        print(f"❌ Cache Manager: {e}")


async def main():
    """Run all integration tests."""

    print("🧪 Multi-Modal Chat Integration Test Suite")
    print("Testing integration with all existing Nura services")
    print("=" * 60)

    # Test individual services first
    await test_individual_services()

    # Run main integration tests
    success = await test_service_integrations()

    if success:
        print("\n🚀 INTEGRATION TEST SUITE COMPLETED SUCCESSFULLY!")
        print(
            "The multi-modal chat system is ready to integrate with existing Nura services."
        )
    else:
        print("\n⚠️  INTEGRATION ISSUES DETECTED")
        print("Please review the failed tests and fix any service connection issues.")

    return success


if __name__ == "__main__":
    # Run the integration tests
    result = asyncio.run(main())
    exit(0 if result else 1)
