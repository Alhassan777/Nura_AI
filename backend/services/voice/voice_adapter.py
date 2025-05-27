"""
Voice Adapter for Mental Health Assistant (Section 3: Voice Processing Pipeline)
Wraps existing MentalHealthAssistant to add voice-specific prompt lines and optimizations.
Integrates with Vapi.ai control URL for response delivery.
"""

import logging
import aiohttp
import json
import os
from typing import Dict, Any, Optional

# Import from memory service
from ..memory.assistant.mental_health_assistant import MentalHealthAssistant
from ..memory.types import MemoryContext

logger = logging.getLogger(__name__)


class VoiceAdapter:
    """
    Enhanced adapter class that wraps MentalHealthAssistant for voice-specific responses.
    Section 3: Adds voice-optimized prompts, TTS optimization, and Vapi integration.
    """

    def __init__(self):
        self.mental_health_assistant = MentalHealthAssistant()
        self.vapi_api_key = os.getenv("VAPI_API_KEY")

        # Voice optimization settings
        self.max_voice_words = 50
        self.sentence_pause_marker = "... "
        self.emphasis_markers = {"important": "*", "gentle": "~", "pause": "..."}

    async def process_voice_message(
        self,
        user_message: str,
        user_id: str,
        memory_context: Optional[MemoryContext] = None,
        call_id: Optional[str] = None,
        control_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced voice message processing with Vapi integration.

        Args:
            user_message: The user's spoken message
            user_id: The user identifier
            memory_context: Memory context for personalization
            call_id: Optional call ID for tracking
            control_url: Vapi control URL for sending responses

        Returns:
            Assistant response optimized for voice with delivery status
        """

        # Enhance the message with voice-specific instructions
        voice_enhanced_message = self._add_voice_instructions(user_message)

        logger.info(f"🎙️  Processing voice message for user {user_id} (call: {call_id})")

        # Generate response using existing mental health assistant
        response = await self.mental_health_assistant.generate_response(
            user_message=voice_enhanced_message,
            memory_context=memory_context,
            user_id=user_id,
        )

        # Post-process response for voice optimization
        response = self._optimize_response_for_voice(response)

        # Add voice-specific metadata
        response["source"] = "voice_call"
        response["delivery_method"] = "tts"
        if call_id:
            response["call_id"] = call_id

        # Handle crisis situations with immediate voice response
        if response.get("crisis_level") in ["CRISIS", "HIGH"]:
            crisis_response = await self.handle_crisis_voice_response(
                response["crisis_level"], user_message, user_id
            )
            response["crisis_voice_response"] = crisis_response
            response["requires_immediate_delivery"] = True

        # Send response to Vapi if control URL provided
        if control_url:
            delivery_result = await self._send_to_vapi_control(
                control_url,
                response["response"],
                response.get("crisis_level", "SUPPORT"),
            )
            response["vapi_delivery"] = delivery_result

        logger.info(
            f"🤖 Voice response generated: {len(response['response'])} chars, crisis: {response.get('crisis_level', 'SUPPORT')}"
        )

        return response

    def _add_voice_instructions(self, user_message: str) -> str:
        """
        Enhanced voice-specific instructions with better prompting for TTS optimization.
        """

        voice_instructions = """
[VOICE THERAPY SESSION - RESPONSE OPTIMIZATION]

CONTEXT: You are responding to a user in a live voice therapy session. Your response will be converted to speech.

CRITICAL VOICE GUIDELINES:
1. BREVITY: Maximum 40-50 words per response
2. NATURAL SPEECH: Use conversational language, not written text
3. TTS OPTIMIZATION: 
   - Use simple punctuation (periods, commas, question marks)
   - Avoid complex formatting, parentheses, or lists
   - Include natural pauses with "..." for emphasis
4. EMOTIONAL WARMTH: Match the user's emotional tone appropriately
5. ENGAGEMENT: End with a gentle question or invitation to continue
6. CLARITY: One main idea per response

THERAPEUTIC FOCUS:
- Validate feelings immediately
- Offer one concrete coping strategy if appropriate
- Maintain hope and connection
- Be present-focused

USER'S VOICE MESSAGE: "{user_message}"

Respond as if you're sitting across from them in a gentle, supportive conversation. Keep it natural and brief.
""".strip()

        return voice_instructions.format(user_message=user_message)

    def _optimize_response_for_voice(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced post-processing for voice delivery with TTS optimization.
        """

        # Get the assistant's response text
        response_text = response.get("response", "")

        # Apply comprehensive voice optimizations
        optimized_text = self._apply_enhanced_voice_optimizations(response_text)

        # Update the response with optimization metadata
        response["response"] = optimized_text
        response["voice_optimized"] = True
        response["original_length"] = len(response_text)
        response["optimized_length"] = len(optimized_text)
        response["word_count"] = len(optimized_text.split())
        response["estimated_speech_time"] = self._estimate_speech_duration(
            optimized_text
        )

        return response

    def _apply_enhanced_voice_optimizations(self, text: str) -> str:
        """
        Enhanced optimizations for voice delivery with TTS considerations.
        """
        if not text:
            return "I'm here to listen and support you."

        # Remove configuration warnings from voice output
        if text.startswith("⚠️"):
            lines = text.split("\n")
            text = "\n".join(line for line in lines if not line.startswith("⚠️"))

        optimized = text.strip()

        # Convert complex punctuation to speech-friendly alternatives
        optimized = optimized.replace(" - ", " ")
        optimized = optimized.replace("; ", ", ")
        optimized = optimized.replace(": ", ", ")

        # Handle parenthetical statements
        optimized = self._handle_parentheticals(optimized)

        # Optimize for TTS pronunciation
        optimized = self._optimize_for_tts(optimized)

        # Ensure appropriate length for voice
        optimized = self._enforce_voice_length_limits(optimized)

        # Add natural speech markers
        optimized = self._add_speech_markers(optimized)

        return optimized.strip()

    def _handle_parentheticals(self, text: str) -> str:
        """Remove or convert parenthetical statements for voice."""
        # Simple parentheses removal for voice clarity
        import re

        text = re.sub(r"\([^)]*\)", "", text)
        return text.strip()

    def _optimize_for_tts(self, text: str) -> str:
        """Optimize text for Text-to-Speech pronunciation."""
        # Common TTS optimizations
        tts_replacements = {
            "&": "and",
            "%": "percent",
            "#": "number",
            "@": "at",
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "and so on",
            "vs.": "versus",
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
        }

        for symbol, word in tts_replacements.items():
            text = text.replace(symbol, word)

        return text

    def _enforce_voice_length_limits(self, text: str) -> str:
        """Enforce length limits appropriate for voice interaction."""
        words = text.split()

        if len(words) <= self.max_voice_words:
            return text

        # Truncate gracefully
        truncated = " ".join(words[: self.max_voice_words - 8])

        # Add natural continuation
        if "?" in text:
            return truncated + "... Can you tell me more about that?"
        else:
            return truncated + "... Would you like to explore this further?"

    def _add_speech_markers(self, text: str) -> str:
        """Add natural speech markers for better TTS delivery."""
        # Add gentle pauses after important statements
        if ". " in text:
            text = text.replace(". ", "... ")

        # Ensure natural ending
        if not text.endswith((".", "?", "!")):
            text += "."

        return text

    def _estimate_speech_duration(self, text: str) -> float:
        """Estimate speech duration in seconds (average 150 words per minute)."""
        word_count = len(text.split())
        return round((word_count / 150) * 60, 1)

    async def _send_to_vapi_control(
        self, control_url: str, response_text: str, crisis_level: str
    ) -> Dict[str, Any]:
        """
        Send assistant response to Vapi control URL for immediate delivery.
        """
        if not control_url:
            return {"status": "no_control_url", "delivered": False}

        try:
            # Prepare Vapi control payload
            payload = {
                "type": "conversation-update",
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "triggerResponseEnabled": True,  # Enable immediate TTS delivery
                "metadata": {
                    "source": "nura_assistant",
                    "crisis_level": crisis_level,
                    "optimized_for_voice": True,
                },
            }

            # Add crisis handling if needed
            if crisis_level in ["CRISIS", "HIGH"]:
                payload["priority"] = "high"
                payload["metadata"]["requires_immediate_attention"] = True

            headers = {
                "Content-Type": "application/json",
            }

            # Add API key if available
            if self.vapi_api_key:
                headers["Authorization"] = f"Bearer {self.vapi_api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    control_url, json=payload, headers=headers, timeout=5.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"✅ Response sent to Vapi control URL: {control_url}"
                        )
                        return {
                            "status": "success",
                            "delivered": True,
                            "response": result,
                            "delivery_time": "immediate",
                        }
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"❌ Failed to send to Vapi: {response.status} - {error_text}"
                        )
                        return {
                            "status": "failed",
                            "delivered": False,
                            "error": f"HTTP {response.status}: {error_text}",
                        }

        except aiohttp.ClientTimeout:
            logger.error("⏰ Timeout sending response to Vapi control URL")
            return {
                "status": "timeout",
                "delivered": False,
                "error": "Request timeout after 5 seconds",
            }
        except Exception as e:
            logger.error(f"💥 Error sending to Vapi control URL: {str(e)}")
            return {"status": "error", "delivered": False, "error": str(e)}

    async def handle_crisis_voice_response(
        self, crisis_level: str, user_message: str, user_id: str
    ) -> str:
        """
        Generate immediate, appropriate voice response for crisis situations.
        Enhanced for Section 5 (Crisis Escalation via Voice).
        """

        if crisis_level == "CRISIS":
            return (
                "I hear you, and I want you to know that you're not alone. "
                "I'm connecting you with emergency support right now. "
                "Please stay on the line with me."
            )
        elif crisis_level == "HIGH":
            return (
                "Thank you for trusting me with this. "
                "It sounds like you're going through something really difficult. "
                "Let me help you find some immediate support."
            )
        elif crisis_level == "MEDIUM":
            return (
                "I can hear that this is weighing heavily on you. "
                "You're being really brave by sharing this. "
                "Let's work through this together."
            )
        else:
            return (
                "I'm here to listen and support you. "
                "Tell me more about what's on your mind."
            )

    async def prepare_system_message(
        self, rag_content: str, user_context: Optional[MemoryContext] = None
    ) -> Dict[str, Any]:
        """
        Prepare system message for Vapi with RAG content and user context.
        Used when triggerResponseEnabled is True.
        """

        system_message = {
            "role": "system",
            "content": f"""
You are a compassionate mental health assistant in a voice therapy session.

CONTEXT: {rag_content}

VOICE RESPONSE GUIDELINES:
- Keep responses under 50 words
- Use natural, conversational language
- Add gentle pauses with "..." 
- Focus on validation and support
- End with engagement questions

Respond as if you're having a caring conversation.
""".strip(),
        }

        if user_context:
            # Add relevant context from memory
            context_summary = self._summarize_context_for_voice(user_context)
            system_message["content"] += f"\n\nUSER CONTEXT: {context_summary}"

        return {
            "message": system_message,
            "triggerResponseEnabled": True,
            "metadata": {
                "source": "nura_rag_system",
                "has_context": user_context is not None,
                "optimized_for_voice": True,
            },
        }

    def _summarize_context_for_voice(self, context: MemoryContext) -> str:
        """Summarize memory context for voice system message."""
        parts = []

        if context.short_term:
            recent = context.short_term[-2:]  # Last 2 interactions
            parts.append(f"Recent: {', '.join(m.content[:30] + '...' for m in recent)}")

        if context.digest:
            parts.append(f"Background: {context.digest[:100]}...")

        return " | ".join(parts) if parts else "New conversation"


# Global instance for easy access
voice_adapter = VoiceAdapter()
