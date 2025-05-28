"""
Prompt builder for image generation that collects emotional and contextual data
from various memory sources and builds comprehensive prompts.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..memory.memoryService import MemoryService


class PromptBuilder:
    """Builds rich prompts for image generation by collecting user context."""

    def __init__(self, redis_store=None, vector_store=None):
        # For backward compatibility, accept storage objects but use MemoryService
        self.memory_service = MemoryService()

    async def build_image_prompt_context(
        self,
        user_id: str,
        current_input: str,
        include_long_term: bool = False,
        identified_emotion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for image generation prompt.

        Args:
            user_id: The user's unique identifier
            current_input: The current user input/message
            include_long_term: Whether to include long-term memory context
            identified_emotion: Emotion identified by the mental health assistant

        Returns:
            Dictionary containing all relevant context for prompt generation
        """

        # Create query for relevant memories
        query = current_input
        if identified_emotion:
            query = f"{current_input} (emotion: {identified_emotion})"

        # Use centralized memory service to get context
        memory_context = await self.memory_service.get_memory_context(
            user_id, query if include_long_term else None
        )

        # Format context for prompt generation
        short_term_context = self._format_short_term_context(memory_context.short_term)
        long_term_context = (
            self._format_long_term_context(memory_context.long_term)
            if include_long_term
            else ""
        )

        # Get emotional anchors specifically
        emotional_anchors = ""
        if identified_emotion or include_long_term:
            emotional_anchor_memories = await self.memory_service.get_emotional_anchors(
                user_id
            )
            emotional_anchors = self._format_emotional_anchors(
                emotional_anchor_memories, identified_emotion
            )

        # Analyze current input for emotional/visual content
        input_analysis = self._analyze_input_content(current_input)

        return {
            "input_context": current_input,
            "short_term_context": short_term_context,
            "emotional_anchors": emotional_anchors,
            "long_term_context": long_term_context,
            "input_analysis": input_analysis,
            "has_sufficient_content": self._has_sufficient_visual_content(
                current_input, short_term_context, emotional_anchors
            ),
            "memory_digest": memory_context.digest,
        }

    def _format_short_term_context(self, short_term_memories: List) -> str:
        """Format short-term memories for prompt context."""
        if not short_term_memories:
            return "No recent conversation context available."

        context_parts = []
        for memory in short_term_memories[-5:]:  # Last 5 messages for context
            content = memory.content.strip()
            memory_type = memory.type

            if content and len(content) > 10:  # Filter out very short messages
                if memory_type == "user_message":
                    context_parts.append(f"User: {content}")
                elif memory_type == "assistant_message":
                    # Include assistant responses that contain emotional guidance
                    if any(
                        keyword in content.lower()
                        for keyword in [
                            "feel",
                            "emotion",
                            "color",
                            "imagine",
                            "picture",
                            "landscape",
                            "scene",
                            "metaphor",
                            "visual",
                        ]
                    ):
                        context_parts.append(f"Assistant: {content[:200]}...")

        return (
            "\n".join(context_parts)
            if context_parts
            else "Limited recent context available."
        )

    def _format_long_term_context(self, long_term_memories: List) -> str:
        """Format long-term memories for prompt context."""
        if not long_term_memories:
            return "No relevant long-term context."

        relevant_context = []
        for memory in long_term_memories[:3]:  # Top 3 relevant memories
            content = memory.content.strip()
            if len(content) > 30:
                relevant_context.append(content[:100])

        return (
            " | ".join(relevant_context)
            if relevant_context
            else "No relevant long-term context."
        )

    def _format_emotional_anchors(
        self, emotional_memories: List, identified_emotion: Optional[str] = None
    ) -> str:
        """Format emotional anchor memories for prompt context."""
        if not emotional_memories:
            return "No strong emotional anchors found."

        anchors = []
        for memory in emotional_memories[:3]:  # Top 3 emotional anchors
            content = memory.content.strip()
            connection_type = memory.metadata.get("connection_type", "")

            # Prefer anchors that match the identified emotion
            if identified_emotion and identified_emotion.lower() in content.lower():
                anchors.insert(0, f"{content[:150]} ({connection_type})")
            elif len(content) > 20:
                anchors.append(f"{content[:150]} ({connection_type})")

        if anchors:
            return "Key emotional themes: " + " | ".join(anchors[:3])
        else:
            return "No strong emotional anchors found."

    def _analyze_input_content(self, input_text: str) -> Dict[str, Any]:
        """Analyze input for emotional and visual content."""
        input_lower = input_text.lower()

        # Check for emotional keywords
        emotional_keywords = [
            "feel",
            "feeling",
            "emotion",
            "mood",
            "happy",
            "sad",
            "angry",
            "anxious",
            "excited",
            "nervous",
            "calm",
            "overwhelmed",
            "stuck",
            "confused",
            "hopeful",
            "worried",
            "peaceful",
            "frustrated",
        ]

        # Check for visual/sensory keywords
        visual_keywords = [
            "color",
            "see",
            "look",
            "image",
            "picture",
            "scene",
            "landscape",
            "bright",
            "dark",
            "light",
            "shadow",
            "warm",
            "cold",
            "rough",
            "smooth",
            "texture",
            "weather",
            "sky",
            "ocean",
            "mountain",
            "forest",
            "city",
            "room",
            "place",
            "remember",
            "reminds",
        ]

        # Check for metaphorical language
        metaphor_keywords = [
            "like",
            "as if",
            "reminds me",
            "feels like",
            "imagine",
            "picture",
            "seems like",
            "appears",
            "looks like",
        ]

        emotional_score = sum(1 for word in emotional_keywords if word in input_lower)
        visual_score = sum(1 for word in visual_keywords if word in input_lower)
        metaphor_score = sum(1 for phrase in metaphor_keywords if phrase in input_lower)

        return {
            "emotional_content": emotional_score > 0,
            "visual_content": visual_score > 0,
            "metaphorical_content": metaphor_score > 0,
            "word_count": len(input_text.split()),
            "richness_score": emotional_score + visual_score + metaphor_score,
        }

    def _has_sufficient_visual_content(
        self, current_input: str, short_term_context: str, emotional_anchors: str
    ) -> bool:
        """Determine if there's enough content to generate a meaningful image."""

        # Analyze current input
        input_analysis = self._analyze_input_content(current_input)

        # Check if input is too minimal (greetings, single words, etc.)
        minimal_inputs = [
            "hi",
            "hello",
            "hey",
            "yes",
            "no",
            "ok",
            "okay",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "sure",
            "maybe",
            "hmm",
        ]

        input_words = current_input.lower().strip().split()
        if len(input_words) <= 2 and any(
            word in minimal_inputs for word in input_words
        ):
            return False

        # Check for sufficient emotional or visual content
        has_emotional_content = input_analysis["emotional_content"]
        has_visual_content = input_analysis["visual_content"]
        has_context = (
            "error" not in short_term_context.lower() and len(short_term_context) > 50
        )
        has_anchors = (
            "error" not in emotional_anchors.lower()
            and "no strong" not in emotional_anchors.lower()
        )

        # Sufficient if we have emotional/visual content in input OR meaningful context
        return (
            has_emotional_content
            or has_visual_content
            or (has_context and input_analysis["word_count"] > 3)
            or (has_anchors and input_analysis["word_count"] > 2)
        )

    def format_prompt_template(self, context: Dict[str, Any]) -> str:
        """Format the context into the prompt template."""

        with open("services/memory/prompts/photo_generation.txt", "r") as f:
            template = f.read()

        return template.format(
            input_context=context["input_context"],
            short_term_context=context["short_term_context"],
            emotional_anchors=context["emotional_anchors"],
            long_term_context=context["long_term_context"],
        )
