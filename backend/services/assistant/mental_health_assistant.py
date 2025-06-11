"""
Refactored Mental Health Assistant
A cleaner, more maintainable version with separated concerns.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime
import time
import random

# New modular imports
from .extractors import (
    ScheduleExtractor,
    ScheduleOpportunityAnalyzer,
    ActionPlanExtractor,
    ActionPlanOpportunityAnalyzer,
)
from .crisis_intervention import CrisisInterventionManager
from ..memory.types import MemoryItem, MemoryContext
from ..memory.config import Config

logger = logging.getLogger(__name__)


class MentalHealthAssistant:
    """
    Refactored Mental Health Assistant with improved modularity and maintainability.

    Key improvements:
    - Separated extraction logic into specialized modules
    - Extracted crisis intervention into its own manager
    - Reduced repetition through base classes
    - Cleaner, more focused methods
    """

    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Setup generation configurations
        self._setup_generation_configs()

        # Initialize the model
        self.model = genai.GenerativeModel(
            Config.GEMINI_MODEL, generation_config=self.conversational_config
        )

        # Load core prompts
        self._load_core_prompts()

        # Initialize extractors
        self._initialize_extractors()

        # Check configuration
        self._check_configuration()

    def _setup_generation_configs(self):
        """Define all generation configurations in one place for consistency."""
        # Main conversational responses - more creative and varied
        self.conversational_config = genai.types.GenerationConfig(
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048,
            candidate_count=1,
        )

        # Crisis assessment - more deterministic and consistent
        self.crisis_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=20,
            max_output_tokens=512,
            candidate_count=1,
        )

        # Metadata extraction - balanced for structured output
        self.metadata_config = genai.types.GenerationConfig(
            temperature=0.5,
            top_p=0.85,
            top_k=30,
            max_output_tokens=4096,
            candidate_count=1,
        )

    def _load_core_prompts(self):
        """Load core prompts from configuration."""
        self.system_prompt = Config.get_mental_health_system_prompt()
        self.conversation_guidelines = Config.get_conversation_guidelines()
        self.crisis_detection_prompt = Config.get_crisis_detection_prompt()

    def _initialize_extractors(self):
        """Initialize all the extraction modules."""
        # Schedule extraction
        self.schedule_extractor = ScheduleExtractor(self.model, self.metadata_config)
        self.schedule_analyzer = ScheduleOpportunityAnalyzer()

        # Action plan extraction
        self.action_plan_extractor = ActionPlanExtractor(
            self.model, self.metadata_config
        )
        self.action_plan_analyzer = ActionPlanOpportunityAnalyzer()

    def _check_configuration(self):
        """Check if environment variables are properly configured and warn if not."""
        missing_configs = []

        if "CONFIGURATION ERROR" in self.system_prompt:
            missing_configs.append("MENTAL_HEALTH_SYSTEM_PROMPT")
        if "CONFIGURATION ERROR" in self.conversation_guidelines:
            missing_configs.append("CONVERSATION_GUIDELINES")
        if "CONFIGURATION ERROR" in self.crisis_detection_prompt:
            missing_configs.append("CRISIS_DETECTION_PROMPT")

        if missing_configs:
            error_msg = f"⚠️  CONFIGURATION ERROR: Missing environment variables: {', '.join(missing_configs)}. Using fallback configurations with limited functionality."
            logger.error(error_msg)
            print(f"\n{error_msg}\n")

    async def generate_response(
        self,
        user_message: str,
        memory_context: Optional[MemoryContext] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a mental health assistant response."""

        # Check for configuration warnings
        config_warning = self._get_configuration_warning()

        # First, assess crisis level
        crisis_assessment = await self._assess_crisis_level(user_message)

        # Build conversation context
        context = self._build_conversation_context(user_message, memory_context)

        # Generate the main response
        response_prompt = self._build_response_prompt(context, user_message)

        try:
            response = self.model.generate_content(
                response_prompt, generation_config=self.conversational_config
            )

            response_text = response.text.strip()
            if config_warning:
                response_text = f"{config_warning}\n\n{response_text}"

            # Extract all metadata in parallel using the new extractors
            metadata, schedule_analysis, action_plan_analysis = (
                await self._extract_all_metadata(user_message, response_text, context)
            )

            # Build final response
            final_response = self._build_final_response(
                response_text,
                crisis_assessment,
                metadata,
                schedule_analysis,
                action_plan_analysis,
                config_warning,
            )

            return final_response

        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            return self._create_fallback_response(crisis_assessment, config_warning, e)

    def _build_response_prompt(self, context: str, user_message: str) -> str:
        """Build the prompt for response generation."""
        return f"""
{self.system_prompt}

{self.conversation_guidelines}

CONVERSATION CONTEXT:
{context}

USER MESSAGE: {user_message}
"""

    async def _extract_all_metadata(
        self, user_message: str, response_text: str, context: str
    ) -> tuple:
        """Extract all metadata using the new modular extractors."""

        # Run extractions in parallel for efficiency
        import asyncio

        # Session metadata extraction (simplified version)
        metadata_task = self._extract_session_metadata(user_message, response_text)

        # Schedule analysis
        schedule_opportunity = self.schedule_analyzer.analyze_opportunity(
            user_message, response_text, context
        )
        schedule_task = self.schedule_extractor.extract_information(
            user_message, response_text, context, schedule_opportunity
        )

        # Action plan analysis
        action_plan_opportunity = self.action_plan_analyzer.analyze_opportunity(
            user_message, response_text, context
        )
        action_plan_task = self.action_plan_extractor.extract_information(
            user_message, response_text, context, action_plan_opportunity
        )

        # Wait for all extractions to complete
        metadata, schedule_analysis, action_plan_analysis = await asyncio.gather(
            metadata_task, schedule_task, action_plan_task
        )

        return metadata, schedule_analysis, action_plan_analysis

    def _build_final_response(
        self,
        response_text: str,
        crisis_assessment: Dict[str, Any],
        metadata: Dict[str, Any],
        schedule_analysis: Dict[str, Any],
        action_plan_analysis: Dict[str, Any],
        config_warning: Optional[str],
    ) -> Dict[str, Any]:
        """Build the final response dictionary."""
        return {
            "response": response_text,
            "crisis_level": crisis_assessment["level"],
            "crisis_explanation": crisis_assessment["explanation"],
            "timestamp": datetime.utcnow(),
            "resources_provided": self._extract_resources(response_text),
            "coping_strategies": self._extract_coping_strategies(response_text),
            "session_metadata": metadata,
            "crisis_flag": crisis_assessment["crisis_flag"],
            "configuration_warning": config_warning is not None,
            "schedule_analysis": schedule_analysis,
            "action_plan_analysis": action_plan_analysis,
        }

    def _create_fallback_response(
        self,
        crisis_assessment: Dict[str, Any],
        config_warning: Optional[str],
        error: Exception,
    ) -> Dict[str, Any]:
        """Create fallback response when main generation fails."""
        fallback_response = "I'm here to listen and support you. While I'm having technical difficulties right now, please know that your feelings are valid and you don't have to go through this alone."

        if config_warning:
            fallback_response = f"{config_warning}\n\n{fallback_response}"

        return {
            "response": fallback_response,
            "crisis_level": crisis_assessment["level"],
            "crisis_explanation": "Technical error occurred",
            "timestamp": datetime.utcnow(),
            "resources_provided": ["crisis_hotline"],
            "coping_strategies": ["seek_immediate_help"],
            "session_metadata": {},
            "crisis_flag": False,
            "configuration_warning": True,
            "schedule_analysis": {"should_suggest_scheduling": False},
            "action_plan_analysis": {"should_suggest_action_plan": False},
            "error": str(error),
        }

    async def _assess_crisis_level(self, user_message: str) -> Dict[str, str]:
        """Assess if the user message indicates a mental health crisis."""
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries + 1):
            try:
                assessment_response = self.model.generate_content(
                    self.crisis_detection_prompt.format(content=user_message),
                    generation_config=self.crisis_config,
                )

                assessment_text = assessment_response.text.strip()

                # Parse the structured response
                crisis_level = "SUPPORT"  # default
                crisis_flag = False  # default
                explanation = assessment_text

                # Extract LEVEL
                if "LEVEL:" in assessment_text:
                    level_line = [
                        line
                        for line in assessment_text.split("\n")
                        if line.startswith("LEVEL:")
                    ]
                    if level_line:
                        level_value = level_line[0].replace("LEVEL:", "").strip()
                        if level_value in ["CRISIS", "CONCERN", "SUPPORT"]:
                            crisis_level = level_value

                # Extract FLAG
                if "FLAG:" in assessment_text:
                    flag_line = [
                        line
                        for line in assessment_text.split("\n")
                        if line.startswith("FLAG:")
                    ]
                    if flag_line:
                        flag_value = flag_line[0].replace("FLAG:", "").strip().upper()
                        crisis_flag = flag_value == "TRUE"

                # Extract REASONING for explanation
                if "REASONING:" in assessment_text:
                    reasoning_lines = assessment_text.split("REASONING:", 1)
                    if len(reasoning_lines) > 1:
                        explanation = reasoning_lines[1].strip()

                return {
                    "level": crisis_level,
                    "explanation": explanation,
                    "crisis_flag": crisis_flag,
                }

            except Exception as e:
                error_str = str(e)

                # Handle rate limiting with exponential backoff
                if (
                    "429" in error_str
                    or "quota" in error_str.lower()
                    or "rate" in error_str.lower()
                ):
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            "level": "CONCERN",
                            "explanation": f"Unable to assess due to rate limiting after {max_retries + 1} attempts",
                            "crisis_flag": False,
                        }
                else:
                    break

        # Default fallback
        return {
            "level": "SUPPORT",
            "explanation": "Unable to assess crisis level due to technical error",
            "crisis_flag": False,
        }

    async def _extract_session_metadata(
        self, user_message: str, assistant_response: str
    ) -> Dict[str, Any]:
        """Extract metadata for visualization and data capture."""
        metadata_prompt = f"""
Based on this conversation exchange, extract metadata for visualization and therapeutic insights:

USER MESSAGE: {user_message}
ASSISTANT RESPONSE: {assistant_response}

Extract and return the following metadata in JSON format:
{{
  "transcript": "Full user message transcript",
  "ground_emotion": "Primary emotion detected",
  "scene_title": "Brief descriptive title for this emotional moment",
  "metaphor_prompt": "Visual metaphor that captures the user's emotional state",
  "cognitive_load": "high/medium/low",
  "temporal_tag": "new/familiar",
  "color_palette": ["array", "of", "colors"],
  "texture_descriptor": "Physical texture",
  "temp_descriptor": "Temperature association",
  "sketch_motion": "Type of movement",
  "scene_description": "Brief scene description",
  "body_locus": "Where emotion is felt",
  "sketch_shape": "Geometric or organic shape"
}}
"""

        try:
            metadata_response = self.model.generate_content(
                metadata_prompt, generation_config=self.metadata_config
            )
            import json

            metadata_text = metadata_response.text.strip()
            start_idx = metadata_text.find("{")
            end_idx = metadata_text.rfind("}") + 1

            if start_idx != -1 and end_idx != -1:
                json_str = metadata_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return self._create_fallback_metadata(user_message)
        except Exception:
            return self._create_fallback_metadata(user_message)

    def _create_fallback_metadata(self, user_message: str) -> Dict[str, Any]:
        """Create basic metadata when automated extraction fails."""
        return {
            "transcript": user_message,
            "ground_emotion": "support_needed",
            "scene_title": "Moment of Connection",
            "metaphor_prompt": "reaching out in the darkness",
            "cognitive_load": "medium",
            "temporal_tag": "new",
            "color_palette": ["soft blue", "warm gray"],
            "texture_descriptor": "gentle",
            "temp_descriptor": "room temperature",
            "sketch_motion": "reaching",
            "scene_description": "A moment of vulnerability and courage",
            "body_locus": "heart",
            "sketch_shape": "flowing",
        }

    def _build_conversation_context(
        self, current_message: str, memory_context: Optional[MemoryContext] = None
    ) -> str:
        """Build context from memory for the conversation."""
        if not memory_context:
            return "This appears to be a new conversation."

        context_parts = []

        # Add recent conversation context
        if memory_context.short_term:
            recent_memories = memory_context.short_term[-3:]
            context_parts.append("Recent conversation context:")
            for memory in recent_memories:
                context_parts.append(f"- {memory.content}")

        # Add relevant long-term context
        if memory_context.long_term:
            context_parts.append("\nRelevant background information:")
            for memory in memory_context.long_term[:2]:
                context_parts.append(f"- {memory.content}")

        # Add digest if available
        if memory_context.digest:
            context_parts.append(f"\nOverall context: {memory_context.digest}")

        return (
            "\n".join(context_parts)
            if context_parts
            else "No previous context available."
        )

    def _extract_resources(self, response_text: str) -> List[str]:
        """Extract mentioned resources from the response."""
        resources = []
        response_lower = response_text.lower()

        resource_keywords = {
            "therapy": "therapy",
            "counseling": "counseling",
            "hotline": "crisis_hotline",
            "therapist": "therapist",
            "psychiatrist": "psychiatrist",
            "support group": "support_group",
            "meditation": "meditation_app",
            "crisis": "crisis_resources",
        }

        for keyword, resource in resource_keywords.items():
            if keyword in response_lower:
                resources.append(resource)

        return list(set(resources))

    def _extract_coping_strategies(self, response_text: str) -> List[str]:
        """Extract mentioned coping strategies from the response."""
        strategies = []
        response_lower = response_text.lower()

        strategy_keywords = {
            "breathing": "breathing_exercise",
            "mindfulness": "mindfulness",
            "grounding": "grounding_technique",
            "journal": "journaling",
            "exercise": "physical_activity",
            "sleep": "sleep_hygiene",
            "meditation": "meditation",
            "relaxation": "relaxation_technique",
        }

        for keyword, strategy in strategy_keywords.items():
            if keyword in response_lower:
                strategies.append(strategy)

        return list(set(strategies))

    def _get_configuration_warning(self) -> Optional[str]:
        """Get user-facing configuration warning if environment variables are missing."""
        missing_configs = []

        if "CONFIGURATION ERROR" in self.system_prompt:
            missing_configs.append("system prompts")
        if "CONFIGURATION ERROR" in self.conversation_guidelines:
            missing_configs.append("conversation guidelines")
        if "CONFIGURATION ERROR" in self.crisis_detection_prompt:
            missing_configs.append("crisis detection")

        if missing_configs:
            return f"⚠️ Notice: This assistant is running with limited configuration. Missing: {', '.join(missing_configs)}. Some features may not work as expected."

        return None

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process a chat message with enhanced crisis intervention.
        """
        try:
            # Generate the main response
            response_data = await self.generate_response(
                user_message=message,
                memory_context=None,
                user_id=user_id,
            )

            # Check if crisis intervention is needed
            if (
                response_data.get("crisis_flag")
                or response_data.get("crisis_level") == "CRISIS"
            ):
                logger.warning(
                    f"Crisis detected for user {user_id}: {response_data.get('crisis_explanation')}"
                )

                # Initiate crisis intervention using the new manager
                await CrisisInterventionManager.handle_crisis_intervention(
                    user_id=user_id,
                    crisis_data=response_data,
                    user_message=message,
                    conversation_context=conversation_context,
                )

            return response_data["response"]

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {str(e)}")
            return "I'm here to support you, but I'm having technical difficulties right now. If you're in crisis, please reach out to emergency services or a crisis hotline immediately."

    async def provide_crisis_resources(self) -> Dict[str, Any]:
        """Provide immediate crisis resources."""
        return {
            "message": "If you're having thoughts of self-harm or suicide, please reach out for help immediately. You are not alone, and there are people who want to support you.",
            "crisis_resources": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "phone": "988",
                    "description": "24/7 free and confidential support",
                },
                {
                    "name": "Crisis Text Line",
                    "text": "Text HOME to 741741",
                    "description": "24/7 crisis support via text",
                },
                {
                    "name": "International Association for Suicide Prevention",
                    "website": "https://www.iasp.info/resources/Crisis_Centres/",
                    "description": "Global crisis center directory",
                },
            ],
            "immediate_actions": [
                "Call 911 or go to your nearest emergency room if in immediate danger",
                "Reach out to a trusted friend, family member, or mental health professional",
                "Remove any means of self-harm from your immediate environment",
                "Stay with someone or ask someone to stay with you",
                "Consider calling a crisis hotline to talk through your feelings",
            ],
        }
