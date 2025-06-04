"""
Schedule extraction functionality for mental health assistant.
"""

import os
import logging
from typing import Dict, Any
from .base_extractor import BaseExtractor, BaseOpportunityAnalyzer

logger = logging.getLogger(__name__)


class ScheduleExtractor(BaseExtractor):
    """Extracts scheduling information from conversations."""

    def __init__(self, model, generation_config):
        super().__init__(model, generation_config)
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load the schedule extraction prompt from file."""
        utils_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "utils", "prompts", "chat"
        )
        prompt_file = os.path.join(utils_dir, "schedule_extraction.txt")

        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    logger.info("Loaded schedule extraction prompt from file")
                    return content

        logger.warning("Schedule extraction prompt file not found")
        return None

    def get_prompt_template(self) -> str:
        return self.prompt_template

    def get_extraction_type(self) -> str:
        return "schedule"

    def create_fallback_info(self) -> Dict[str, Any]:
        """Create fallback schedule info when parsing fails."""
        return {
            "should_suggest_scheduling": False,
            "suggested_timing": None,
            "purpose_description": None,
            "extracted_schedule": {},
            "gentle_prompt": None,
            "scheduling_type": None,
            "schedule_metadata": {},
            "parse_error": True,
        }

    def parse_extracted_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize the extracted schedule data."""
        # Ensure extracted_schedule is always a dict to avoid NoneType errors
        extracted_schedule = parsed_data.get("extracted_schedule") or {}

        return {
            "should_suggest_scheduling": parsed_data.get(
                "should_suggest_scheduling", False
            ),
            "suggested_timing": parsed_data.get("suggested_timing"),
            "purpose_description": parsed_data.get("purpose_description"),
            "extracted_schedule": extracted_schedule,
            "gentle_prompt": parsed_data.get("gentle_prompt"),
            "scheduling_type": extracted_schedule.get("schedule_type"),
            "schedule_metadata": {
                "name": extracted_schedule.get("name"),
                "description": extracted_schedule.get("description"),
                "cron_expression": extracted_schedule.get("suggested_cron"),
                "timezone": extracted_schedule.get("timezone", "UTC"),
                "reminder_method": extracted_schedule.get("reminder_method", "email"),
            },
        }


class ScheduleOpportunityAnalyzer(BaseOpportunityAnalyzer):
    """Analyzes conversations for scheduling opportunities."""

    def get_analysis_keywords(self) -> Dict[str, list]:
        """Return keyword categories for schedule analysis."""
        return {
            "isolation": [
                "alone",
                "lonely",
                "isolated",
                "no one to talk to",
                "nobody understands",
                "feel disconnected",
                "withdrawn",
            ],
            "support_mentions": [
                "family",
                "friend",
                "mom",
                "dad",
                "sister",
                "brother",
                "therapist",
                "counselor",
                "support group",
                "partner",
            ],
            "checkup_opportunities": [
                "should call",
                "need to talk to",
                "haven't spoken to",
                "miss talking to",
                "want to reach out",
                "check in",
            ],
            "crisis_indicators": [
                "overwhelmed",
                "can't handle",
                "too much",
                "breaking down",
                "giving up",
                "hopeless",
                "desperate",
                "crisis",
            ],
        }

    def get_analysis_type(self) -> str:
        return "schedule_opportunity"

    def _determine_suggestion(
        self, analysis: Dict[str, Any], combined_text: str
    ) -> Dict[str, Any]:
        """Determine if we should suggest scheduling based on analysis."""
        reasoning = []

        if analysis["has_isolation"]:
            reasoning.append("User expressing feelings of isolation")
            analysis["should_suggest"] = True
            analysis["confidence_level"] = "high"
            analysis["suggested_type"] = "wellness_check"
            analysis["suggested_frequency"] = "weekly"

        if analysis["has_crisis_indicators"]:
            reasoning.append("Crisis context detected")
            analysis["should_suggest"] = True
            analysis["confidence_level"] = "high"
            analysis["suggested_type"] = "crisis_followup"
            analysis["suggested_frequency"] = (
                "daily" if "crisis" in combined_text else "weekly"
            )

        if analysis["has_support_mentions"] and analysis["has_checkup_opportunities"]:
            reasoning.append("User mentioned support network and check-in opportunity")
            analysis["should_suggest"] = True
            analysis["confidence_level"] = "moderate"
            analysis["suggested_type"] = "routine_checkin"
            analysis["suggested_frequency"] = "weekly"

        # Don't suggest if already getting regular support
        therapy_mentions = ["therapy", "therapist", "counseling", "seeing someone"]
        if any(therapy in combined_text for therapy in therapy_mentions):
            if "therapy" in combined_text and "reminder" in combined_text:
                analysis["suggested_type"] = "therapy_reminder"
                reasoning.append("Therapy reminder opportunity detected")
            else:
                # Already getting professional support
                analysis["should_suggest"] = False
                reasoning.append("User already receiving professional support")

        analysis["reasoning"] = reasoning
        return analysis
