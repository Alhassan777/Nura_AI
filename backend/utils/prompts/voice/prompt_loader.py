"""
Voice Assistant Prompt Loader.

Utilities for loading voice-specific prompts and shared prompts
used by the voice assistant (Vapi).
"""

import os
from typing import Optional


class VoicePromptLoader:
    """Loads prompts for voice assistant."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.voice_prompts_dir = self.base_dir
        self.chat_prompts_dir = os.path.join(self.base_dir, "..", "chat")

    def _load_prompt(self, filename: str, directory: str) -> str:
        """Load a prompt file from the specified directory."""
        try:
            prompt_path = os.path.join(directory, filename)
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {filename}")

    def get_safety_network_enhancement_prompt(self) -> str:
        """Get the safety network crisis intervention enhancement prompt for voice assistant."""
        return self._load_prompt(
            "safety_network_enhancement.txt", self.voice_prompts_dir
        )

    # Shared prompts (now in chat directory)
    def get_conversation_guidelines(self) -> str:
        """Get the conversation guidelines used by both chat and voice."""
        return self._load_prompt("conversation_guidelines.txt", self.chat_prompts_dir)

    def get_crisis_detection_prompt(self) -> str:
        """Get the crisis detection prompt used by both chat and voice."""
        return self._load_prompt("crisis_detection.txt", self.chat_prompts_dir)


# Convenience functions for backward compatibility
def get_safety_network_enhancement_prompt() -> str:
    """Get the safety network crisis intervention enhancement prompt for voice assistant."""
    loader = VoicePromptLoader()
    return loader.get_safety_network_enhancement_prompt()


def get_conversation_guidelines() -> str:
    """Get the conversation guidelines used by both chat and voice."""
    loader = VoicePromptLoader()
    return loader.get_conversation_guidelines()


def get_crisis_detection_prompt() -> str:
    """Get the crisis detection prompt used by both chat and voice."""
    loader = VoicePromptLoader()
    return loader.get_crisis_detection_prompt()
