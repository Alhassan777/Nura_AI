"""
Information Gatherer Component
Handles assessment of information completeness and generates follow-up questions.
"""

import logging
from typing import Dict, Any, List
import random

logger = logging.getLogger(__name__)


class InformationGatherer:
    """Handles information gathering for different chat modes."""

    def __init__(self):
        self.question_variations = self._load_question_variations()

    def _load_question_variations(self) -> Dict[str, List[str]]:
        """Load different variations of questions to avoid repetition."""
        return {
            "action_plan": {
                "specific_goal": [
                    "What specific outcome would you like to achieve?",
                    "Can you help me understand what success looks like for you?",
                    "What's the main thing you're hoping to accomplish?",
                    "If everything went perfectly, what would that look like?",
                ],
                "current_situation": [
                    "Can you tell me more about your current situation?",
                    "What's happening in your life right now that's bringing this up?",
                    "Help me understand where you're starting from.",
                    "What's the current state of things for you?",
                ],
                "timeline": [
                    "What timeframe are you working with? When would you like to achieve this?",
                    "Do you have any deadlines or time pressures I should know about?",
                    "How urgent is this for you - are we talking days, weeks, or months?",
                    "When would be ideal for you to see progress on this?",
                ],
                "available_resources": [
                    "What resources, skills, or support do you currently have available?",
                    "Who or what can help you with this journey?",
                    "What strengths do you bring to this challenge?",
                    "What tools or support systems are already in your corner?",
                ],
                "potential_obstacles": [
                    "What challenges or obstacles do you think you might face?",
                    "What has held you back from this in the past?",
                    "Are there any roadblocks you're already anticipating?",
                    "What concerns do you have about moving forward?",
                ],
            },
            "visualization": {
                "emotional_state": [
                    "How are you feeling right now? Can you describe the emotion?",
                    "What's the strongest emotion you're experiencing?",
                    "If you had to name what you're feeling, what would it be?",
                    "What emotion is most present for you in this moment?",
                ],
                "visual_description": [
                    "If this feeling had a shape, color, or form, what would it look like?",
                    "When you close your eyes and think about this emotion, what do you see?",
                    "How would you paint or draw this feeling?",
                    "If this emotion was a landscape, what would it be?",
                ],
                "emotional_intensity": [
                    "How strong is this feeling? Is it gentle, moderate, or overwhelming?",
                    "On a scale where a whisper is 1 and a thunderstorm is 10, where is this emotion?",
                    "Is this feeling more like a gentle breeze or a powerful wave?",
                    "How much space is this emotion taking up inside you right now?",
                ],
            },
        }

    async def assess_action_plan_readiness(
        self, user_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if we have enough information to create a comprehensive action plan."""
        try:
            conversation_context = context.get("context", "")
            full_text = f"{conversation_context} {message}".lower()

            # Enhanced keyword detection with more nuanced patterns
            has_goal = any(
                keyword in full_text
                for keyword in [
                    "want to",
                    "need to",
                    "goal",
                    "achieve",
                    "improve",
                    "change",
                    "become",
                    "get better at",
                    "work on",
                    "focus on",
                    "accomplish",
                ]
            )

            has_current_situation = any(
                keyword in full_text
                for keyword in [
                    "currently",
                    "right now",
                    "situation",
                    "problem",
                    "struggling",
                    "dealing with",
                    "facing",
                    "experiencing",
                    "going through",
                ]
            )

            has_timeline = any(
                keyword in full_text
                for keyword in [
                    "when",
                    "by",
                    "deadline",
                    "soon",
                    "time",
                    "quickly",
                    "urgent",
                    "asap",
                    "eventually",
                    "long term",
                    "short term",
                ]
            )

            has_resources = any(
                keyword in full_text
                for keyword in [
                    "have",
                    "can",
                    "able",
                    "resources",
                    "support",
                    "help",
                    "skills",
                    "experience",
                    "knowledge",
                    "tools",
                    "access",
                ]
            )

            has_obstacles = any(
                keyword in full_text
                for keyword in [
                    "difficult",
                    "challenge",
                    "problem",
                    "obstacle",
                    "hard",
                    "struggle",
                    "barrier",
                    "issue",
                    "concern",
                    "worry",
                ]
            )

            info_score = sum(
                [
                    has_goal,
                    has_current_situation,
                    has_timeline,
                    has_resources,
                    has_obstacles,
                ]
            )

            missing_info = []
            if not has_goal:
                missing_info.append("specific_goal")
            if not has_current_situation:
                missing_info.append("current_situation")
            if not has_timeline:
                missing_info.append("timeline")
            if not has_resources:
                missing_info.append("available_resources")
            if not has_obstacles:
                missing_info.append("potential_obstacles")

            return {
                "ready": info_score >= 3,  # Need at least 3 components
                "info_score": info_score,
                "missing_info": missing_info,
                "has_components": {
                    "goal": has_goal,
                    "situation": has_current_situation,
                    "timeline": has_timeline,
                    "resources": has_resources,
                    "obstacles": has_obstacles,
                },
            }

        except Exception as e:
            logger.error(f"Error assessing action plan readiness: {e}")
            return {"ready": False, "error": str(e)}

    async def generate_action_plan_questions(
        self,
        message: str,
        missing_info: List[str],
        conversation_history: List[str] = None,
    ) -> List[str]:
        """Generate varied follow-up questions to avoid repetition."""
        questions = []

        # Track previously asked questions to avoid repetition
        asked_questions = set()
        if conversation_history:
            for msg in conversation_history:
                if "?" in msg:
                    asked_questions.add(msg.lower().strip())

        # Priority order for information gathering
        priority_order = [
            "specific_goal",
            "current_situation",
            "timeline",
            "available_resources",
            "potential_obstacles",
        ]

        for info_type in priority_order:
            if info_type in missing_info and len(questions) < 2:
                available_questions = self.question_variations["action_plan"][info_type]

                # Find a question we haven't asked before
                for question in available_questions:
                    if question.lower() not in asked_questions:
                        questions.append(question)
                        break
                else:
                    # If all variations have been used, pick a random one
                    questions.append(random.choice(available_questions))

        return questions

    async def assess_visualization_readiness(
        self, user_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if we have enough emotional information for meaningful visualization."""
        try:
            conversation_context = context.get("context", "")
            full_text = f"{conversation_context} {message}".lower()

            # Enhanced emotional content detection
            emotion_keywords = [
                "feel",
                "feeling",
                "emotion",
                "sad",
                "happy",
                "angry",
                "anxious",
                "excited",
                "frustrated",
                "overwhelmed",
                "peaceful",
                "stressed",
                "depressed",
                "joyful",
                "worried",
                "calm",
                "nervous",
                "content",
                "disappointed",
                "hopeful",
                "scared",
                "confident",
                "lonely",
            ]

            imagery_keywords = [
                "like",
                "looks",
                "seems",
                "appears",
                "imagine",
                "picture",
                "visualize",
                "see",
                "vision",
                "image",
                "color",
                "shape",
                "form",
                "texture",
            ]

            metaphor_keywords = [
                "storm",
                "ocean",
                "mountain",
                "fire",
                "ice",
                "darkness",
                "light",
                "colors",
                "rainbow",
                "cloud",
                "river",
                "forest",
                "desert",
                "garden",
                "thunder",
                "sunshine",
                "shadow",
                "bridge",
                "wall",
                "door",
            ]

            intensity_keywords = [
                "very",
                "extremely",
                "really",
                "so",
                "quite",
                "little",
                "bit",
                "much",
                "overwhelming",
                "intense",
                "mild",
                "strong",
                "weak",
                "powerful",
                "gentle",
                "fierce",
                "subtle",
                "deep",
                "surface",
            ]

            has_emotion = any(keyword in full_text for keyword in emotion_keywords)
            has_imagery = any(keyword in full_text for keyword in imagery_keywords)
            has_metaphor = any(keyword in full_text for keyword in metaphor_keywords)
            has_intensity = any(keyword in full_text for keyword in intensity_keywords)

            info_score = sum([has_emotion, has_imagery, has_metaphor, has_intensity])

            missing_info = []
            if not has_emotion:
                missing_info.append("emotional_state")
            if not has_imagery:
                missing_info.append("visual_description")
            if not has_intensity:
                missing_info.append("emotional_intensity")

            return {
                "ready": info_score >= 2,  # Need at least emotion + one other component
                "info_score": info_score,
                "missing_info": missing_info,
                "has_components": {
                    "emotion": has_emotion,
                    "imagery": has_imagery,
                    "metaphor": has_metaphor,
                    "intensity": has_intensity,
                },
            }

        except Exception as e:
            logger.error(f"Error assessing visualization readiness: {e}")
            return {"ready": False, "error": str(e)}

    async def generate_visualization_questions(
        self,
        message: str,
        missing_info: List[str],
        conversation_history: List[str] = None,
    ) -> List[str]:
        """Generate varied visualization questions to avoid repetition."""
        questions = []

        # Track previously asked questions
        asked_questions = set()
        if conversation_history:
            for msg in conversation_history:
                if "?" in msg:
                    asked_questions.add(msg.lower().strip())

        for info_type in missing_info:
            if (
                info_type in self.question_variations["visualization"]
                and len(questions) < 2
            ):
                available_questions = self.question_variations["visualization"][
                    info_type
                ]

                # Find a question we haven't asked before
                for question in available_questions:
                    if question.lower() not in asked_questions:
                        questions.append(question)
                        break
                else:
                    # If all variations have been used, pick a random one
                    questions.append(random.choice(available_questions))

        return questions

    def generate_gathering_message(self, mode: str, missing_info: List[str]) -> str:
        """Generate a natural, varied message for information gathering."""

        messages = {
            "action_plan": [
                "I'd love to help you create a detailed action plan. Let me understand your situation better first.",
                "Creating a solid plan requires understanding the full picture. Can you help me with a few details?",
                "To build the most helpful action plan for you, I need to understand a bit more about your goals and situation.",
                "Let's work together to create a plan that really fits your needs. I have a few questions to get us started.",
            ],
            "visualization": [
                "I'd love to help you create a visual representation of your feelings. Let me understand your emotions better first.",
                "Creating meaningful art from emotions requires understanding the full emotional landscape. Can you share more?",
                "To create something that truly captures your feelings, I need to understand the emotional details better.",
                "Let's explore your emotions together so I can help you express them visually.",
            ],
        }

        return random.choice(messages.get(mode, messages["action_plan"]))
