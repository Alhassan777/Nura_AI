"""
Base extraction functionality for mental health assistant.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for all conversation extractors."""

    def __init__(
        self,
        model: genai.GenerativeModel,
        generation_config: genai.types.GenerationConfig,
    ):
        self.model = model
        self.generation_config = generation_config

    @abstractmethod
    def get_prompt_template(self) -> str:
        """Return the prompt template for this extractor."""
        pass

    @abstractmethod
    def get_extraction_type(self) -> str:
        """Return the type of extraction (for logging)."""
        pass

    @abstractmethod
    def create_fallback_info(self) -> Dict[str, Any]:
        """Create fallback information when extraction fails."""
        pass

    @abstractmethod
    def parse_extracted_data(self, parsed_json: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize the extracted JSON data."""
        pass

    async def extract_information(
        self,
        user_message: str,
        assistant_response: str,
        conversation_context: str,
        additional_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generic extraction method that handles the common pattern:
        1. Build prompt
        2. Generate response
        3. Parse JSON
        4. Handle errors
        """

        # Check if we have required prompt
        prompt_template = self.get_prompt_template()
        if not prompt_template:
            result = self.create_fallback_info()
            if additional_analysis:
                result[f"{self.get_extraction_type()}_analysis"] = additional_analysis
            return result

        # Build extraction prompt
        extraction_prompt = f"""
{prompt_template}

CONVERSATION CONTEXT:
{conversation_context}

USER MESSAGE: {user_message}
ASSISTANT RESPONSE: {assistant_response}

Analyze the conversation and extract any {self.get_extraction_type()} information or opportunities.
"""

        try:
            response = self.model.generate_content(
                extraction_prompt, generation_config=self.generation_config
            )

            # Parse the structured response
            extracted_info = self._parse_llm_response(response.text)

            # Add additional analysis if provided
            if additional_analysis:
                extracted_info[f"{self.get_extraction_type()}_analysis"] = (
                    additional_analysis
                )

            return extracted_info

        except Exception as e:
            logger.error(
                f"Error extracting {self.get_extraction_type()} information: {e}"
            )
            result = self.create_fallback_info()
            result["error"] = str(e)
            if additional_analysis:
                result[f"{self.get_extraction_type()}_analysis"] = additional_analysis
            return result

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for JSON content with improved error handling."""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()

            # Log the raw response for debugging
            logger.debug(
                f"Raw {self.get_extraction_type()} response: {cleaned_text[:500]}..."
            )

            # Find JSON in the response - try multiple strategies
            json_str = self._extract_json_from_text(cleaned_text)

            if not json_str:
                logger.warning(
                    f"No JSON found in {self.get_extraction_type()} extraction response"
                )
                return self.create_fallback_info()

            # Log the extracted JSON for debugging
            logger.debug(
                f"Extracted JSON for {self.get_extraction_type()}: {json_str[:300]}..."
            )

            # Try to parse JSON with multiple strategies
            parsed_data = self._parse_json_with_fallbacks(json_str)

            if parsed_data:
                # Use subclass-specific parsing
                return self.parse_extracted_data(parsed_data)
            else:
                logger.warning("All JSON parsing strategies failed")
                return self.create_fallback_info()

        except Exception as e:
            logger.error(f"Error parsing {self.get_extraction_type()} extraction: {e}")
            return self.create_fallback_info()

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON string from text using multiple strategies."""
        import re

        # Strategy 1: Standard { ... } extraction
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx]
            # Basic validation - count braces
            if json_str.count("{") == json_str.count("}"):
                return json_str

        # Strategy 2: Find the largest balanced JSON block
        json_blocks = []
        brace_count = 0
        start = -1

        for i, char in enumerate(text):
            if char == "{":
                if brace_count == 0:
                    start = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    json_blocks.append(text[start : i + 1])

        # Return the largest JSON block
        if json_blocks:
            return max(json_blocks, key=len)

        return None

    def _parse_json_with_fallbacks(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Try multiple strategies to parse JSON."""
        import json

        # Strategy 1: Parse as-is
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Fix common issues and try again
        try:
            fixed_json = self._fix_common_json_issues(json_str)
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass

        # Strategy 3: More aggressive fixing
        try:
            aggressively_fixed = self._aggressive_json_fix(json_str)
            return json.loads(aggressively_fixed)
        except json.JSONDecodeError:
            pass

        # Strategy 4: Extract partial data manually
        partial_data = self._extract_partial_json_data(json_str)
        if partial_data:
            return partial_data

        return None

    def _aggressive_json_fix(self, json_str: str) -> str:
        """More aggressive JSON fixing for complex structures."""
        import re

        # Start with basic fixes
        json_str = self._fix_common_json_issues(json_str)

        # Fix nested quote issues more aggressively
        # Replace sequences of quotes that are clearly errors
        json_str = re.sub(r'"""+', '"', json_str)

        # Fix line breaks within string values
        # Look for strings that span multiple lines and join them
        json_str = re.sub(
            r'"\s*\n\s*([^"]*?)\s*\n\s*"', r'"\1"', json_str, flags=re.MULTILINE
        )

        # Fix missing quotes around keys (common LLM error)
        json_str = re.sub(
            r"(\s|{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', json_str
        )

        # Fix incomplete string values (ending quotes missing)
        # This is complex and might introduce errors, so be careful
        lines = json_str.split("\n")
        fixed_lines = []
        for line in lines:
            # If line has opening quote but no closing quote for a value
            if ":" in line and line.count('"') % 2 == 1:
                # Check if this is a string value without closing quote
                colon_idx = line.find(":")
                after_colon = line[colon_idx + 1 :].strip()
                if (
                    after_colon.startswith('"')
                    and not after_colon.endswith('"')
                    and not after_colon.endswith('",')
                ):
                    # Add closing quote
                    if line.endswith(","):
                        line = line[:-1] + '",'
                    else:
                        line = line + '"'
            fixed_lines.append(line)

        json_str = "\n".join(fixed_lines)

        # Fix common structural issues
        # Remove trailing commas before closing braces/brackets (more aggressive)
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Fix missing commas between objects (more precise)
        json_str = re.sub(r"}\s*{", r"}, {", json_str)
        json_str = re.sub(r"]\s*\[", r"], [", json_str)

        # Fix boolean and null values
        json_str = re.sub(r":\s*True\b", r": true", json_str)
        json_str = re.sub(r":\s*False\b", r": false", json_str)
        json_str = re.sub(r":\s*None\b", r": null", json_str)

        return json_str

    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues from LLM responses."""
        import re

        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Fix unescaped quotes in strings (basic attempt)
        json_str = json_str.replace('""', '"')

        # Fix newlines in strings (replace with spaces)
        json_str = re.sub(
            r'"\s*\n\s*([^"]*)\s*\n\s*"', r'"\1"', json_str, flags=re.MULTILINE
        )

        # Remove extra whitespace and newlines within JSON
        json_str = re.sub(r"\s+", " ", json_str)

        # Fix missing commas between key-value pairs (common LLM mistake)
        # Look for patterns like: "key": "value" "nextkey": "nextvalue"
        json_str = re.sub(r'"\s*([^"]*)\s*"\s*"([^"]*)":', r'"\1", "\2":', json_str)

        # Fix missing commas between objects/arrays
        json_str = re.sub(r"}\s*{", r"}, {", json_str)
        json_str = re.sub(r"]\s*\[", r"], [", json_str)

        # Fix boolean values that might be capitalized
        json_str = re.sub(r":\s*True\b", r": true", json_str)
        json_str = re.sub(r":\s*False\b", r": false", json_str)
        json_str = re.sub(r":\s*None\b", r": null", json_str)

        return json_str

    def _extract_partial_json_data(self, text: str) -> Dict[str, Any]:
        """Extract partial data when JSON parsing fails."""
        import re

        partial_data = {}

        # Common patterns to extract key information - more comprehensive
        patterns = {
            # Boolean fields
            "should_suggest_scheduling": r'"should_suggest_scheduling"[:\s]*(true|false)',
            "should_suggest_action_plan": r'"should_suggest_action_plan"[:\s]*(true|false)',
            "should_generate_action_plan": r'"should_generate_action_plan"[:\s]*(true|false)',
            # String fields
            "purpose_description": r'"purpose_description"[:\s]*"([^"]*)"',
            "gentle_prompt": r'"gentle_prompt"[:\s]*"([^"]*)"',
            "suggested_timing": r'"suggested_timing"[:\s]*"([^"]*)"',
            "suggested_action_plan": r'"suggested_action_plan"[:\s]*"([^"]*)"',
            "plan_type": r'"plan_type"[:\s]*"([^"]*)"',
            "user_emotional_state": r'"user_emotional_state"[:\s]*"([^"]*)"',
            "primary_goal": r'"primary_goal"[:\s]*"([^"]*)"',
            "user_capacity": r'"user_capacity"[:\s]*"([^"]*)"',
            "motivation_level": r'"motivation_level"[:\s]*"([^"]*)"',
            "gentle_introduction": r'"gentle_introduction"[:\s]*"([^"]*)"',
            "collaboration_invitation": r'"collaboration_invitation"[:\s]*"([^"]*)"',
        }

        # Also try without quotes around keys (another common LLM mistake)
        fallback_patterns = {
            "should_suggest_scheduling": r"should_suggest_scheduling[:\s]*(true|false)",
            "should_suggest_action_plan": r"should_suggest_action_plan[:\s]*(true|false)",
            "should_generate_action_plan": r"should_generate_action_plan[:\s]*(true|false)",
            "purpose_description": r'purpose_description[:\s]*"([^"]*)"',
            "gentle_prompt": r'gentle_prompt[:\s]*"([^"]*)"',
            "plan_type": r'plan_type[:\s]*"([^"]*)"',
        }

        # Try quoted patterns first
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1)
                if value.lower() in ["true", "false"]:
                    partial_data[key] = value.lower() == "true"
                else:
                    partial_data[key] = value.strip()

        # If we didn't find much, try fallback patterns
        if len(partial_data) < 2:
            for key, pattern in fallback_patterns.items():
                if key not in partial_data:  # Don't overwrite good data
                    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = match.group(1)
                        if value.lower() in ["true", "false"]:
                            partial_data[key] = value.lower() == "true"
                        else:
                            partial_data[key] = value.strip()

        # Try to extract nested object data if present
        self._extract_nested_objects(text, partial_data)

        return partial_data if partial_data else None

    def _extract_nested_objects(self, text: str, partial_data: Dict[str, Any]) -> None:
        """Extract data from nested objects like action_plan or extracted_schedule."""
        import re

        # Look for action_plan object
        action_plan_match = re.search(r'"action_plan"[:\s]*{([^}]+)}', text, re.DOTALL)
        if action_plan_match:
            action_plan_content = action_plan_match.group(1)
            action_plan_data = {}

            # Extract fields from action plan
            plan_patterns = {
                "plan_title": r'"plan_title"[:\s]*"([^"]*)"',
                "plan_summary": r'"plan_summary"[:\s]*"([^"]*)"',
            }

            for key, pattern in plan_patterns.items():
                match = re.search(pattern, action_plan_content)
                if match:
                    action_plan_data[key] = match.group(1).strip()

            if action_plan_data:
                partial_data["action_plan"] = action_plan_data

        # Look for extracted_schedule object
        schedule_match = re.search(
            r'"extracted_schedule"[:\s]*{([^}]+)}', text, re.DOTALL
        )
        if schedule_match:
            schedule_content = schedule_match.group(1)
            schedule_data = {}

            # Extract fields from schedule
            schedule_patterns = {
                "name": r'"name"[:\s]*"([^"]*)"',
                "description": r'"description"[:\s]*"([^"]*)"',
                "schedule_type": r'"schedule_type"[:\s]*"([^"]*)"',
                "suggested_cron": r'"suggested_cron"[:\s]*"([^"]*)"',
                "timezone": r'"timezone"[:\s]*"([^"]*)"',
                "reminder_method": r'"reminder_method"[:\s]*"([^"]*)"',
            }

            for key, pattern in schedule_patterns.items():
                match = re.search(pattern, schedule_content)
                if match:
                    schedule_data[key] = match.group(1).strip()

            if schedule_data:
                partial_data["extracted_schedule"] = schedule_data


class BaseOpportunityAnalyzer(ABC):
    """Base class for analyzing conversation opportunities."""

    @abstractmethod
    def get_analysis_keywords(self) -> Dict[str, list]:
        """Return keyword categories for analysis."""
        pass

    @abstractmethod
    def get_analysis_type(self) -> str:
        """Return the type of analysis (for logging)."""
        pass

    def analyze_opportunity(
        self, user_message: str, assistant_response: str, context: str
    ) -> Dict[str, Any]:
        """
        Generic opportunity analysis using keyword matching.
        """
        user_lower = user_message.lower()
        response_lower = assistant_response.lower()
        combined_text = f"{user_lower} {response_lower}"

        # Get keyword categories from subclass
        keywords = self.get_analysis_keywords()

        # Analyze conversation
        analysis = {
            "should_suggest": False,
            "confidence_level": "low",
            "reasoning": [],
            **{
                f"has_{category}": any(
                    keyword in combined_text for keyword in keyword_list
                )
                for category, keyword_list in keywords.items()
            },
        }

        # Let subclass determine if we should suggest
        analysis = self._determine_suggestion(analysis, combined_text)

        return analysis

    @abstractmethod
    def _determine_suggestion(
        self, analysis: Dict[str, Any], combined_text: str
    ) -> Dict[str, Any]:
        """Determine if we should make a suggestion based on analysis."""
        pass
