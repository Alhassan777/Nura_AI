"""
Response Generator Component
Handles fast response generation with crisis detection.
"""

import logging
from typing import Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Handles fast response generation for different chat modes."""

    def __init__(self, model: genai.GenerativeModel, generation_config):
        self.model = model
        self.generation_config = generation_config

    async def generate_fast_response(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any],
        mode: str,
        mode_prompts: Dict[str, str],
        mode_guidelines: Dict[str, str],
    ) -> Dict[str, Any]:
        """Generate response optimized for speed."""
        # Build mode-specific prompt
        system_prompt = mode_prompts.get(mode, mode_prompts["general"])
        guidelines = mode_guidelines.get(mode, mode_guidelines["general"])

        prompt = f"""
{system_prompt}

{guidelines}

CONTEXT: {context.get('context', 'New conversation')}

USER MESSAGE: {message}

Please provide a supportive, empathetic response. Focus on immediate emotional support.
"""

        try:
            response = self.model.generate_content(
                prompt, generation_config=self.generation_config
            )

            response_text = response.text.strip()

            # Quick crisis check (simple keywords for immediate response)
            immediate_crisis = self._quick_crisis_check(message)
            needs_resources = self._quick_resource_check(response_text)

            return {
                "response": response_text,
                "immediate_crisis": immediate_crisis,
                "needs_resources": needs_resources,
            }

        except Exception as e:
            logger.error(f"Error generating fast response: {e}")
            return {
                "response": "I hear you and I'm here to support you. Let me take a moment to provide the best response.",
                "immediate_crisis": False,
                "needs_resources": False,
            }

    def _quick_crisis_check(self, message: str) -> bool:
        """Quick crisis detection using simple keywords."""
        crisis_keywords = [
            "suicide",
            "kill myself",
            "end it all",
            "not worth living",
            "hurt myself",
            "self harm",
            "better off dead",
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)

    def _quick_resource_check(self, response: str) -> bool:
        """Check if response mentions resources."""
        resource_keywords = ["hotline", "counselor", "therapist", "crisis", "emergency"]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in resource_keywords)

    def build_minimal_context(self, recent_messages: list) -> str:
        """Build minimal context from recent messages for fast response."""
        if not recent_messages:
            return "No recent conversation context available."

        context_parts = ["Recent conversation:"]
        for msg in recent_messages[-3:]:  # Only last 3 messages
            content = msg.get("content", "")[:200]  # Truncate for speed
            context_parts.append(f"- {content}")

        return "\n".join(context_parts)
