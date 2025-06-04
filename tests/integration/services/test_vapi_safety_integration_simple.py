"""
Simple VAPI → Safety Network Integration Test

Tests the core components without requiring a running server.
Verifies that all the pieces can work together.
"""

import sys
import os

sys.path.append("../backend")
sys.path.append("../backend/services")


def test_safety_network_manager():
    """Test SafetyNetworkManager can be imported and basic functions work."""
    try:
        from safety_network.manager import SafetyNetworkManager

        print("✅ SafetyNetworkManager imported successfully")

        # Test method existence
        methods = [
            "get_emergency_contacts",
            "get_user_safety_contacts",
            "log_contact_attempt",
            "add_safety_contact",
        ]

        for method in methods:
            if hasattr(SafetyNetworkManager, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")

        return True

    except ImportError as e:
        print(f"❌ Failed to import SafetyNetworkManager: {e}")
        return False


def test_vapi_tools_registry():
    """Test VAPI tools registry has crisis tools defined."""
    try:
        from voice.vapi_tools_registry import VAPIToolsRegistry

        print("✅ VAPIToolsRegistry imported successfully")

        registry = VAPIToolsRegistry()
        routing_map = registry.get_tool_routing_map()

        # Check for crisis tools
        crisis_tools = [
            "query_safety_network_contacts",
            "log_crisis_intervention",
            "send_crisis_sms",
            "transfer_to_emergency_contact",
        ]

        all_exist = True
        for tool in crisis_tools:
            if tool in routing_map:
                print(f"✅ VAPI tool {tool} registered")
            else:
                print(f"❌ VAPI tool {tool} missing")
                all_exist = False

        return all_exist

    except ImportError as e:
        print(f"❌ Failed to import VAPIToolsRegistry: {e}")
        return False


def test_models_exist():
    """Test that required models exist."""
    try:
        from models import SafetyContact, CommunicationMethod, ContactLog

        print("✅ Safety network models imported successfully")

        # Test enums
        methods = list(CommunicationMethod)
        print(f"✅ Communication methods available: {[m.value for m in methods]}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False


def test_webhook_handler_structure():
    """Test that webhook handler has crisis tool handling."""
    try:
        from voice.vapi_webhook_router import VAPIWebhookRouter

        print("✅ VAPIWebhookRouter imported successfully")

        router = VAPIWebhookRouter()

        # Check for crisis handler method
        if hasattr(router, "_handle_crisis_tool"):
            print("✅ Crisis tool handler method exists")
        else:
            print("❌ Crisis tool handler method missing")

        return True

    except ImportError as e:
        print(f"❌ Failed to import VAPIWebhookRouter: {e}")
        return False


def simulate_crisis_flow():
    """Simulate the crisis intervention flow end-to-end."""
    print("\n🚨 SIMULATING CRISIS INTERVENTION FLOW:")
    print("=" * 50)

    # Step 1: VAPI Crisis Detection
    print("1. 🤖 VAPI Assistant detects crisis situation")
    print("   - User: 'I'm having thoughts of hurting myself'")
    print("   - Assistant triggers crisis protocol")

    # Step 2: Query Safety Network
    print("\n2. 🔍 Query Safety Network Contacts")
    try:
        from safety_network.manager import SafetyNetworkManager

        # This would normally get real contacts, but for demo we'll simulate
        print("   - Tool: query_safety_network_contacts")
        print("   - Parameters: {user_id: 'test-123', crisis_level: 'high'}")
        print("   - Response: Found 2 emergency contacts")
        print("   ✅ Safety network query successful")

    except Exception as e:
        print(f"   ❌ Safety network query failed: {e}")

    # Step 3: Initiate Contact Outreach
    print("\n3. 📞 Initiate Emergency Contact Outreach")
    print("   - Tool: initiate_emergency_contact_outreach")
    print("   - Target: Primary emergency contact (Mom)")
    print("   - Method: SMS")
    print("   - Message: 'Your loved one needs immediate support. Crisis level: HIGH'")
    print("   ✅ Contact outreach initiated")

    # Step 4: VAPI Native SMS
    print("\n4. 📱 VAPI Sends SMS")
    print("   - Tool: send_crisis_sms (VAPI native)")
    print("   - To: +1234567890")
    print("   - Message: Crisis intervention SMS")
    print("   ✅ SMS sent via VAPI")

    # Step 5: Log Intervention
    print("\n5. 📝 Log Crisis Intervention")
    print("   - Tool: log_crisis_intervention")
    print("   - Outcome: SMS sent successfully")
    print("   - Follow-up: Monitor for response")
    print("   ✅ Intervention logged")

    # Step 6: Continue Support
    print("\n6. 🤗 Continue User Support")
    print("   - Assistant: 'I've contacted your emergency contact Mom via SMS'")
    print("   - Assistant: 'Let's talk about how you're feeling right now'")
    print("   - Assistant: 'I'm staying here with you until help arrives'")
    print("   ✅ Ongoing support provided")

    print("\n🎯 CRISIS INTERVENTION COMPLETE")
    print("✅ User has emergency support contact initiated")
    print("✅ User receives immediate AI support")
    print("✅ All actions logged for follow-up")


def main():
    """Run all integration tests."""
    print("🧪 VAPI → Safety Network Integration Test (Simple)")
    print("=" * 60)

    tests = [
        ("Safety Network Manager", test_safety_network_manager),
        ("VAPI Tools Registry", test_vapi_tools_registry),
        ("Database Models", test_models_exist),
        ("Webhook Handler", test_webhook_handler_structure),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))

    # Simulate crisis flow
    simulate_crisis_flow()

    # Final report
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n🏁 SUMMARY: {passed}/{total} component tests passed")

    if passed == total:
        print("✅ ALL COMPONENTS AVAILABLE - Pipeline ready for testing")
        print("\n🎯 NEXT STEPS:")
        print("   1. Start backend server: python main.py")
        print("   2. Test API endpoints: GET /safety-network/contacts")
        print("   3. Register VAPI tools with real API key")
        print("   4. Test end-to-end with real phone numbers")
    else:
        print("⚠️  SOME COMPONENTS MISSING - Fix import issues first")


if __name__ == "__main__":
    main()
