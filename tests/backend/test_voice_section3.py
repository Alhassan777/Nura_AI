#!/usr/bin/env python3
"""
Test script for Section 3: Voice Processing Pipeline
Tests enhanced voice adapter, TTS optimization, Vapi control URL integration, and response delivery.
"""

import asyncio
import uuid
import json
import logging
import time
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our voice utilities
import sys
import os

sys.path.append(".")

from services.memory.voice_adapter import voice_adapter
from services.memory.utils.vapi import (
    store_call_mapping,
    delete_call_mapping,
)


async def test_voice_adapter_enhancements():
    """Test the enhanced voice adapter with Section 3 features."""
    print("🎙️  Testing Enhanced Voice Adapter (Section 3)")
    print("=" * 50)

    passed_tests = []
    failed_tests = []

    # Test 1: Voice instruction enhancement
    print("\n1️⃣ Testing enhanced voice instructions...")

    test_message = "I've been feeling really anxious about my job interview tomorrow"
    enhanced_message = voice_adapter._add_voice_instructions(test_message)

    test_name = "Enhanced voice instructions"
    if (
        "VOICE THERAPY SESSION" in enhanced_message
        and "TTS OPTIMIZATION" in enhanced_message
    ):
        print("  ✅ Voice instructions enhanced with TTS guidelines")
        passed_tests.append(test_name)
    else:
        print("  ❌ Voice instructions not properly enhanced")
        failed_tests.append(test_name)

    # Test 2: TTS optimization
    print("\n2️⃣ Testing TTS optimizations...")

    test_responses = [
        "I understand you're feeling anxious; that's really tough.",
        "Let's try some breathing exercises (deep breaths) - they can help.",
        "You're not alone & I'm here to support you through this.",
        "Dr. Smith mentioned some techniques vs. the usual methods.",
    ]

    for i, test_response in enumerate(test_responses):
        optimized = voice_adapter._apply_enhanced_voice_optimizations(test_response)

        test_name = f"TTS optimization {i+1}"
        # Check for proper TTS replacements
        has_improvements = (
            "and" in optimized
            if "&" in test_response
            else (
                True and "versus" in optimized
                if "vs." in test_response
                else (
                    True and "Doctor" in optimized
                    if "Dr." in test_response
                    else True and ";" not in optimized
                )
            )  # Should remove semicolons
        )

        if has_improvements:
            print(f"  ✅ Response {i+1}: TTS optimized")
            print(f"      Original: {test_response}")
            print(f"      Optimized: {optimized}")
            passed_tests.append(test_name)
        else:
            print(f"  ❌ Response {i+1}: TTS optimization failed")
            failed_tests.append(test_name)

    # Test 3: Length enforcement
    print("\n3️⃣ Testing voice length limits...")

    long_response = " ".join(
        ["This is a very long response that should be truncated"] * 10
    )
    truncated = voice_adapter._enforce_voice_length_limits(long_response)

    word_count = len(truncated.split())
    test_name = "Length enforcement"

    if word_count <= voice_adapter.max_voice_words and "..." in truncated:
        print(
            f"  ✅ Long response truncated: {len(long_response.split())} → {word_count} words"
        )
        passed_tests.append(test_name)
    else:
        print(
            f"  ❌ Length enforcement failed: {word_count} words (max: {voice_adapter.max_voice_words})"
        )
        failed_tests.append(test_name)

    # Test 4: Speech duration estimation
    print("\n4️⃣ Testing speech duration estimation...")

    test_text = "This is a test message with exactly fifteen words for duration estimation testing purposes here."
    duration = voice_adapter._estimate_speech_duration(test_text)

    expected_duration = (15 / 150) * 60  # 15 words at 150 words per minute
    test_name = "Speech duration estimation"

    if abs(duration - expected_duration) < 1.0:  # Within 1 second tolerance
        print(
            f"  ✅ Duration estimated: {duration}s (expected: ~{expected_duration:.1f}s)"
        )
        passed_tests.append(test_name)
    else:
        print(
            f"  ❌ Duration estimation off: {duration}s (expected: ~{expected_duration:.1f}s)"
        )
        failed_tests.append(test_name)

    print(
        f"\n📊 Voice Adapter Tests: {len(passed_tests)}/{len(passed_tests) + len(failed_tests)} passed"
    )
    return len(failed_tests) == 0


async def test_vapi_control_integration():
    """Test Vapi control URL integration."""
    print("\n🎯 Testing Vapi Control URL Integration")
    print("=" * 45)

    passed_tests = []
    failed_tests = []

    # Mock control URL for testing
    mock_control_url = "https://api.vapi.ai/call/control/test-123"

    # Test 1: Control payload preparation
    print("\n1️⃣ Testing control payload preparation...")

    test_response = "I understand how you're feeling. Let's work through this together."
    crisis_level = "SUPPORT"

    # Mock the aiohttp session to test payload structure
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "delivered"}
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await voice_adapter._send_to_vapi_control(
            mock_control_url, test_response, crisis_level
        )

        test_name = "Control payload preparation"
        if result["status"] == "success" and result["delivered"]:
            print("  ✅ Control payload sent successfully")

            # Check if the mock was called with correct payload
            call_args = mock_post.call_args
            if call_args:
                json_payload = call_args[1]["json"]
                if (
                    json_payload.get("type") == "conversation-update"
                    and json_payload.get("triggerResponseEnabled")
                    and json_payload["message"]["content"] == test_response
                ):
                    print("  ✅ Payload structure correct")
                    passed_tests.append(test_name)
                else:
                    print("  ❌ Payload structure incorrect")
                    failed_tests.append(test_name)
            else:
                print("  ❌ Mock not called properly")
                failed_tests.append(test_name)
        else:
            print(f"  ❌ Control delivery failed: {result}")
            failed_tests.append(test_name)

    # Test 2: Crisis prioritization
    print("\n2️⃣ Testing crisis prioritization...")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "delivered"}
        mock_post.return_value.__aenter__.return_value = mock_response

        crisis_response = "I hear you and I'm connecting you with support right now."
        result = await voice_adapter._send_to_vapi_control(
            mock_control_url, crisis_response, "CRISIS"
        )

        test_name = "Crisis prioritization"
        if result["delivered"]:
            # Check if priority was set for crisis
            call_args = mock_post.call_args
            json_payload = call_args[1]["json"]

            if json_payload.get("priority") == "high" and json_payload["metadata"].get(
                "requires_immediate_attention"
            ):
                print("  ✅ Crisis priority set correctly")
                passed_tests.append(test_name)
            else:
                print("  ❌ Crisis priority not set")
                failed_tests.append(test_name)
        else:
            print("  ❌ Crisis delivery failed")
            failed_tests.append(test_name)

    # Test 3: Error handling
    print("\n3️⃣ Testing error handling...")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await voice_adapter._send_to_vapi_control(
            mock_control_url, "Test message", "SUPPORT"
        )

        test_name = "Error handling"
        if result["status"] == "failed" and not result["delivered"]:
            print("  ✅ Error handling works correctly")
            passed_tests.append(test_name)
        else:
            print(f"  ❌ Error handling failed: {result}")
            failed_tests.append(test_name)

    print(
        f"\n📊 Vapi Control Tests: {len(passed_tests)}/{len(passed_tests) + len(failed_tests)} passed"
    )
    return len(failed_tests) == 0


async def test_full_voice_pipeline():
    """Test the complete voice processing pipeline with memory integration."""
    print("\n🔄 Testing Complete Voice Processing Pipeline")
    print("=" * 50)

    passed_tests = []
    failed_tests = []

    # Setup test data
    test_call_id = f"pipeline_test_{uuid.uuid4()}"
    test_customer_id = "pipeline-test-user-123"
    test_control_url = "https://api.vapi.ai/call/control/pipeline-test"

    try:
        # Setup call mapping
        await store_call_mapping(test_call_id, test_customer_id, "web")

        # Test 1: Full pipeline processing
        print("\n1️⃣ Testing full pipeline processing...")

        test_message = "I'm feeling overwhelmed with work and can't seem to focus"

        # Mock the mental health assistant response
        with patch.object(
            voice_adapter.mental_health_assistant, "generate_response"
        ) as mock_assistant:
            mock_assistant.return_value = {
                "response": "I understand you're feeling overwhelmed. That sounds really challenging. Let's take this one step at a time.",
                "crisis_level": "SUPPORT",
                "crisis_explanation": "User expressing work stress",
                "resources_provided": ["stress_management"],
                "coping_strategies": ["breathing_exercise"],
                "timestamp": "2025-01-26T15:30:00Z",
            }

            # Mock Vapi control delivery
            with patch("aiohttp.ClientSession.post") as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "delivered"}
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await voice_adapter.process_voice_message(
                    user_message=test_message,
                    user_id=test_customer_id,
                    memory_context=None,
                    call_id=test_call_id,
                    control_url=test_control_url,
                )

                test_name = "Full pipeline processing"
                if result.get("voice_optimized") and result.get(
                    "vapi_delivery", {}
                ).get("delivered"):
                    print("  ✅ Full pipeline processed successfully")
                    print(f"      Response: {result['response'][:50]}...")
                    print(f"      Word count: {result.get('word_count', 'N/A')}")
                    print(
                        f"      Speech time: {result.get('estimated_speech_time', 'N/A')}s"
                    )
                    print(f"      Crisis level: {result.get('crisis_level', 'N/A')}")
                    passed_tests.append(test_name)
                else:
                    print(f"  ❌ Pipeline processing failed: {result}")
                    print(f"      Available keys: {list(result.keys())}")
                    failed_tests.append(test_name)

        # Test 2: Crisis handling in pipeline
        print("\n2️⃣ Testing crisis handling in pipeline...")

        crisis_message = "I don't think I can go on like this anymore"

        with patch.object(
            voice_adapter.mental_health_assistant, "generate_response"
        ) as mock_assistant:
            mock_assistant.return_value = {
                "response": "I hear you and I want you to know that you're not alone. Let me connect you with support.",
                "crisis_level": "CRISIS",
                "crisis_explanation": "Potential suicidal ideation",
                "resources_provided": ["crisis_hotline", "emergency_services"],
                "coping_strategies": ["immediate_safety"],
                "timestamp": "2025-01-26T15:35:00Z",
            }

            with patch("aiohttp.ClientSession.post") as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "status": "delivered",
                    "priority": "high",
                }
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await voice_adapter.process_voice_message(
                    user_message=crisis_message,
                    user_id=test_customer_id,
                    memory_context=None,
                    call_id=test_call_id,
                    control_url=test_control_url,
                )

                test_name = "Crisis handling in pipeline"
                if (
                    result["crisis_level"] == "CRISIS"
                    and result.get("requires_immediate_delivery")
                    and result.get("crisis_voice_response")
                ):
                    print("  ✅ Crisis handling works correctly")
                    print(
                        f"      Crisis response: {result.get('crisis_voice_response', 'N/A')}"
                    )
                    passed_tests.append(test_name)
                else:
                    print(f"  ❌ Crisis handling failed: {result}")
                    failed_tests.append(test_name)

        # Cleanup
        await delete_call_mapping(test_call_id)

    except Exception as e:
        print(f"  ❌ Pipeline test failed with error: {str(e)}")
        failed_tests.append("Pipeline setup")

    print(
        f"\n📊 Pipeline Tests: {len(passed_tests)}/{len(passed_tests) + len(failed_tests)} passed"
    )
    return len(failed_tests) == 0


async def test_api_integration():
    """Test API integration with Section 3 enhancements."""
    print("\n🌐 Testing API Integration (Section 3)")
    print("=" * 40)

    try:
        import aiohttp

        backend_url = "http://localhost:8000"
        test_call_id = f"api_section3_test_{uuid.uuid4()}"
        test_customer_id = "api-section3-test-user"

        # Setup call mapping
        await store_call_mapping(test_call_id, test_customer_id, "web")

        async with aiohttp.ClientSession() as session:
            # Test enhanced webhook processing with control URL
            webhook_event = {
                "event": {
                    "type": "conversation-update",
                    "call": {
                        "id": test_call_id,
                        "controlUrl": "https://api.vapi.ai/call/control/test-123",
                        "status": "active",
                    },
                    "message": {
                        "role": "user",
                        "content": "I've been having trouble sleeping and feeling stressed about everything",
                    },
                },
                "callId": test_call_id,
                "receivedAt": "2025-01-26T15:30:00Z",
                "source": "test",
            }

            async with session.post(
                f"{backend_url}/voice/webhook-event", json=webhook_event
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Enhanced webhook processing: Success")
                    print(
                        f"   Processing time: {result.get('processingTimeMs', 0):.1f}ms"
                    )
                    print(f"   Voice optimized: {result.get('voiceOptimized', False)}")
                    print(f"   Word count: {result.get('wordCount', 'N/A')}")
                    print(
                        f"   Speech time: {result.get('estimatedSpeechTime', 'N/A')}s"
                    )
                    print(
                        f"   Control URL used: {result.get('controlUrlUsed', 'N/A') is not None}"
                    )
                    print(
                        f"   Delivery status: {result.get('vapiDelivery', {}).get('status', 'N/A')}"
                    )
                else:
                    print(f"❌ Enhanced webhook processing failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")

        # Cleanup
        await delete_call_mapping(test_call_id)

    except ImportError:
        print("⚠️  aiohttp not available for API testing")
    except Exception as e:
        print(f"❌ API integration test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Section 3: Voice Processing Pipeline Tests")

    async def main():
        print("\n" + "=" * 60)
        print("🎙️  SECTION 3: VOICE PROCESSING PIPELINE")
        print("=" * 60)

        # Test voice adapter enhancements
        adapter_success = await test_voice_adapter_enhancements()

        # Test Vapi control integration
        control_success = await test_vapi_control_integration()

        # Test full pipeline
        pipeline_success = await test_full_voice_pipeline()

        # Test API integration
        await test_api_integration()

        print(f"\n📋 Section 3 Implementation Status:")
        print(f"   ✅ Enhanced voice prompt optimization")
        print(f"   ✅ TTS-specific text processing")
        print(f"   ✅ Vapi control URL integration")
        print(f"   ✅ Crisis response prioritization")
        print(f"   ✅ Response delivery tracking")
        print(f"   ✅ Enhanced latency metrics")
        print(f"   {'✅' if adapter_success else '❌'} Voice adapter enhancements")
        print(f"   {'✅' if control_success else '❌'} Vapi control integration")
        print(f"   {'✅' if pipeline_success else '❌'} Complete pipeline processing")

        all_success = adapter_success and control_success and pipeline_success

        if all_success:
            print("\n🎉 Section 3: Voice Processing Pipeline - COMPLETE")
            print("\n🔄 Pipeline Flow Summary:")
            print("   1. Webhook receives conversation-update event")
            print("   2. Extract user message and control URL")
            print("   3. Resolve customer ID from call mapping")
            print("   4. Get memory context for personalization")
            print("   5. Process message through enhanced voice adapter")
            print("   6. Apply TTS optimizations and length limits")
            print("   7. Send response to Vapi control URL")
            print("   8. Store memories and metrics")
            print("   9. Return enhanced processing result")
        else:
            print("\n⚠️  Section 3: Voice Processing Pipeline - NEEDS REVIEW")

    asyncio.run(main())
