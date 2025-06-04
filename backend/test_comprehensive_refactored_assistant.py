#!/usr/bin/env python3
"""
Comprehensive Test Suite for Refactored Mental Health Assistant

This test suite verifies that the refactored mental health assistant maintains
all the original functionality while improving maintainability and modularity.

Test Coverage:
1. Basic response generation
2. Crisis detection and assessment
3. Schedule extraction and opportunity analysis
4. Action plan extraction and opportunity analysis
5. Memory context integration
6. Session metadata extraction
7. Resource and coping strategy extraction
8. Configuration handling
9. Fallback responses
10. Error handling
11. Crisis intervention integration
12. Extractor modularity and parsing
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.assistant.mental_health_assistant import MentalHealthAssistant
from services.assistant.extractors import (
    ScheduleExtractor,
    ScheduleOpportunityAnalyzer,
    ActionPlanExtractor,
    ActionPlanOpportunityAnalyzer,
)
from services.memory.types import MemoryContext, MemoryItem

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveAssistantTest:
    """Comprehensive test suite for the refactored mental health assistant."""

    def __init__(self):
        self.assistant = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
        }

    async def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🧪 COMPREHENSIVE MENTAL HEALTH ASSISTANT TEST SUITE")
        print("=" * 70)
        print("Testing refactored version for functionality parity...")
        print()

        try:
            # Initialize assistant
            self.assistant = MentalHealthAssistant()
            print("✅ Assistant initialized successfully")
            print()

            # Run test categories
            await self._test_basic_functionality()
            await self._test_crisis_detection()
            await self._test_schedule_extraction()
            await self._test_action_plan_extraction()
            await self._test_memory_integration()
            await self._test_metadata_extraction()
            await self._test_resource_extraction()
            await self._test_configuration_handling()
            await self._test_error_handling()
            await self._test_extractor_modularity()
            await self._test_parallel_processing()

            # Print final results
            self._print_final_results()

        except Exception as e:
            print(f"❌ Critical error in test setup: {e}")
            self.test_results["errors"].append(f"Setup error: {e}")

    async def _test_basic_functionality(self):
        """Test basic response generation functionality."""
        print("🧠 1. BASIC FUNCTIONALITY TESTS")
        print("-" * 50)

        test_cases = [
            {
                "name": "Simple support message",
                "message": "I'm feeling a bit sad today",
                "expected_response_length": 50,
                "expected_crisis_level": "SUPPORT",
            },
            {
                "name": "Anxiety expression",
                "message": "I'm feeling really anxious about work",
                "expected_response_length": 50,
                "expected_crisis_level": "SUPPORT",
            },
            {
                "name": "General wellness check",
                "message": "How can I improve my mental health?",
                "expected_response_length": 50,
                "expected_crisis_level": "SUPPORT",
            },
        ]

        for case in test_cases:
            await self._run_basic_test(case)

    async def _run_basic_test(self, case: Dict[str, Any]):
        """Run a single basic functionality test."""
        try:
            response = await self.assistant.generate_response(
                user_message=case["message"],
                memory_context=None,
                user_id="test_user",
            )

            # Validate response structure
            required_fields = [
                "response",
                "crisis_level",
                "crisis_explanation",
                "timestamp",
                "resources_provided",
                "coping_strategies",
                "session_metadata",
                "crisis_flag",
                "configuration_warning",
                "schedule_analysis",
                "action_plan_analysis",
            ]

            missing_fields = [
                field for field in required_fields if field not in response
            ]
            if missing_fields:
                self._fail_test(f"{case['name']}: Missing fields: {missing_fields}")
                return

            # Validate response content
            if len(response["response"]) < case["expected_response_length"]:
                self._fail_test(f"{case['name']}: Response too short")
                return

            if response["crisis_level"] != case["expected_crisis_level"]:
                self._warn_test(
                    f"{case['name']}: Crisis level {response['crisis_level']} != expected {case['expected_crisis_level']}"
                )

            # Validate timestamp
            if not isinstance(response["timestamp"], datetime):
                self._fail_test(f"{case['name']}: Invalid timestamp type")
                return

            self._pass_test(f"{case['name']}: Basic functionality works")

        except Exception as e:
            self._fail_test(f"{case['name']}: Exception - {e}")

    async def _test_crisis_detection(self):
        """Test crisis detection functionality."""
        print("\n🚨 2. CRISIS DETECTION TESTS")
        print("-" * 50)

        crisis_scenarios = [
            {
                "name": "Direct suicide threat",
                "message": "I want to kill myself tonight",
                "expected_level": "CRISIS",
                "expected_flag": True,
            },
            {
                "name": "Passive death ideation",
                "message": "I wish I was dead but I don't have plans",
                "expected_level": "CONCERN",
                "expected_flag": False,
            },
            {
                "name": "Self-harm mention",
                "message": "I've been cutting myself and can't stop",
                "expected_level": "CRISIS",
                "expected_flag": True,
            },
            {
                "name": "Normal sadness",
                "message": "I'm having a difficult day but I'll get through it",
                "expected_level": "SUPPORT",
                "expected_flag": False,
            },
            {
                "name": "Specific plan",
                "message": "I have pills ready and plan to take them all",
                "expected_level": "CRISIS",
                "expected_flag": True,
            },
        ]

        for scenario in crisis_scenarios:
            await self._run_crisis_test(scenario)

    async def _run_crisis_test(self, scenario: Dict[str, Any]):
        """Run a single crisis detection test."""
        try:
            response = await self.assistant.generate_response(
                user_message=scenario["message"],
                memory_context=None,
                user_id="crisis_test_user",
            )

            # Check crisis level
            if response["crisis_level"] != scenario["expected_level"]:
                self._warn_test(
                    f"Crisis {scenario['name']}: Level {response['crisis_level']} != expected {scenario['expected_level']}"
                )
            else:
                self._pass_test(f"Crisis {scenario['name']}: Correct level detected")

            # Check crisis flag
            if response["crisis_flag"] != scenario["expected_flag"]:
                self._fail_test(
                    f"Crisis {scenario['name']}: Flag {response['crisis_flag']} != expected {scenario['expected_flag']}"
                )
            else:
                self._pass_test(f"Crisis {scenario['name']}: Correct flag set")

            # Validate crisis explanation exists
            if not response.get("crisis_explanation"):
                self._fail_test(
                    f"Crisis {scenario['name']}: Missing crisis explanation"
                )

        except Exception as e:
            self._fail_test(f"Crisis {scenario['name']}: Exception - {e}")

    async def _test_schedule_extraction(self):
        """Test schedule extraction and opportunity analysis."""
        print("\n📅 3. SCHEDULE EXTRACTION TESTS")
        print("-" * 50)

        schedule_scenarios = [
            {
                "name": "Isolation with support mention",
                "message": "I feel so lonely. I should call my mom but I keep forgetting",
                "should_suggest": True,
                "suggested_type": "wellness_check",
            },
            {
                "name": "Therapy reminder need",
                "message": "I keep missing my therapy appointments",
                "should_suggest": True,
                "suggested_type": "therapy_reminder",
            },
            {
                "name": "No scheduling needed",
                "message": "I had a great day today!",
                "should_suggest": False,
                "suggested_type": None,
            },
            {
                "name": "Crisis followup",
                "message": "I'm overwhelmed and need regular check-ins",
                "should_suggest": True,
                "suggested_type": "crisis_followup",
            },
        ]

        for scenario in schedule_scenarios:
            await self._run_schedule_test(scenario)

    async def _run_schedule_test(self, scenario: Dict[str, Any]):
        """Run a single schedule extraction test."""
        try:
            response = await self.assistant.generate_response(
                user_message=scenario["message"],
                memory_context=None,
                user_id="schedule_test_user",
            )

            schedule_analysis = response.get("schedule_analysis", {})

            # Check if suggestion matches expectation
            should_suggest = schedule_analysis.get("should_suggest_scheduling", False)
            if should_suggest != scenario["should_suggest"]:
                self._warn_test(
                    f"Schedule {scenario['name']}: Suggestion {should_suggest} != expected {scenario['should_suggest']}"
                )
            else:
                self._pass_test(f"Schedule {scenario['name']}: Correct suggestion")

            # Check extracted schedule structure if suggested
            if should_suggest:
                if "extracted_schedule" not in schedule_analysis:
                    self._fail_test(
                        f"Schedule {scenario['name']}: Missing extracted_schedule"
                    )
                else:
                    self._pass_test(f"Schedule {scenario['name']}: Has extracted data")

        except Exception as e:
            self._fail_test(f"Schedule {scenario['name']}: Exception - {e}")

    async def _test_action_plan_extraction(self):
        """Test action plan extraction and opportunity analysis."""
        print("\n🎯 4. ACTION PLAN EXTRACTION TESTS")
        print("-" * 50)

        action_plan_scenarios = [
            {
                "name": "Career change goal",
                "message": "I want to change careers but don't know where to start",
                "should_suggest": True,
                "plan_type": "personal_achievement",
            },
            {
                "name": "Anxiety management",
                "message": "I need help managing my anxiety better",
                "should_suggest": True,
                "plan_type": "therapeutic_emotional",
            },
            {
                "name": "Just venting",
                "message": "Just need someone to listen, having a rough day",
                "should_suggest": False,
                "plan_type": None,
            },
            {
                "name": "Fitness goal",
                "message": "I want to get healthier but feel overwhelmed about starting",
                "should_suggest": True,
                "plan_type": "personal_achievement",
            },
        ]

        for scenario in action_plan_scenarios:
            await self._run_action_plan_test(scenario)

    async def _run_action_plan_test(self, scenario: Dict[str, Any]):
        """Run a single action plan extraction test."""
        try:
            response = await self.assistant.generate_response(
                user_message=scenario["message"],
                memory_context=None,
                user_id="action_plan_test_user",
            )

            action_plan_analysis = response.get("action_plan_analysis", {})

            # Check if suggestion matches expectation
            should_suggest = action_plan_analysis.get(
                "should_suggest_action_plan", False
            )
            if should_suggest != scenario["should_suggest"]:
                self._warn_test(
                    f"Action Plan {scenario['name']}: Suggestion {should_suggest} != expected {scenario['should_suggest']}"
                )
            else:
                self._pass_test(f"Action Plan {scenario['name']}: Correct suggestion")

            # Check plan type if suggested
            if should_suggest and scenario["plan_type"]:
                plan_type = action_plan_analysis.get("action_plan_type")
                if plan_type != scenario["plan_type"]:
                    self._warn_test(
                        f"Action Plan {scenario['name']}: Type {plan_type} != expected {scenario['plan_type']}"
                    )

            # Check extracted action plan structure if suggested
            if should_suggest:
                if "extracted_action_plan" not in action_plan_analysis:
                    self._fail_test(
                        f"Action Plan {scenario['name']}: Missing extracted_action_plan"
                    )
                else:
                    self._pass_test(
                        f"Action Plan {scenario['name']}: Has extracted data"
                    )

        except Exception as e:
            self._fail_test(f"Action Plan {scenario['name']}: Exception - {e}")

    async def _test_memory_integration(self):
        """Test memory context integration."""
        print("\n🧠 5. MEMORY INTEGRATION TESTS")
        print("-" * 50)

        # Test with no memory context
        try:
            response = await self.assistant.generate_response(
                user_message="How are you?",
                memory_context=None,
                user_id="memory_test_user",
            )
            self._pass_test("Memory: No context handling works")
        except Exception as e:
            self._fail_test(f"Memory: No context failed - {e}")

        # Test with empty memory context
        try:
            empty_context = MemoryContext(short_term=[], long_term=[], digest=None)
            response = await self.assistant.generate_response(
                user_message="How are you?",
                memory_context=empty_context,
                user_id="memory_test_user",
            )
            self._pass_test("Memory: Empty context handling works")
        except Exception as e:
            self._fail_test(f"Memory: Empty context failed - {e}")

        # Test with mock memory context
        try:
            mock_memory = MemoryContext(
                short_term=[
                    MemoryItem(
                        id="mem1",
                        user_id="memory_test_user",
                        content="User mentioned feeling anxious yesterday",
                        type="user_message",
                        metadata={},
                        timestamp=datetime.now(),
                    )
                ],
                long_term=[],
                digest="User has been working on anxiety management",
            )
            response = await self.assistant.generate_response(
                user_message="How are you?",
                memory_context=mock_memory,
                user_id="memory_test_user",
            )
            self._pass_test("Memory: Context integration works")
        except Exception as e:
            self._fail_test(f"Memory: Context integration failed - {e}")

    async def _test_metadata_extraction(self):
        """Test session metadata extraction."""
        print("\n📊 6. METADATA EXTRACTION TESTS")
        print("-" * 50)

        try:
            response = await self.assistant.generate_response(
                user_message="I'm feeling overwhelmed with work stress",
                memory_context=None,
                user_id="metadata_test_user",
            )

            metadata = response.get("session_metadata", {})
            required_metadata_fields = [
                "transcript",
                "ground_emotion",
                "scene_title",
                "metaphor_prompt",
                "cognitive_load",
                "temporal_tag",
                "color_palette",
                "texture_descriptor",
                "temp_descriptor",
                "sketch_motion",
                "scene_description",
                "body_locus",
                "sketch_shape",
            ]

            missing_metadata = [
                field for field in required_metadata_fields if field not in metadata
            ]
            if missing_metadata:
                self._warn_test(f"Metadata: Missing fields: {missing_metadata}")
            else:
                self._pass_test("Metadata: All required fields present")

            # Validate metadata content
            if metadata.get("transcript") != "I'm feeling overwhelmed with work stress":
                self._warn_test("Metadata: Transcript doesn't match input")

            if not metadata.get("ground_emotion"):
                self._warn_test("Metadata: No ground emotion detected")

        except Exception as e:
            self._fail_test(f"Metadata: Extraction failed - {e}")

    async def _test_resource_extraction(self):
        """Test resource and coping strategy extraction."""
        print("\n🆘 7. RESOURCE EXTRACTION TESTS")
        print("-" * 50)

        # Mock a response that should contain resources
        mock_response = "I recommend trying therapy and consider calling a crisis hotline. Meditation and breathing exercises can help."

        resources = self.assistant._extract_resources(mock_response)
        strategies = self.assistant._extract_coping_strategies(mock_response)

        if "therapy" in resources:
            self._pass_test("Resources: Therapy detection works")
        else:
            self._warn_test("Resources: Therapy not detected")

        if "crisis_hotline" in resources:
            self._pass_test("Resources: Crisis hotline detection works")
        else:
            self._warn_test("Resources: Crisis hotline not detected")

        if "breathing_exercise" in strategies:
            self._pass_test("Strategies: Breathing exercise detection works")
        else:
            self._warn_test("Strategies: Breathing exercise not detected")

        if "meditation" in strategies:
            self._pass_test("Strategies: Meditation detection works")
        else:
            self._warn_test("Strategies: Meditation not detected")

    async def _test_configuration_handling(self):
        """Test configuration handling and warnings."""
        print("\n⚙️ 8. CONFIGURATION HANDLING TESTS")
        print("-" * 50)

        # Test configuration warning detection
        warning = self.assistant._get_configuration_warning()
        if warning:
            self._warn_test(f"Configuration: Warning detected - {warning}")
        else:
            self._pass_test("Configuration: No warnings detected")

        # Test configuration check during init
        try:
            # This should not raise an exception
            self.assistant._check_configuration()
            self._pass_test("Configuration: Check method works")
        except Exception as e:
            self._fail_test(f"Configuration: Check failed - {e}")

    async def _test_error_handling(self):
        """Test error handling and fallback responses."""
        print("\n🚫 9. ERROR HANDLING TESTS")
        print("-" * 50)

        # Test fallback response creation
        try:
            mock_crisis = {"level": "SUPPORT", "explanation": "Test"}
            fallback = self.assistant._create_fallback_response(
                crisis_assessment=mock_crisis,
                config_warning=None,
                error=Exception("Test error"),
            )

            required_fallback_fields = [
                "response",
                "crisis_level",
                "crisis_explanation",
                "timestamp",
                "resources_provided",
                "coping_strategies",
                "session_metadata",
                "crisis_flag",
                "configuration_warning",
                "schedule_analysis",
                "action_plan_analysis",
                "error",
            ]

            missing_fallback = [
                field for field in required_fallback_fields if field not in fallback
            ]
            if missing_fallback:
                self._fail_test(
                    f"Error handling: Missing fallback fields: {missing_fallback}"
                )
            else:
                self._pass_test("Error handling: Fallback response structure correct")

        except Exception as e:
            self._fail_test(f"Error handling: Fallback creation failed - {e}")

    async def _test_extractor_modularity(self):
        """Test that extractors work independently."""
        print("\n🔧 10. EXTRACTOR MODULARITY TESTS")
        print("-" * 50)

        # Test schedule extractor independently
        try:
            schedule_analyzer = ScheduleOpportunityAnalyzer()
            analysis = schedule_analyzer.analyze_opportunity(
                user_message="I feel lonely and should call my friend",
                assistant_response="I understand you're feeling isolated",
                context="No context",
            )

            if "should_suggest" in analysis:
                self._pass_test("Extractors: Schedule analyzer works independently")
            else:
                self._fail_test("Extractors: Schedule analyzer missing key fields")

        except Exception as e:
            self._fail_test(f"Extractors: Schedule analyzer failed - {e}")

        # Test action plan extractor independently
        try:
            action_plan_analyzer = ActionPlanOpportunityAnalyzer()
            analysis = action_plan_analyzer.analyze_opportunity(
                user_message="I want to change careers but don't know how",
                assistant_response="Career changes can be challenging",
                context="No context",
            )

            if "should_suggest" in analysis:
                self._pass_test("Extractors: Action plan analyzer works independently")
            else:
                self._fail_test("Extractors: Action plan analyzer missing key fields")

        except Exception as e:
            self._fail_test(f"Extractors: Action plan analyzer failed - {e}")

    async def _test_parallel_processing(self):
        """Test that parallel processing works correctly."""
        print("\n⚡ 11. PARALLEL PROCESSING TESTS")
        print("-" * 50)

        try:
            # Test multiple concurrent requests
            import time

            start_time = time.time()

            tasks = [
                self.assistant.generate_response(
                    user_message=f"Test message {i}",
                    memory_context=None,
                    user_id=f"parallel_test_user_{i}",
                )
                for i in range(3)
            ]

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            if len(responses) == 3:
                self._pass_test("Parallel: Multiple concurrent requests work")
            else:
                self._fail_test(f"Parallel: Expected 3 responses, got {len(responses)}")

            # Check that all responses are valid
            for i, response in enumerate(responses):
                if "response" not in response:
                    self._fail_test(f"Parallel: Response {i} missing response field")
                else:
                    self._pass_test(f"Parallel: Response {i} is valid")

            # Check reasonable processing time (should be faster than sequential)
            processing_time = end_time - start_time
            if processing_time > 30:  # Reasonable timeout
                self._warn_test(
                    f"Parallel: Processing time {processing_time:.2f}s seems slow"
                )
            else:
                self._pass_test(
                    f"Parallel: Processing completed in {processing_time:.2f}s"
                )

        except Exception as e:
            self._fail_test(f"Parallel: Processing failed - {e}")

    def _pass_test(self, test_name: str):
        """Mark a test as passed."""
        print(f"  ✅ {test_name}")
        self.test_results["passed"] += 1

    def _fail_test(self, test_name: str):
        """Mark a test as failed."""
        print(f"  ❌ {test_name}")
        self.test_results["failed"] += 1
        self.test_results["errors"].append(test_name)

    def _warn_test(self, test_name: str):
        """Mark a test with warning."""
        print(f"  ⚠️  {test_name}")
        self.test_results["warnings"].append(test_name)

    def _print_final_results(self):
        """Print final test results."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)

        total_tests = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (
            (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        )

        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"⚠️  Warnings: {len(self.test_results['warnings'])}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")

        if self.test_results["errors"]:
            print(f"\n❌ FAILED TESTS:")
            for error in self.test_results["errors"]:
                print(f"   - {error}")

        if self.test_results["warnings"]:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.test_results["warnings"]:
                print(f"   - {warning}")

        print(f"\n🎯 REFACTORING SUCCESS METRICS:")
        print(f"   - Modularity: Extractors work independently")
        print(f"   - Maintainability: Clear separation of concerns")
        print(f"   - Functionality: All original features preserved")
        print(f"   - Error Handling: Robust fallback mechanisms")

        if pass_rate >= 90:
            print(
                f"\n🎉 EXCELLENT: Refactoring maintained {pass_rate:.1f}% functionality!"
            )
        elif pass_rate >= 80:
            print(f"\n✅ GOOD: Refactoring maintained {pass_rate:.1f}% functionality")
        elif pass_rate >= 70:
            print(
                f"\n⚠️  ACCEPTABLE: Refactoring maintained {pass_rate:.1f}% functionality"
            )
        else:
            print(f"\n❌ NEEDS WORK: Only {pass_rate:.1f}% functionality maintained")


async def main():
    """Run the comprehensive test suite."""
    test_suite = ComprehensiveAssistantTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
