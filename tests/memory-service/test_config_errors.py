#!/usr/bin/env python3
"""
Test script to demonstrate configuration error handling.

This script shows how the Memory Service behaves when environment variables are missing.
"""

import os
import sys
from datetime import datetime


def test_configuration_errors():
    """Test configuration error handling by temporarily removing env vars."""

    print("🧪 Testing Configuration Error Handling")
    print("=" * 50)
    print(f"Test started at: {datetime.utcnow()}")
    print()

    # Save original environment variables
    original_env = {}
    test_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_API_KEY",
        "MENTAL_HEALTH_SYSTEM_PROMPT",
        "CONVERSATION_GUIDELINES",
        "CRISIS_DETECTION_PROMPT",
    ]

    for var in test_vars:
        original_env[var] = os.environ.get(var)

    print("📋 Current environment status:")
    for var in test_vars:
        status = "✅ SET" if os.environ.get(var) else "❌ NOT SET"
        print(f"  {var}: {status}")
    print()

    # Test 1: Configuration check with proper setup
    print("🧪 Test 1: Normal Configuration Check")
    try:
        from ..config import Config

        Config.validate()
        Config.check_optional_config()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
    print()

    # Test 2: Remove required variables and test
    print("🧪 Test 2: Testing with Missing Required Variables")
    print("Temporarily removing GOOGLE_API_KEY...")

    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

    try:
        from ..config import Config

        # Force reload of config
        import importlib
        import sys

        if "src.services.memory.config" in sys.modules:
            importlib.reload(sys.modules["src.services.memory.config"])

        Config.validate()
        print("❌ This should have failed!")
    except ValueError as e:
        print(f"✅ Expected error caught: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    print()

    # Test 3: Test assistant with missing prompts
    print("🧪 Test 3: Testing Assistant with Missing Prompts")
    print("Temporarily removing MENTAL_HEALTH_SYSTEM_PROMPT...")

    if "MENTAL_HEALTH_SYSTEM_PROMPT" in os.environ:
        del os.environ["MENTAL_HEALTH_SYSTEM_PROMPT"]

    try:
        from ..assistant.mental_health_assistant import MentalHealthAssistant

        assistant = MentalHealthAssistant()

        # Check if fallback prompt contains error message
        if "CONFIGURATION ERROR" in assistant.system_prompt:
            print("✅ Assistant correctly using error fallback prompt")
            print(f"Fallback prompt preview: {assistant.system_prompt[:100]}...")
        else:
            print("❌ Assistant not showing configuration error")
    except Exception as e:
        print(f"❌ Error creating assistant: {e}")
    print()

    # Restore environment variables
    print("🔄 Restoring original environment...")
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]

    print("✅ Environment restored")
    print()

    # Test 4: API configuration status
    print("🧪 Test 4: Testing API Configuration Status")
    try:
        from ..api import get_configuration_status

        status = get_configuration_status()
        print(f"Configuration status: {status['status']}")
        print(f"Has issues: {status['has_configuration_issues']}")
        print(f"Message: {status['message']}")

        if status["missing_required"]:
            print(f"Missing required: {status['missing_required']}")
        if status["missing_optional"]:
            print(f"Missing optional: {status['missing_optional']}")

    except Exception as e:
        print(f"❌ Error testing API status: {e}")

    print()
    print("🏁 Configuration error testing completed")
    print("=" * 50)


if __name__ == "__main__":
    test_configuration_errors()
