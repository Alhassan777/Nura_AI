import os
import logging
import json
import google.generativeai as genai
from typing import Dict, Any

from ..types import MemoryItem, MemoryScore
from ..config import Config

# Set up logging
logger = logging.getLogger(__name__)


class GeminiScorer:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)

        # Load scoring prompt
        self.scoring_prompt = Config.get_memory_comprehensive_scoring_prompt()

        # Check if we're using fallbacks and warn
        self._check_configuration()

    def _check_configuration(self):
        """Check if environment variables are properly configured and warn if not."""
        if "CONFIGURATION ERROR" in self.scoring_prompt:
            error_msg = "⚠️  CONFIGURATION ERROR: Missing MEMORY_COMPREHENSIVE_SCORING_PROMPT. Using fallback scoring with limited functionality."
            logger.error(error_msg)
            print(f"\n{error_msg}\n")

    def score_memory(self, memory: MemoryItem) -> MemoryScore:
        """Score a memory using Gemini's significance-based analysis."""
        try:
            # Use comprehensive scoring with Gemini
            comprehensive_response = self.model.generate_content(
                self.scoring_prompt.format(content=memory.content)
            )

            # Clean and parse the response
            response_text = comprehensive_response.text.strip()

            # Handle cases where Gemini returns conversational responses instead of JSON
            if not response_text.startswith("{"):
                # Try to extract JSON from the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx]
                else:
                    # If no JSON found, retry with more explicit prompt
                    logger.warning(
                        "Gemini returned conversational response, retrying with explicit JSON prompt"
                    )
                    retry_prompt = f"""
{self.scoring_prompt.format(content=memory.content)}

CRITICAL: You must respond ONLY with valid JSON. Do not include any explanatory text, markdown, or conversational responses. Return exactly the JSON structure specified above.
"""
                    retry_response = self.model.generate_content(retry_prompt)
                    response_text = retry_response.text.strip()

                    # Extract JSON from retry response
                    start_idx = response_text.find("{")
                    end_idx = response_text.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        response_text = response_text[start_idx:end_idx]

            try:
                scoring_data = json.loads(response_text)

                # Extract significance-based data
                significance_category = scoring_data.get(
                    "significance_category", "routine_moment"
                )
                significance_level = scoring_data.get("significance_level", "minimal")
                storage_recommendation = scoring_data.get(
                    "storage_recommendation", "probably_skip"
                )
                key_elements = scoring_data.get("key_elements", [])
                therapeutic_value = scoring_data.get("therapeutic_value", {})
                reasoning = scoring_data.get("reasoning", "")

                # Map significance to numeric scores for compatibility
                significance_to_score = {
                    "critical": 0.95,
                    "high": 0.85,
                    "moderate": 0.65,
                    "low": 0.35,
                    "minimal": 0.15,
                }

                base_score = significance_to_score.get(significance_level, 0.5)

                # Adjust scores based on category
                if significance_category == "life_changing":
                    relevance_score = base_score
                    stability_score = min(
                        1.0, base_score + 0.2
                    )  # Life events are stable
                    explicitness_score = base_score
                elif significance_category == "emotional_insight":
                    relevance_score = min(
                        1.0, base_score + 0.15
                    )  # High therapeutic relevance
                    stability_score = base_score
                    explicitness_score = min(
                        1.0, base_score + 0.1
                    )  # Insights are often explicit
                elif significance_category == "therapeutic_foundation":
                    relevance_score = min(1.0, base_score + 0.2)  # Very relevant
                    stability_score = min(
                        1.0, base_score + 0.15
                    )  # Foundation info is stable
                    explicitness_score = base_score
                elif significance_category == "meaningful_connection":
                    relevance_score = base_score
                    stability_score = min(
                        1.0, base_score + 0.1
                    )  # Personal anchors are stable
                    explicitness_score = base_score
                else:  # routine_moment
                    relevance_score = base_score
                    stability_score = base_score
                    explicitness_score = base_score

                # Store significance metadata
                metadata = {
                    "significance_category": significance_category,
                    "significance_level": significance_level,
                    "storage_recommendation": storage_recommendation,
                    "key_elements": key_elements,
                    "therapeutic_value": therapeutic_value,
                    "reasoning": reasoning,
                    "gemini_used": True,
                    "api_calls_used": 1,
                }

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse scoring response: {str(e)}")
                logger.warning(f"Raw response: {repr(response_text[:500])}")

                # Fallback to basic scores
                relevance_score = 0.5
                stability_score = 0.5
                explicitness_score = 0.5
                metadata = {
                    "error": f"Parsing error: {str(e)}",
                    "storage_recommendation": "user_choice",
                    "gemini_used": True,
                    "api_calls_used": 1,
                }

            return MemoryScore(
                relevance=relevance_score,
                stability=stability_score,
                explicitness=explicitness_score,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Memory scoring failed: {str(e)}")
            # Return error scores that indicate configuration issues
            return MemoryScore(
                relevance=0.0,
                stability=0.0,
                explicitness=0.0,
                metadata={"error": str(e), "gemini_used": False},
            )

    def should_store_memory(
        self, score: MemoryScore, thresholds: Dict[str, float]
    ) -> bool:
        """Determine if a memory should be stored based on its significance."""
        metadata = score.metadata or {}

        # Use significance-based approach
        storage_recommendation = metadata.get("storage_recommendation", "probably_skip")
        significance_level = metadata.get("significance_level", "minimal")

        # Map storage recommendations to boolean decisions
        should_store = storage_recommendation in ["definitely_save", "probably_save"]

        logger.info(
            f"Storage decision: {should_store} "
            f"(level={significance_level}, recommendation={storage_recommendation})"
        )
        return should_store
