"""
Chat Assistant Prompt Loader.

Utilities for loading chat-specific prompts and shared prompts
used by the chat assistant.
"""

import os
from typing import Optional


class ChatPromptLoader:
    """Loads prompts for chat assistant."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.chat_prompts_dir = self.base_dir

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt file from the chat directory."""
        try:
            prompt_path = os.path.join(self.chat_prompts_dir, filename)
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {filename}")

    def get_system_prompt(self, mode: str = "general") -> str:
        """Get the system prompt for specific chat mode."""
        mode_files = {
            "general": "system_prompt_general.txt",
            "action_plan": "system_prompt_action_plan.txt",
            "visualization": "system_prompt_visualization.txt",
        }

        filename = mode_files.get(mode, "system_prompt_general.txt")
        try:
            return self._load_prompt(filename)
        except FileNotFoundError:
            # Fallback to general system prompt if mode-specific not found
            return self._load_prompt("system_prompt_general.txt")

    def get_conversation_guidelines(self, mode: str = "general") -> str:
        """Get conversation guidelines for specific chat mode."""
        mode_files = {
            "general": "conversation_guidelines_general.txt",
            "action_plan": "conversation_guidelines_action_plan.txt",
            "visualization": "conversation_guidelines_visualization.txt",
        }

        filename = mode_files.get(mode, "conversation_guidelines_general.txt")
        try:
            return self._load_prompt(filename)
        except FileNotFoundError:
            # Fallback to general guidelines if mode-specific not found
            return self._load_prompt("conversation_guidelines_general.txt")

    def get_memory_scoring_prompt(self) -> str:
        """Get the memory scoring prompt for conversation analysis."""
        return self._load_prompt("memory_scoring.txt")

    def get_photo_generation_prompt(self) -> str:
        """Get the photo generation prompt for visual creation."""
        return self._load_prompt("photo_generation.txt")

    def get_schedule_extraction_prompt(self) -> str:
        """Get the schedule extraction prompt for detecting scheduling opportunities."""
        return self._load_prompt("schedule_extraction.txt")

    def get_action_plan_generation_prompt(self) -> str:
        """Get the action plan generation prompt for creating structured action plans."""
        return self._load_prompt("action_plan_generation.txt")

    def get_crisis_detection_prompt(self) -> str:
        """Get the crisis detection prompt used by both chat and voice."""
        return self._load_prompt("crisis_detection.txt")


# Convenience functions for backward compatibility
def get_system_prompt(mode: str = "general") -> str:
    """Get the system prompt for specific chat mode."""
    loader = ChatPromptLoader()
    return loader.get_system_prompt(mode)


def get_conversation_guidelines(mode: str = "general") -> str:
    """Get conversation guidelines for specific chat mode."""
    loader = ChatPromptLoader()
    return loader.get_conversation_guidelines(mode)


def get_memory_scoring_prompt() -> str:
    """Get the memory scoring prompt for conversation analysis."""
    loader = ChatPromptLoader()
    return loader.get_memory_scoring_prompt()


def get_photo_generation_prompt() -> str:
    """Get the photo generation prompt for visual creation."""
    loader = ChatPromptLoader()
    return loader.get_photo_generation_prompt()


def get_schedule_extraction_prompt() -> str:
    """Get the schedule extraction prompt for detecting scheduling opportunities."""
    loader = ChatPromptLoader()
    return loader.get_schedule_extraction_prompt()


def get_action_plan_generation_prompt() -> str:
    """Get the action plan generation prompt for creating structured action plans."""
    loader = ChatPromptLoader()
    return loader.get_action_plan_generation_prompt()


def get_crisis_detection_prompt() -> str:
    """Get the crisis detection prompt used by both chat and voice."""
    loader = ChatPromptLoader()
    return loader.get_crisis_detection_prompt()
