"""
Mode Detector Component
Handles mode detection and suggestions for better user experience.
"""

import logging
from typing import Dict, Any, Optional, List
import random

logger = logging.getLogger(__name__)


class ModeDetector:
    """Handles mode detection and suggestions."""

    def __init__(self):
        self.mode_keywords = self._load_mode_keywords()
        self.suggestion_messages = self._load_suggestion_messages()

    def _load_mode_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Load keywords for mode detection."""
        return {
            "action_plan": {
                "primary": [
                    "help me",
                    "what should i do",
                    "how do i",
                    "plan",
                    "steps",
                    "goal",
                    "achieve",
                    "improve",
                    "change",
                    "start",
                    "begin",
                ],
                "secondary": [
                    "need to",
                    "want to",
                    "trying to",
                    "working on",
                    "focus on",
                    "get better",
                    "move forward",
                    "make progress",
                    "solve",
                ],
            },
            "visualization": {
                "primary": [
                    "feel like",
                    "imagine",
                    "picture",
                    "visualize",
                    "looks like",
                    "colors",
                    "drawing",
                    "art",
                    "creative",
                    "express",
                ],
                "secondary": [
                    "see",
                    "vision",
                    "image",
                    "metaphor",
                    "symbol",
                    "represent",
                    "show",
                    "paint",
                    "create",
                    "design",
                ],
            },
            "general": {
                "primary": [
                    "feeling",
                    "emotion",
                    "sad",
                    "happy",
                    "anxious",
                    "stressed",
                    "talk",
                    "listen",
                    "support",
                    "understand",
                ],
                "secondary": [
                    "need someone",
                    "lonely",
                    "overwhelmed",
                    "confused",
                    "just want to",
                    "share",
                    "vent",
                    "discuss",
                ],
            },
        }

    def _load_suggestion_messages(self) -> Dict[str, List[Dict[str, str]]]:
        """Load varied suggestion messages for each mode."""
        return {
            "action_plan": [
                {
                    "suggestion": "It sounds like you're looking for practical steps to move forward. Would you like me to help you create a detailed action plan?",
                    "benefit": "I can help break down your goals into manageable steps with timelines and resources.",
                },
                {
                    "suggestion": "I notice you're thinking about making changes. Would it be helpful if we worked together on a structured plan?",
                    "benefit": "We can create a step-by-step roadmap that takes your specific situation into account.",
                },
                {
                    "suggestion": "You seem ready to take action on this. Would you like to explore creating a concrete plan together?",
                    "benefit": "I can guide you through breaking this down into achievable milestones.",
                },
            ],
            "visualization": [
                {
                    "suggestion": "I notice you're describing some vivid feelings. Would you like to explore expressing these emotions through visual art?",
                    "benefit": "Sometimes creating visual representations can help us understand and process emotions in new ways.",
                },
                {
                    "suggestion": "Your emotions sound very rich and complex. Would it help to create a visual representation of what you're experiencing?",
                    "benefit": "Art can sometimes capture feelings that words alone can't fully express.",
                },
                {
                    "suggestion": "I can sense the depth of what you're feeling. Would you be interested in exploring this through creative expression?",
                    "benefit": "Visual art can offer a different pathway to understanding and processing emotions.",
                },
            ],
            "general": [
                {
                    "suggestion": "It seems like you might benefit from some emotional support and validation right now.",
                    "benefit": "I'm here to listen and provide the emotional support you need.",
                },
                {
                    "suggestion": "I can hear that you're going through something important. Would you like to talk through your feelings?",
                    "benefit": "Sometimes just having someone listen and understand can make a real difference.",
                },
            ],
        }

    async def detect_mode(self, message: str, context: Dict[str, Any] = None) -> str:
        """Auto-detect chat mode based on message content with enhanced accuracy."""
        message_lower = message.lower()
        context_text = ""

        if context:
            context_text = context.get("context", "").lower()

        full_text = f"{context_text} {message_lower}"

        # Score each mode based on keyword matches
        mode_scores = {}

        for mode, keywords in self.mode_keywords.items():
            score = 0

            # Primary keywords get higher weight
            for keyword in keywords["primary"]:
                if keyword in full_text:
                    score += 3

            # Secondary keywords get lower weight
            for keyword in keywords["secondary"]:
                if keyword in full_text:
                    score += 1

            mode_scores[mode] = score

        # Return the mode with highest score, default to general
        if max(mode_scores.values()) == 0:
            return "general"

        return max(mode_scores, key=mode_scores.get)

    async def suggest_mode_switch(
        self, current_mode: str, message: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Suggest a different mode if it would be more helpful."""
        try:
            # Detect if message would benefit from different mode
            detected_mode = await self.detect_mode(message, context)

            if detected_mode != current_mode:
                # Get a random suggestion message to avoid repetition
                suggestions = self.suggestion_messages[detected_mode]
                selected_suggestion = random.choice(suggestions)

                return {
                    "suggested_mode": detected_mode,
                    "current_mode": current_mode,
                    "suggestion_text": selected_suggestion["suggestion"],
                    "benefit": selected_suggestion["benefit"],
                    "confidence": self._calculate_confidence(message, detected_mode),
                }

            return None

        except Exception as e:
            logger.error(f"Error suggesting mode switch: {e}")
            return None

    def _calculate_confidence(self, message: str, detected_mode: str) -> float:
        """Calculate confidence score for mode detection."""
        message_lower = message.lower()
        keywords = self.mode_keywords[detected_mode]

        total_keywords = len(keywords["primary"]) + len(keywords["secondary"])
        matched_keywords = 0

        for keyword in keywords["primary"]:
            if keyword in message_lower:
                matched_keywords += 2  # Primary keywords count double

        for keyword in keywords["secondary"]:
            if keyword in message_lower:
                matched_keywords += 1

        # Normalize to 0-1 scale
        confidence = min(matched_keywords / (total_keywords * 0.5), 1.0)
        return round(confidence, 2)

    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about available modes."""
        return {
            "modes": {
                "general": {
                    "name": "General Support",
                    "description": "Emotional support and validation through active listening",
                    "best_for": [
                        "Emotional processing",
                        "Feeling heard",
                        "General support",
                        "Crisis situations",
                    ],
                    "keywords": self.mode_keywords["general"]["primary"][:5],
                },
                "action_plan": {
                    "name": "Action Planning",
                    "description": "Practical solution-oriented collaborative planning",
                    "best_for": [
                        "Goal setting",
                        "Problem solving",
                        "Creating plans",
                        "Making progress",
                    ],
                    "keywords": self.mode_keywords["action_plan"]["primary"][:5],
                },
                "visualization": {
                    "name": "Creative Expression",
                    "description": "Visual and creative expression of emotions through art",
                    "best_for": [
                        "Emotional expression",
                        "Creative therapy",
                        "Visual processing",
                        "Art creation",
                    ],
                    "keywords": self.mode_keywords["visualization"]["primary"][:5],
                },
            },
            "auto_detection": True,
            "mode_switching": False,
        }
