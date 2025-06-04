"""
Action plan extraction functionality for mental health assistant.
"""

import os
import logging
from typing import Dict, Any
from .base_extractor import BaseExtractor, BaseOpportunityAnalyzer

logger = logging.getLogger(__name__)


class ActionPlanExtractor(BaseExtractor):
    """Extracts action plan information from conversations."""

    def __init__(self, model, generation_config):
        super().__init__(model, generation_config)
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load the action plan generation prompt from file."""
        utils_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "utils", "prompts", "chat"
        )
        prompt_file = os.path.join(utils_dir, "action_plan_generation.txt")

        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    logger.info("Loaded action plan generation prompt from file")
                    return content

        logger.warning("Action plan generation prompt file not found")
        return None

    def get_prompt_template(self) -> str:
        return self.prompt_template

    def get_extraction_type(self) -> str:
        return "action_plan"

    def create_fallback_info(self) -> Dict[str, Any]:
        """Create fallback action plan info when parsing fails."""
        return {
            "should_suggest_action_plan": False,
            "suggested_action_plan": None,
            "purpose_description": None,
            "extracted_action_plan": {},
            "gentle_prompt": None,
            "action_plan_type": None,
            "action_plan_metadata": {},
            "parse_error": True,
        }

    def parse_extracted_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize the extracted action plan data."""
        # Handle both old and new field names
        should_suggest = parsed_data.get(
            "should_suggest_action_plan"
        ) or parsed_data.get("should_generate_action_plan", False)

        # Ensure extracted_action_plan is always a dict to avoid NoneType errors
        # Try both 'extracted_action_plan' and 'action_plan' keys
        extracted_action_plan = (
            parsed_data.get("extracted_action_plan")
            or parsed_data.get("action_plan")
            or {}
        )

        return {
            "should_suggest_action_plan": should_suggest,
            "suggested_action_plan": parsed_data.get("suggested_action_plan"),
            "purpose_description": parsed_data.get("purpose_description"),
            "extracted_action_plan": extracted_action_plan,
            "gentle_prompt": (
                parsed_data.get("gentle_prompt")
                or parsed_data.get("gentle_introduction")
                or parsed_data.get("collaboration_invitation")
            ),
            "action_plan_type": (
                extracted_action_plan.get("action_plan_type")
                or parsed_data.get("plan_type")
            ),
            "action_plan_metadata": {
                "name": extracted_action_plan.get("name")
                or extracted_action_plan.get("plan_title"),
                "description": (
                    extracted_action_plan.get("description")
                    or extracted_action_plan.get("plan_summary")
                ),
                "action_plan_type": (
                    extracted_action_plan.get("action_plan_type")
                    or parsed_data.get("plan_type")
                ),
                "user_emotional_state": parsed_data.get("user_emotional_state"),
                "primary_goal": parsed_data.get("primary_goal"),
                "user_capacity": parsed_data.get("user_capacity"),
                "motivation_level": parsed_data.get("motivation_level"),
            },
        }


class ActionPlanOpportunityAnalyzer(BaseOpportunityAnalyzer):
    """Analyzes conversations for action plan opportunities."""

    def get_analysis_keywords(self) -> Dict[str, list]:
        """Return keyword categories for action plan analysis."""
        return {
            "goal_language": [
                "want to",
                "goal",
                "achieve",
                "improve",
                "change",
                "get better",
                "work on",
                "start",
                "begin",
                "learn",
                "develop",
                "build",
            ],
            "stuck_indicators": [
                "stuck",
                "don't know how",
                "don't know where to start",
                "overwhelming",
                "overwhelmed",
                "need help",
                "what should i do",
                "how do i",
                "help me",
            ],
            "specific_domains": [
                "career",
                "job",
                "work",
                "fitness",
                "health",
                "exercise",
                "relationship",
                "social",
                "anxiety",
                "depression",
                "stress",
                "writing",
                "creative",
                "art",
                "music",
                "learning",
                "skill",
                "habit",
                "routine",
                "organization",
                "productivity",
                "money",
                "financial",
            ],
            "therapeutic_context": [
                "anxiety",
                "depression",
                "stress",
                "overwhelmed",
                "cope",
                "coping",
                "therapy",
                "mental health",
                "emotional",
                "feelings",
                "mood",
            ],
            "just_venting": [
                "just need someone to listen",
                "just want to talk",
                "just feeling",
                "having a bad day",
                "need to vent",
            ],
        }

    def get_analysis_type(self) -> str:
        return "action_plan_opportunity"

    def _determine_suggestion(
        self, analysis: Dict[str, Any], combined_text: str
    ) -> Dict[str, Any]:
        """Determine if we should suggest action plan based on analysis."""
        reasoning = []

        # Start with base analysis structure
        analysis.update(
            {"should_suggest": False, "plan_type": None, "confidence_level": "low"}
        )

        # Determine if we should suggest an action plan
        if analysis["has_goal_language"] and analysis["has_stuck_indicators"]:
            reasoning.append(
                "User has goals but feels stuck - prime candidate for action planning"
            )
            analysis["should_suggest"] = True
            analysis["confidence_level"] = "high"

        if analysis["has_goal_language"] and analysis["has_specific_domains"]:
            reasoning.append("User has specific goals in identifiable domain")
            analysis["should_suggest"] = True
            analysis["confidence_level"] = (
                "high" if analysis["confidence_level"] != "high" else "high"
            )

        if "what should i do" in combined_text or "help me" in combined_text:
            reasoning.append("User explicitly asking for guidance/help")
            analysis["should_suggest"] = True
            analysis["confidence_level"] = "moderate"

        # Determine plan type
        if analysis["has_therapeutic_context"]:
            analysis["plan_type"] = "therapeutic_emotional"
            reasoning.append("Therapeutic/emotional context detected")
        elif analysis["has_specific_domains"]:
            analysis["plan_type"] = "personal_achievement"
            reasoning.append("Personal achievement context detected")
        else:
            analysis["plan_type"] = "hybrid"

        # Don't suggest if they seem to just want emotional support
        if analysis["has_just_venting"]:
            analysis["should_suggest"] = False
            reasoning.append(
                "User seems to want emotional support, not action planning"
            )

        analysis["reasoning"] = reasoning
        return analysis
