#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


async def test_api():
    print("=== Testing API Components ===")

    try:
        from services.memory.api import app, memory_service, mental_health_assistant

        print("✅ API components imported successfully")

        # Test memory service
        print("\n=== Testing Memory Service ===")
        result = await memory_service.process_memory(
            user_id="test-user-123", content="I'm feeling anxious today", type="chat"
        )
        print(f"✅ Memory service test: {result}")

        # Test mental health assistant
        print("\n=== Testing Mental Health Assistant ===")
        response = await mental_health_assistant.generate_response(
            user_message="I'm feeling anxious today",
            memory_context=None,
            user_id="test-user-123",
        )
        print(f"✅ Mental health assistant test: {response}")

    except Exception as e:
        print(f"❌ API test error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api())
