import os
import logging
import json
import google.generativeai as genai
from typing import Dict, Any, List

from services.memory.types import MemoryItem, MemoryScore
from services.memory.config import Config

# Set up logging
logger = logging.getLogger(__name__)


class GeminiScorer:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Set up generation configurations for memory processing
        self._setup_generation_configs()

        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)

        # Load scoring prompt
        self.scoring_prompt = Config.get_memory_comprehensive_scoring_prompt()

        # Check if we're using fallbacks and warn
        self._check_configuration()

    def _setup_generation_configs(self):
        """Define generation configurations for consistent memory processing."""
        # Memory extraction - low temperature for consistent, instruction-following behavior
        self.memory_extraction_config = genai.types.GenerationConfig(
            temperature=0.2,  # Very low temperature for consistent extraction
            top_p=0.7,  # Focused sampling for structured output
            top_k=20,  # Limited token selection for consistency
            max_output_tokens=2048,  # Allow detailed component extraction
            candidate_count=1,
        )

        # Retry extraction - even lower temperature for strict JSON compliance
        self.strict_extraction_config = genai.types.GenerationConfig(
            temperature=0.1,  # Extremely low for strict instruction following
            top_p=0.6,
            top_k=10,
            max_output_tokens=2048,
            candidate_count=1,
        )

    def _check_configuration(self):
        """Check if environment variables are properly configured and warn if not."""
        if "CONFIGURATION ERROR" in self.scoring_prompt:
            error_msg = "⚠️  CONFIGURATION ERROR: Missing MEMORY_COMPREHENSIVE_SCORING_PROMPT. Using fallback scoring with limited functionality."
            logger.error(error_msg)
            print(f"\n{error_msg}\n")

    def score_memory(self, memory: MemoryItem) -> List[MemoryScore]:
        """Score a memory using Gemini's significance-based analysis, returning multiple components."""
        try:
            # Use comprehensive scoring with Gemini - LOW TEMPERATURE for consistency
            comprehensive_response = self.model.generate_content(
                self.scoring_prompt.format(content=memory.content),
                generation_config=self.memory_extraction_config,
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
                    # If no JSON found, retry with more explicit prompt and EVEN LOWER temperature
                    logger.warning(
                        "Gemini returned conversational response, retrying with strict extraction config"
                    )
                    retry_prompt = f"""
{self.scoring_prompt.format(content=memory.content)}

CRITICAL: You must respond ONLY with valid JSON. Do not include any explanatory text, markdown, or conversational responses. Return exactly the JSON structure specified above.
"""
                    retry_response = self.model.generate_content(
                        retry_prompt, generation_config=self.strict_extraction_config
                    )
                    response_text = retry_response.text.strip()

                    # Extract JSON from retry response
                    start_idx = response_text.find("{")
                    end_idx = response_text.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        response_text = response_text[start_idx:end_idx]

            try:
                scoring_data = json.loads(response_text)
                components = scoring_data.get("components", [])

                # If no components found, treat as single component (backward compatibility)
                if not components:
                    components = [scoring_data]

                memory_scores = []

                for i, component_data in enumerate(components):
                    # Extract component data
                    component_content = component_data.get("content", memory.content)
                    memory_type = component_data.get("memory_type", "temporary_state")
                    significance_category = component_data.get(
                        "significance_category", "routine_moment"
                    )
                    significance_level = component_data.get(
                        "significance_level", "minimal"
                    )
                    storage_recommendation = component_data.get(
                        "storage_recommendation", "probably_skip"
                    )
                    reasoning = component_data.get("reasoning", "")

                    # Extract meaningful connection fields if present
                    connection_type = component_data.get("connection_type")
                    emotional_significance = component_data.get(
                        "emotional_significance"
                    )
                    personal_meaning = component_data.get("personal_meaning")
                    anchor_strength = component_data.get("anchor_strength")
                    display_category = component_data.get("display_category")

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
                        stability_score = min(1.0, base_score + 0.2)
                        explicitness_score = base_score
                    elif significance_category == "emotional_insight":
                        relevance_score = min(1.0, base_score + 0.15)
                        stability_score = base_score
                        explicitness_score = min(1.0, base_score + 0.1)
                    elif significance_category == "therapeutic_foundation":
                        relevance_score = min(1.0, base_score + 0.2)
                        stability_score = min(1.0, base_score + 0.15)
                        explicitness_score = base_score
                    elif significance_category == "meaningful_connection":
                        relevance_score = base_score
                        stability_score = min(1.0, base_score + 0.1)
                        explicitness_score = base_score
                    else:  # routine_moment
                        relevance_score = base_score
                        stability_score = base_score
                        explicitness_score = base_score

                    # Store component metadata
                    metadata = {
                        "component_content": component_content,
                        "component_index": i,
                        "total_components": len(components),
                        "original_message": memory.content,
                        "memory_type": memory_type,
                        "significance_category": significance_category,
                        "significance_level": significance_level,
                        "storage_recommendation": storage_recommendation,
                        "reasoning": reasoning,
                        "gemini_used": True,
                        "api_calls_used": 1,
                    }

                    # Add meaningful connection fields if they exist
                    if connection_type:
                        metadata["connection_type"] = connection_type
                    if emotional_significance:
                        metadata["emotional_significance"] = emotional_significance
                    if personal_meaning:
                        metadata["personal_meaning"] = personal_meaning
                    if anchor_strength:
                        metadata["anchor_strength"] = anchor_strength
                    if display_category:
                        metadata["display_category"] = display_category

                    memory_scores.append(
                        MemoryScore(
                            relevance=relevance_score,
                            stability=stability_score,
                            explicitness=explicitness_score,
                            metadata=metadata,
                        )
                    )

                return memory_scores

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse scoring response: {str(e)}")
                logger.warning(f"Raw response: {repr(response_text[:500])}")

                # Fallback to single component with basic scores
                return [
                    MemoryScore(
                        relevance=0.5,
                        stability=0.5,
                        explicitness=0.5,
                        metadata={
                            "error": f"Parsing error: {str(e)}",
                            "storage_recommendation": "user_choice",
                            "gemini_used": True,
                            "api_calls_used": 1,
                            "component_content": memory.content,
                            "original_message": memory.content,
                        },
                    )
                ]

        except Exception as e:
            logger.error(f"Memory scoring failed: {str(e)}")
            # Return error scores that indicate configuration issues
            return [
                MemoryScore(
                    relevance=0.0,
                    stability=0.0,
                    explicitness=0.0,
                    metadata={
                        "error": str(e),
                        "gemini_used": False,
                        "component_content": memory.content,
                        "original_message": memory.content,
                    },
                )
            ]

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
