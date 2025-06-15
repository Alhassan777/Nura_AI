"""
Multi-Modal Mental Health Chat System
Integrates with existing Nura services for ultra-fast responses with background processing.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai

# Import existing services
from ..assistant.extractors import (
    ScheduleExtractor,
    ScheduleOpportunityAnalyzer,
    ActionPlanExtractor,
    ActionPlanOpportunityAnalyzer,
)
from ..memory.memoryService import MemoryService
from ..memory.types import MemoryContext
from ..privacy.security.pii_detector import PIIDetector
from ..image_generation.emotion_visualizer import EmotionVisualizer
from ..scheduling.scheduler import ScheduleManager
from utils.scoring.gemini_scorer import GeminiScorer
from .cache_manager import CacheManager

# Import new prompt loading system
from utils.prompts.chat.prompt_loader import ChatPromptLoader

# Import modular components
from .components import (
    InformationGatherer,
    ModeDetector,
    ResponseGenerator,
    BackgroundProcessor,
)

logger = logging.getLogger(__name__)


class MultiModalChatService:
    """
    Multi-modal chat service that integrates with all existing Nura services
    for ultra-fast responses with comprehensive background processing.
    """

    def __init__(self):
        # Initialize cache manager
        self.cache_manager = CacheManager()

        # Initialize Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self._setup_generation_configs()
        self.model = genai.GenerativeModel(
            "models/gemini-2.0-flash", generation_config=self.conversational_config
        )

        # Initialize prompt loader and load prompts
        self.prompt_loader = ChatPromptLoader()
        self._load_mode_prompts()

        # Initialize existing services
        self._initialize_services()

        # Initialize modular components
        self._initialize_components()

    def _setup_generation_configs(self):
        """Setup generation configurations for different purposes."""
        # Fast conversational responses - Optimized for natural, concise mental health conversations
        self.conversational_config = genai.types.GenerationConfig(
            temperature=0.6,  # Reduced from 0.8 - more focused, less verbose
            top_p=0.85,  # Slightly reduced for better coherence
            top_k=25,  # Reduced from 40 - more focused vocabulary
            max_output_tokens=1024,  # Reduced from 2048 - encourages conciseness
            candidate_count=1,
        )

        # Crisis assessment - Keep conservative for safety
        self.crisis_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=20,
            max_output_tokens=512,
            candidate_count=1,
        )

    def _load_mode_prompts(self):
        """Load mode-specific system prompts and guidelines using the prompt loader."""
        try:
            # Load system prompts for each mode
            self.mode_prompts = {
                "general": self.prompt_loader.get_system_prompt("general"),
                "action_plan": self.prompt_loader.get_system_prompt("action_plan"),
                "visualization": self.prompt_loader.get_system_prompt("visualization"),
            }

            # Load conversation guidelines for each mode
            self.mode_guidelines = {
                "general": self.prompt_loader.get_conversation_guidelines("general"),
                "action_plan": self.prompt_loader.get_conversation_guidelines(
                    "action_plan"
                ),
                "visualization": self.prompt_loader.get_conversation_guidelines(
                    "visualization"
                ),
            }

            # Load crisis detection prompt
            self.crisis_detection_prompt = (
                self.prompt_loader.get_crisis_detection_prompt()
            )

            logger.info("Successfully loaded all mode-specific prompts")

        except Exception as e:
            logger.error(f"CRITICAL: Failed to load essential prompts: {e}")
            raise RuntimeError(
                f"Multi-modal chat service cannot start without prompts. "
                f"Check that prompt files exist in backend/utils/prompts/chat/. Error: {e}"
            )

    def _initialize_services(self):
        """Initialize all existing Nura services."""
        # Memory service
        self.memory_service = MemoryService()

        # PII detection
        self.pii_detector = PIIDetector()

        # Memory scoring
        self.memory_scorer = GeminiScorer()

        # Action plan extraction
        self.action_plan_extractor = ActionPlanExtractor(
            self.model, self.conversational_config
        )
        self.action_plan_analyzer = ActionPlanOpportunityAnalyzer()

        # Schedule extraction
        self.schedule_extractor = ScheduleExtractor(
            self.model, self.conversational_config
        )
        self.schedule_analyzer = ScheduleOpportunityAnalyzer()

        # Image generation - Create proper LLM client wrapper
        class LLMClientWrapper:
            def __init__(self, model, config):
                self.model = model
                self.metadata_config = config

        llm_client = LLMClientWrapper(self.model, self.conversational_config)
        self.emotion_visualizer = EmotionVisualizer(llm_client=llm_client)

        # Scheduling manager
        self.schedule_manager = ScheduleManager()

    def _initialize_components(self):
        """Initialize modular components."""
        # Information gathering component
        self.information_gatherer = InformationGatherer()

        # Mode detection component
        self.mode_detector = ModeDetector()

        # Response generation component
        self.response_generator = ResponseGenerator(
            self.model, self.conversational_config
        )

        # Background processing component
        self.background_processor = BackgroundProcessor(
            model=self.model,
            crisis_config=self.crisis_config,
            cache_manager=self.cache_manager,
            memory_service=self.memory_service,
            emotion_visualizer=self.emotion_visualizer,
            action_plan_extractor=self.action_plan_extractor,
            action_plan_analyzer=self.action_plan_analyzer,
            schedule_extractor=self.schedule_extractor,
            schedule_analyzer=self.schedule_analyzer,
            crisis_detection_prompt=self.crisis_detection_prompt,
        )

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        mode: str = "general",
    ) -> Dict[str, Any]:
        """
        Process a message with ultra-fast response and background processing.

        Args:
            user_id: User identifier
            message: User's message
            conversation_id: Optional conversation ID
            mode: Chat mode (general, action_plan, visualization)

        Returns:
            Immediate response with background task ID
        """
        try:
            # Start timing for cache performance
            start_time = datetime.utcnow()

            # Auto-detect mode if not specified
            if mode == "general":
                mode = await self.mode_detector.detect_mode(message)

            # Get cached context super fast
            context = await self._get_fast_context(user_id, message, conversation_id)

            # Generate immediate response using component
            response_data = await self.response_generator.generate_fast_response(
                user_id, message, context, mode, self.mode_prompts, self.mode_guidelines
            )

            # Start background processing (don't await)
            background_task_id = f"bg_{user_id}_{datetime.utcnow().timestamp()}"
            asyncio.create_task(
                self.background_processor.process_background_tasks(
                    user_id, message, conversation_id, mode, background_task_id, context
                )
            )

            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "response": response_data["response"],
                "mode": mode,
                "conversation_id": conversation_id,
                "background_task_id": background_task_id,
                "response_time_ms": response_time,
                "cache_performance": {
                    "context_cached": context.get("from_cache", False),
                    "crisis_cached": False,  # Will be updated in background
                },
                "immediate_flags": {
                    "crisis_detected": response_data.get("immediate_crisis", False),
                    "needs_resources": response_data.get("needs_resources", False),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {
                "response": "I'm here to support you, but I'm having technical difficulties. If you're in crisis, please reach out to emergency services immediately.",
                "mode": mode,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _get_fast_context(
        self, user_id: str, message: str, conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get context using cache-first strategy for ultra-fast response."""
        try:
            # Try to get enriched context from cache first
            context_hash = await self.cache_manager.generate_context_hash(
                user_id, message
            )
            cached_context = await self.cache_manager.get_enriched_context(
                user_id, context_hash
            )

            if cached_context:
                return {
                    "context": cached_context,
                    "from_cache": True,
                    "type": "enriched",
                }

            # Try conversation messages cache
            if conversation_id:
                cached_messages = await self.cache_manager.get_conversation_messages(
                    conversation_id
                )
                if cached_messages:
                    # Build minimal context from cached messages
                    context_str = self.response_generator.build_minimal_context(
                        cached_messages[-5:]
                    )  # Last 5 messages
                    return {
                        "context": context_str,
                        "from_cache": True,
                        "type": "conversation",
                    }

            # Fallback: get minimal context directly (no heavy memory operations)
            return {
                "context": "This appears to be a new or uncached conversation.",
                "from_cache": False,
                "type": "minimal",
            }

        except Exception as e:
            logger.error(f"Error getting fast context: {e}")
            return {
                "context": "Context temporarily unavailable.",
                "from_cache": False,
                "type": "error",
            }

    async def get_background_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get background processing results by task ID."""
        try:
            return await self.cache_manager.get_background_results(task_id)
        except Exception as e:
            logger.error(f"Error getting background results for task {task_id}: {e}")
            return None

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

    async def get_available_modes(self) -> Dict[str, Any]:
        """Get information about available chat modes."""
        return self.mode_detector.get_mode_info()

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all integrated services."""
        try:
            checks = {}

            # Cache manager health
            checks["cache"] = await self.cache_manager.health_check()

            # Memory service health
            try:
                await self.memory_service.get_memory_stats("health_check")
                checks["memory"] = {"status": "healthy"}
            except Exception as e:
                checks["memory"] = {"status": "unhealthy", "error": str(e)}

            # Image generation health
            try:
                status = await self.emotion_visualizer.get_generation_status(
                    "health_check"
                )
                checks["image_generation"] = {"status": "healthy", "details": status}
            except Exception as e:
                checks["image_generation"] = {"status": "unhealthy", "error": str(e)}

            # Overall health
            healthy_services = sum(
                1 for check in checks.values() if check.get("status") == "healthy"
            )
            total_services = len(checks)

            return {
                "status": (
                    "healthy" if healthy_services == total_services else "degraded"
                ),
                "services": checks,
                "healthy_services": healthy_services,
                "total_services": total_services,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
