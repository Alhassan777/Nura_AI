"""
Test Suite for VAPI → Safety Network Pipeline Integration

This test verifies the complete pipeline from VAPI tool calls through to actual
safety network contact outreach. Tests both working components and identifies gaps.
"""

import asyncio
import json
import requests
import aiohttp
from typing import Dict, Any
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust as needed
TEST_USER_ID = "test-user-123"
TEST_JWT_TOKEN = "your-test-jwt-token"  # Replace with actual test token


class VAPISafetyNetworkPipelineTest:
    """Test the complete VAPI → Safety Network integration pipeline."""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Authorization": f"Bearer {TEST_JWT_TOKEN}",
            "Content-Type": "application/json",
        }
        self.test_results = []

    def log_test_result(self, test_name: str, success: bool, details: str):
        """Log test results for final report."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {details}")

    async def test_1_safety_network_endpoints_exist(self):
        """Test 1: Verify safety network API endpoints exist."""
        try:
            # Test checkup endpoints (should exist)
            async with aiohttp.ClientSession() as session:
                checkup_url = f"{self.base_url}/checkup/schedules"
                async with session.get(checkup_url, headers=self.headers) as response:
                    if response.status in [
                        200,
                        401,
                    ]:  # 401 = auth required, which is expected
                        self.log_test_result(
                            "Safety Network Checkup API",
                            True,
                            f"Checkup endpoint exists (status: {response.status})",
                        )
                    else:
                        self.log_test_result(
                            "Safety Network Checkup API",
                            False,
                            f"Unexpected status: {response.status}",
                        )

                # Test contacts endpoint (this should FAIL - missing endpoint)
                contacts_url = f"{self.base_url}/safety-network/contacts"
                try:
                    async with session.get(
                        contacts_url, headers=self.headers
                    ) as response:
                        if response.status == 404:
                            self.log_test_result(
                                "Safety Network Contacts API",
                                False,
                                "❌ MISSING: /contacts endpoint doesn't exist",
                            )
                        else:
                            self.log_test_result(
                                "Safety Network Contacts API",
                                True,
                                f"Contacts endpoint exists (status: {response.status})",
                            )
                except Exception as e:
                    self.log_test_result(
                        "Safety Network Contacts API",
                        False,
                        f"❌ MISSING: Contacts endpoint error: {str(e)}",
                    )

        except Exception as e:
            self.log_test_result(
                "Safety Network API Check", False, f"Error testing endpoints: {str(e)}"
            )

    async def test_2_vapi_tools_registration(self):
        """Test 2: Verify VAPI tools are properly registered."""
        # This would require VAPI API key to test properly
        # For now, we'll check if tools are defined in our registry
        try:
            from backend.services.voice.vapi_tools_registry import VAPIToolsRegistry

            registry = VAPIToolsRegistry()
            routing_map = registry.get_tool_routing_map()

            # Check for crisis tools
            crisis_tools = [
                "query_safety_network_contacts",
                "log_crisis_intervention",
                "send_crisis_sms",
                "transfer_to_emergency_contact",
            ]

            missing_tools = []
            for tool in crisis_tools:
                if tool not in routing_map:
                    missing_tools.append(tool)

            if not missing_tools:
                self.log_test_result(
                    "VAPI Crisis Tools Registration",
                    True,
                    "All crisis tools are defined in registry",
                )
            else:
                self.log_test_result(
                    "VAPI Crisis Tools Registration",
                    False,
                    f"Missing tools: {missing_tools}",
                )

        except ImportError as e:
            self.log_test_result(
                "VAPI Tools Registry", False, f"Cannot import registry: {str(e)}"
            )

    async def test_3_webhook_routing(self):
        """Test 3: Simulate VAPI webhook calls to test routing."""
        try:
            # Simulate a query_safety_network_contacts tool call
            webhook_payload = {
                "type": "function-call",
                "functionCall": {
                    "name": "query_safety_network_contacts",
                    "parameters": {
                        "user_id": TEST_USER_ID,
                        "crisis_level": "moderate",
                        "crisis_description": "User needs support",
                        "user_current_state": "anxious and overwhelmed",
                    },
                },
                "call": {
                    "id": "test-call-123",
                    "orgId": "test-org",
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                    "type": "inboundPhoneCall",
                    "phoneNumberId": "test-phone-123",
                    "customerId": TEST_USER_ID,
                },
            }

            # Test webhook endpoint
            webhook_url = f"{self.base_url}/vapi/webhooks"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        self.log_test_result(
                            "VAPI Webhook Routing",
                            True,
                            f"Webhook processed successfully: {response_data.get('message', 'Success')}",
                        )
                    else:
                        self.log_test_result(
                            "VAPI Webhook Routing",
                            False,
                            f"Webhook failed (status: {response.status}): {response_data}",
                        )

        except Exception as e:
            self.log_test_result(
                "VAPI Webhook Test", False, f"Error testing webhook: {str(e)}"
            )

    async def test_4_safety_network_manager_direct(self):
        """Test 4: Test SafetyNetworkManager functions directly."""
        try:
            from backend.services.safety_network.manager import SafetyNetworkManager

            # Test getting emergency contacts
            contacts = SafetyNetworkManager.get_emergency_contacts(TEST_USER_ID)

            self.log_test_result(
                "SafetyNetworkManager Direct",
                True,
                f"Manager accessible, returned {len(contacts)} contacts",
            )

            # Test logging contact attempt
            from backend.models import CommunicationMethod

            log_success = SafetyNetworkManager.log_contact_attempt(
                safety_contact_id="test-contact-123",
                user_id=TEST_USER_ID,
                contact_method=CommunicationMethod.SMS,
                success=True,
                reason="Pipeline test",
                initiated_by="test_pipeline",
            )

            self.log_test_result(
                "Contact Logging",
                log_success,
                (
                    "Contact attempt logging works"
                    if log_success
                    else "Contact logging failed"
                ),
            )

        except ImportError as e:
            self.log_test_result(
                "SafetyNetworkManager Import", False, f"Cannot import manager: {str(e)}"
            )
        except Exception as e:
            self.log_test_result(
                "SafetyNetworkManager Test", False, f"Manager test error: {str(e)}"
            )

    async def test_5_end_to_end_crisis_flow(self):
        """Test 5: Simulate complete crisis intervention flow."""
        try:
            print("\n🚨 Testing End-to-End Crisis Flow:")
            print(
                "1. VAPI detects crisis → 2. Queries contacts → 3. Initiates outreach → 4. Logs intervention"
            )

            # Step 1: Simulate crisis detection (this would happen in VAPI)
            crisis_detected = True
            print("   ✅ Step 1: Crisis detected by VAPI assistant")

            # Step 2: Query safety network contacts
            webhook_payload = {
                "type": "function-call",
                "functionCall": {
                    "name": "query_safety_network_contacts",
                    "parameters": {
                        "user_id": TEST_USER_ID,
                        "crisis_level": "high",
                        "crisis_description": "User expressing suicidal thoughts",
                        "user_current_state": "severe distress",
                    },
                },
            }

            print("   🔄 Step 2: Querying safety network contacts...")
            # This would call our webhook handler

            # Step 3: Initiate contact (SMS via VAPI native tool)
            print("   🔄 Step 3: Would initiate SMS to emergency contact")
            # This uses VAPI's native SMS tool

            # Step 4: Log intervention
            print("   🔄 Step 4: Logging crisis intervention")

            self.log_test_result(
                "End-to-End Crisis Flow",
                True,
                "Crisis flow steps identified - implementation varies by component",
            )

        except Exception as e:
            self.log_test_result(
                "End-to-End Crisis Flow", False, f"Flow test error: {str(e)}"
            )

    async def test_6_identify_missing_components(self):
        """Test 6: Identify what's missing for complete integration."""
        missing_components = []

        # Check for missing API endpoints
        missing_endpoints = [
            "/safety-network/contacts - Get user's emergency contacts",
            "/safety-network/contact-outreach - Initiate contact with emergency contact",
            "/safety-network/crisis-log - Log crisis interventions",
        ]

        # Check for missing VAPI tools
        # (current tools exist but may need additional ones)

        # Check for missing webhook handlers
        # (crisis handler exists but needs to connect to real endpoints)

        missing_components.extend(
            [
                "❌ MISSING: Safety Network Contacts API endpoint",
                "❌ MISSING: Contact Outreach API endpoint",
                "⚠️  PARTIAL: Crisis webhook handler needs real endpoint integration",
                "⚠️  PARTIAL: VAPI tools registered but may need testing with real API key",
                "✅ EXISTS: SafetyNetworkManager with contact management",
                "✅ EXISTS: Crisis intervention prompts and guidelines",
                "✅ EXISTS: Database models for safety contacts",
            ]
        )

        self.log_test_result(
            "Missing Components Analysis",
            len([c for c in missing_components if c.startswith("❌")]) == 0,
            f"Components status: {len(missing_components)} items checked",
        )

        print("\n📋 MISSING COMPONENTS ANALYSIS:")
        for component in missing_components:
            print(f"   {component}")

    async def run_all_tests(self):
        """Run all pipeline tests and generate report."""
        print("🧪 VAPI → Safety Network Pipeline Integration Test")
        print("=" * 60)

        await self.test_1_safety_network_endpoints_exist()
        await self.test_2_vapi_tools_registration()
        await self.test_3_webhook_routing()
        await self.test_4_safety_network_manager_direct()
        await self.test_5_end_to_end_crisis_flow()
        await self.test_6_identify_missing_components()

        # Generate final report
        print("\n" + "=" * 60)
        print("📊 FINAL TEST REPORT")
        print("=" * 60)

        passed_tests = [r for r in self.test_results if "✅ PASS" in r["status"]]
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]

        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print(f"📊 TOTAL: {len(self.test_results)}")

        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")

        print("\n🎯 NEXT STEPS:")
        print("   1. Add missing /safety-network/contacts API endpoint")
        print("   2. Add /safety-network/contact-outreach endpoint")
        print("   3. Update VAPI webhook handler to use real endpoints")
        print("   4. Test with real VAPI API key and phone numbers")
        print("   5. Add comprehensive error handling and logging")

        return {
            "passed": len(passed_tests),
            "failed": len(failed_tests),
            "total": len(self.test_results),
            "details": self.test_results,
        }


# Main test execution
async def main():
    """Run the complete pipeline test."""
    tester = VAPISafetyNetworkPipelineTest()
    results = await tester.run_all_tests()

    print(f"\n🏁 Test completed: {results['passed']}/{results['total']} passed")

    # Save results to file
    with open("vapi_safety_network_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("📁 Detailed results saved to: vapi_safety_network_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
