import os
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime

from ..types import MemoryItem, MemoryContext
from ..config import Config

# Set up logging
logger = logging.getLogger(__name__)


class MentalHealthAssistant:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Define generation configurations for different use cases
        self._setup_generation_configs()

        self.model = genai.GenerativeModel(
            Config.GEMINI_MODEL, generation_config=self.conversational_config
        )

        # Load prompts from configuration
        self.system_prompt = Config.get_mental_health_system_prompt()
        self.conversation_guidelines = Config.get_conversation_guidelines()
        self.crisis_detection_prompt = Config.get_crisis_detection_prompt()

        # Check if we're using fallbacks and warn
        self._check_configuration()

    def _setup_generation_configs(self):
        """Define all generation configurations in one place for consistency."""
        # Main conversational responses - more creative and varied
        self.conversational_config = genai.types.GenerationConfig(
            temperature=0.8,  # Higher temperature for more creative, varied responses
            top_p=0.9,  # Use nucleus sampling for better diversity
            top_k=40,  # Allow selection from top 40 tokens
            max_output_tokens=2048,  # Allow longer responses when needed
            candidate_count=1,  # Generate one response
        )

        # Crisis assessment - more deterministic and consistent
        self.crisis_config = genai.types.GenerationConfig(
            temperature=0.3,  # Lower temperature for more consistent crisis detection
            top_p=0.8,
            top_k=20,
            max_output_tokens=512,
            candidate_count=1,
        )

        # Metadata extraction - balanced for structured output
        self.metadata_config = genai.types.GenerationConfig(
            temperature=0.5,  # Moderate temperature for structured but varied metadata
            top_p=0.85,
            top_k=30,
            max_output_tokens=1024,
            candidate_count=1,
        )

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
            error_msg = f"⚠️  CONFIGURATION ERROR: Missing environment variables: {', '.join(missing_configs)}. Using fallback configurations with limited functionality. Please set these in your .env file for full mental health assistant capabilities."
            logger.error(error_msg)
            print(f"\n{error_msg}\n")

    async def generate_response(
        self,
        user_message: str,
        memory_context: Optional[MemoryContext] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a mental health assistant response."""

        # Check if we're in degraded mode and include warning
        config_warning = self._get_configuration_warning()

        # First, check for crisis indicators
        crisis_assessment = await self._assess_crisis_level(user_message)

        # Build context for the response
        context = self._build_conversation_context(user_message, memory_context)

        # Generate the main response
        response_prompt = f"""
{self.system_prompt}

{self.conversation_guidelines}

CONVERSATION CONTEXT:
{context}

USER MESSAGE: {user_message}

Please provide a compassionate, helpful response that follows the guidelines above. Consider the user's emotional state and provide appropriate support, coping strategies, or resources as needed.

If this is a crisis situation, prioritize safety and provide immediate resources while maintaining a supportive tone.
"""

        try:
            response = self.model.generate_content(
                response_prompt, generation_config=self.conversational_config
            )

            # Add configuration warning to response if in degraded mode
            response_text = response.text.strip()
            if config_warning:
                response_text = f"{config_warning}\n\n{response_text}"

            # Extract metadata for visualization and data capture
            metadata = await self._extract_session_metadata(user_message, response_text)

            return {
                "response": response_text,
                "crisis_level": crisis_assessment["level"],
                "crisis_explanation": crisis_assessment["explanation"],
                "timestamp": datetime.utcnow(),
                "resources_provided": self._extract_resources(response_text),
                "coping_strategies": self._extract_coping_strategies(response_text),
                "session_metadata": metadata,
                "crisis_flag": "CRISIS" in crisis_assessment["level"],
                "configuration_warning": config_warning is not None,
            }

        except Exception as e:
            # Enhanced fallback response with configuration warning
            fallback_response = "I'm here to listen and support you. While I'm having technical difficulties right now, please know that your feelings are valid and you don't have to go through this alone. If you're in crisis, please reach out to a mental health professional or crisis hotline immediately."

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
                "error": str(e),
            }

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
            return f"⚠️ Notice: This assistant is running with limited configuration. Missing: {', '.join(missing_configs)}. Some features may not work as expected. Please contact support if this continues."

        return None

    async def _assess_crisis_level(self, user_message: str) -> Dict[str, str]:
        """Assess if the user message indicates a mental health crisis."""
        try:
            assessment_response = self.model.generate_content(
                self.crisis_detection_prompt.format(content=user_message),
                generation_config=self.crisis_config,
            )

            assessment_text = assessment_response.text.strip()

            if "CRISIS" in assessment_text:
                return {"level": "CRISIS", "explanation": assessment_text}
            elif "CONCERN" in assessment_text:
                return {"level": "CONCERN", "explanation": assessment_text}
            else:
                return {"level": "SUPPORT", "explanation": assessment_text}

        except Exception:
            # Default to support level if assessment fails
            return {"level": "SUPPORT", "explanation": "Unable to assess crisis level"}

    def _build_conversation_context(
        self, current_message: str, memory_context: Optional[MemoryContext] = None
    ) -> str:
        """Build context from memory for the conversation."""
        if not memory_context:
            return "This appears to be a new conversation."

        context_parts = []

        # Add recent conversation context
        if memory_context.short_term:
            recent_memories = memory_context.short_term[-3:]  # Last 3 interactions
            context_parts.append("Recent conversation context:")
            for memory in recent_memories:
                context_parts.append(f"- {memory.content}")

        # Add relevant long-term context
        if memory_context.long_term:
            context_parts.append("\nRelevant background information:")
            for memory in memory_context.long_term[:2]:  # Top 2 relevant memories
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

        return list(set(resources))  # Remove duplicates

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

        return list(set(strategies))  # Remove duplicates

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

    async def _extract_session_metadata(
        self, user_message: str, assistant_response: str
    ) -> Dict[str, Any]:
        """Extract metadata for visualization and data capture (internal use only)."""
        metadata_prompt = f"""
Based on this conversation exchange, extract metadata for visualization and therapeutic insights:

USER MESSAGE: {user_message}
ASSISTANT RESPONSE: {assistant_response}

Extract and return the following metadata in JSON format:
{{
  "transcript": "Full user message transcript",
  "ground_emotion": "Primary emotion detected (e.g., anxiety, sadness, hope, confusion)",
  "scene_title": "Brief descriptive title for this emotional moment",
  "metaphor_prompt": "Visual metaphor that captures the user's emotional state",
  "cognitive_load": "high/medium/low - user's mental processing capacity",
  "temporal_tag": "new/familiar - whether this seems like a new or recurring issue",
  "color_palette": ["array", "of", "colors", "that", "match", "the", "mood"],
  "texture_descriptor": "Physical texture that matches the emotional quality",
  "temp_descriptor": "Temperature association with the emotional state",
  "sketch_motion": "Type of movement that represents their emotional state",
  "scene_description": "Brief scene that visualizes their internal experience",
  "body_locus": "Where in the body this emotion might be felt",
  "sketch_shape": "Geometric or organic shape that represents their state"
}}

Focus on therapeutic insight and emotional understanding. Keep all fields concise and meaningful.
"""

        try:
            metadata_response = self.model.generate_content(
                metadata_prompt, generation_config=self.metadata_config
            )
            import json

            # Parse the JSON response
            metadata_text = metadata_response.text.strip()
            # Find JSON in the response
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
