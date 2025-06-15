"""
Background Processor Component
Handles comprehensive background processing tasks.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

from ..cache_manager import CacheManager
from ...memory.memoryService import MemoryService
from ...memory.types import MemoryContext
from ...image_generation.emotion_visualizer import EmotionVisualizer
from services.assistant.extractors import (
    ActionPlanExtractor,
    ActionPlanOpportunityAnalyzer,
    ScheduleExtractor,
    ScheduleOpportunityAnalyzer,
)
from ...scheduling.scheduler import ScheduleManager
from ...action_plans.service import ActionPlanService
from .information_gatherer import InformationGatherer
from .mode_detector import ModeDetector
from utils.database import get_db

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Handles comprehensive background processing tasks."""

    def __init__(
        self,
        model: genai.GenerativeModel,
        crisis_config,
        cache_manager: CacheManager,
        memory_service: MemoryService,
        emotion_visualizer: EmotionVisualizer,
        action_plan_extractor: ActionPlanExtractor,
        action_plan_analyzer: ActionPlanOpportunityAnalyzer,
        schedule_extractor: ScheduleExtractor,
        schedule_analyzer: ScheduleOpportunityAnalyzer,
        crisis_detection_prompt: str,
    ):
        self.model = model
        self.crisis_config = crisis_config
        self.cache_manager = cache_manager
        self.memory_service = memory_service
        self.emotion_visualizer = emotion_visualizer
        self.action_plan_extractor = action_plan_extractor
        self.action_plan_analyzer = action_plan_analyzer
        self.schedule_extractor = schedule_extractor
        self.schedule_analyzer = schedule_analyzer
        self.crisis_detection_prompt = crisis_detection_prompt

        # Initialize components
        self.information_gatherer = InformationGatherer()
        self.mode_detector = ModeDetector()
        self.action_plan_service = ActionPlanService()

    async def process_background_tasks(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str],
        mode: str,
        task_id: str,
        context: Dict[str, Any],
    ):
        """Process comprehensive background tasks after sending immediate response."""
        try:
            background_results = {
                "task_id": task_id,
                "user_id": user_id,
                "mode": mode,
                "started_at": datetime.utcnow().isoformat(),
                "status": "processing",
                "tasks": {},
            }

            # Task 1: Memory processing and storage
            memory_task = asyncio.create_task(
                self._process_memory_background(user_id, message, conversation_id)
            )

            # Task 2: Full crisis assessment
            crisis_task = asyncio.create_task(self._process_crisis_background(message))

            # Task 3: Mode-specific processing
            mode_task = asyncio.create_task(
                self._process_mode_specific_background(user_id, message, mode, context)
            )

            # Task 4: Mode suggestion (for all modes)
            suggestion_task = asyncio.create_task(
                self.mode_detector.suggest_mode_switch(mode, message, context)
            )

            # Task 5: Context enrichment for future responses
            context_task = asyncio.create_task(
                self._enrich_context_background(user_id, message, conversation_id)
            )

            # Wait for all background tasks
            (
                memory_result,
                crisis_result,
                mode_result,
                suggestion_result,
                context_result,
            ) = await asyncio.gather(
                memory_task,
                crisis_task,
                mode_task,
                suggestion_task,
                context_task,
                return_exceptions=True,
            )

            # Handle crisis intervention if needed
            intervention_result = None
            if (
                not isinstance(crisis_result, Exception)
                and crisis_result.get("crisis_flag", False)
                and crisis_result.get("level") == "CRISIS"
            ):
                try:
                    logger.warning(
                        f"Crisis detected for user {user_id}, initiating intervention"
                    )
                    intervention_result = await self._handle_crisis_intervention(
                        user_id=user_id,
                        crisis_data=crisis_result,
                        user_message=message,
                        conversation_id=conversation_id,
                    )
                    logger.info(
                        f"Crisis intervention completed: {intervention_result.get('intervention_attempted', False)}"
                    )
                except Exception as e:
                    logger.error(f"Crisis intervention failed: {e}")
                    intervention_result = {
                        "error": str(e),
                        "intervention_attempted": False,
                    }

            # Store results
            background_results["tasks"] = {
                "memory_processing": (
                    memory_result
                    if not isinstance(memory_result, Exception)
                    else {"error": str(memory_result)}
                ),
                "crisis_assessment": (
                    crisis_result
                    if not isinstance(crisis_result, Exception)
                    else {"error": str(crisis_result)}
                ),
                "crisis_intervention": intervention_result,
                "mode_specific": (
                    mode_result
                    if not isinstance(mode_result, Exception)
                    else {"error": str(mode_result)}
                ),
                "mode_suggestion": (
                    suggestion_result
                    if not isinstance(suggestion_result, Exception)
                    else {"error": str(suggestion_result)}
                ),
                "context_enrichment": (
                    context_result
                    if not isinstance(context_result, Exception)
                    else {"error": str(context_result)}
                ),
            }
            background_results["completed_at"] = datetime.utcnow().isoformat()
            background_results["status"] = "completed"

            # Cache the background results
            await self.cache_manager.cache_background_results(
                task_id, background_results
            )

            logger.info(f"Completed background processing for task {task_id}")

        except Exception as e:
            logger.error(f"Error in background processing for task {task_id}: {e}")
            # Cache error result
            error_result = {
                "task_id": task_id,
                "user_id": user_id,
                "error": str(e),
                "status": "error",
                "completed_at": datetime.utcnow().isoformat(),
            }
            await self.cache_manager.cache_background_results(task_id, error_result)

    async def _process_memory_background(
        self, user_id: str, message: str, conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process memory storage in background using existing memory service."""
        try:
            metadata = {"source": "chat_interface"}
            if conversation_id:
                metadata["conversation_id"] = conversation_id

            # Use existing memory service
            result = await self.memory_service.process_memory(
                user_id=user_id, content=message, type="user_message", metadata=metadata
            )

            return {
                "stored": result.get("stored", False),
                "memory_id": result.get("memory_id"),
                "needs_consent": result.get("needs_consent", False),
                "processing_time": "background",
            }

        except Exception as e:
            logger.error(f"Error in memory background processing: {e}")
            return {"error": str(e), "stored": False}

    async def _process_crisis_background(self, message: str) -> Dict[str, Any]:
        """Full crisis assessment in background."""
        try:
            # Use the loaded crisis detection prompt
            crisis_prompt = self.crisis_detection_prompt.format(content=message)

            assessment_response = self.model.generate_content(
                crisis_prompt, generation_config=self.crisis_config
            )

            assessment_text = assessment_response.text.strip()

            # Parse structured response
            crisis_level = "SUPPORT"
            crisis_flag = False
            explanation = assessment_text

            if "LEVEL:" in assessment_text:
                level_line = [
                    line
                    for line in assessment_text.split("\n")
                    if line.startswith("LEVEL:")
                ]
                if level_line:
                    level_value = level_line[0].replace("LEVEL:", "").strip()
                    if level_value in ["CRISIS", "CONCERN", "SUPPORT"]:
                        crisis_level = level_value

            if "FLAG:" in assessment_text:
                flag_line = [
                    line
                    for line in assessment_text.split("\n")
                    if line.startswith("FLAG:")
                ]
                if flag_line:
                    flag_value = flag_line[0].replace("FLAG:", "").strip().upper()
                    crisis_flag = flag_value == "TRUE"

            return {
                "level": crisis_level,
                "crisis_flag": crisis_flag,
                "explanation": explanation,
                "assessment_type": "background_comprehensive",
            }

        except Exception as e:
            logger.error(f"Error in crisis background processing: {e}")
            return {"error": str(e), "level": "SUPPORT", "crisis_flag": False}

    async def _handle_crisis_intervention(
        self,
        user_id: str,
        crisis_data: Dict[str, Any],
        user_message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle crisis intervention using the existing CrisisInterventionManager."""
        try:
            # Import here to avoid circular imports
            from ....assistant.crisis_intervention import CrisisInterventionManager

            # Prepare conversation context
            conversation_context = {}
            if conversation_id:
                conversation_context["conversation_id"] = conversation_id
                conversation_context["source"] = "multi_modal_chat"

            # Use the existing crisis intervention manager
            intervention_result = (
                await CrisisInterventionManager.handle_crisis_intervention(
                    user_id=user_id,
                    crisis_data=crisis_data,
                    user_message=user_message,
                    conversation_context=conversation_context,
                )
            )

            logger.info(
                f"Crisis intervention completed for user {user_id}: {intervention_result.get('intervention_attempted', False)}"
            )
            return intervention_result

        except Exception as e:
            logger.error(f"Crisis intervention failed for user {user_id}: {e}")
            return {
                "intervention_attempted": False,
                "error": str(e),
                "message": "Crisis intervention system temporarily unavailable. Please call 988 or 911 immediately if you're in danger.",
                "immediate_resources": [
                    {"name": "National Suicide Prevention Lifeline", "contact": "988"},
                    {"name": "Emergency Services", "contact": "911"},
                ],
            }

    async def _process_mode_specific_background(
        self, user_id: str, message: str, mode: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process mode-specific tasks in background."""
        try:
            if mode == "action_plan":
                return await self._process_action_plan_background(
                    user_id, message, context
                )
            elif mode == "visualization":
                return await self._process_visualization_background(
                    user_id, message, context
                )
            else:
                return await self._process_general_background(user_id, message, context)

        except Exception as e:
            logger.error(f"Error in mode-specific background processing: {e}")
            return {"error": str(e), "mode": mode}

    async def _process_action_plan_background(
        self, user_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process action plan generation with information gathering and database creation."""
        try:
            # Check if we have enough information to create an action plan
            readiness = await self.information_gatherer.assess_action_plan_readiness(
                user_id, message, context
            )

            if not readiness["ready"]:
                # Generate follow-up questions to gather more information
                follow_up_questions = (
                    await self.information_gatherer.generate_action_plan_questions(
                        message, readiness["missing_info"]
                    )
                )
                return {
                    "type": "action_plan",
                    "status": "gathering_info",
                    "readiness": readiness,
                    "follow_up_questions": follow_up_questions,
                    "should_suggest_action_plan": False,
                    "info_gathering_message": self.information_gatherer.generate_gathering_message(
                        "action_plan", readiness["missing_info"]
                    ),
                }

            # We have enough info - use existing action plan extractor
            opportunity = self.action_plan_analyzer.analyze_opportunity(
                message, "", context.get("context", "")
            )

            if opportunity.get("should_suggest", False):
                # Extract action plan using existing extractor
                action_plan_info = await self.action_plan_extractor.extract_information(
                    message, "", context.get("context", ""), opportunity
                )

                if action_plan_info.get("should_suggest_action_plan", False):
                    # Create the action plan in the database
                    try:
                        db = next(get_db())
                        conversation_context = context.get("context", "")

                        # Use the action plan service to generate and save the plan
                        result = await self.action_plan_service.generate_action_plan_from_conversation(
                            user_id=user_id,
                            conversation_context=conversation_context,
                            user_message=message,
                            db=db,
                        )

                        if result and result.get("should_suggest"):
                            created_plan = result["action_plan"]

                            return {
                                "should_suggest_action_plan": True,
                                "action_plan_created": True,
                                "action_plan_id": created_plan.id,
                                "action_plan": {
                                    "id": created_plan.id,
                                    "title": created_plan.title,
                                    "description": created_plan.description,
                                    "plan_type": created_plan.plan_type,
                                    "steps_count": len(created_plan.steps),
                                    "generated_by_ai": created_plan.generated_by_ai,
                                },
                                "gentle_prompt": action_plan_info.get("gentle_prompt"),
                                "opportunity_analysis": opportunity,
                                "status": "completed",
                                "readiness": readiness,
                            }
                        else:
                            # AI extraction succeeded but service couldn't create plan
                            return {
                                "should_suggest_action_plan": True,
                                "action_plan_created": False,
                                "action_plan": action_plan_info.get(
                                    "extracted_action_plan", {}
                                ),
                                "gentle_prompt": action_plan_info.get("gentle_prompt"),
                                "opportunity_analysis": opportunity,
                                "status": "extraction_only",
                                "readiness": readiness,
                                "note": "Action plan extracted but not saved to database",
                            }

                    except Exception as db_error:
                        logger.error(
                            f"Error creating action plan in database: {db_error}"
                        )
                        # Fallback to extraction-only result
                        return {
                            "should_suggest_action_plan": True,
                            "action_plan_created": False,
                            "action_plan": action_plan_info.get(
                                "extracted_action_plan", {}
                            ),
                            "gentle_prompt": action_plan_info.get("gentle_prompt"),
                            "opportunity_analysis": opportunity,
                            "status": "db_error",
                            "readiness": readiness,
                            "error": str(db_error),
                        }
                    finally:
                        if "db" in locals():
                            db.close()
                else:
                    return {
                        "should_suggest_action_plan": False,
                        "reason": "Action plan extraction did not recommend creation",
                        "status": "not_recommended",
                    }
            else:
                return {
                    "should_suggest_action_plan": False,
                    "reason": "No action plan opportunity detected",
                    "status": "no_plan_needed",
                }

        except Exception as e:
            logger.error(f"Error in action plan background processing: {e}")
            return {
                "error": str(e),
                "should_suggest_action_plan": False,
                "status": "error",
            }

    async def _process_visualization_background(
        self, user_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process visualization generation with emotional information gathering."""
        try:
            # Check if we have enough emotional information for meaningful visualization
            readiness = await self.information_gatherer.assess_visualization_readiness(
                user_id, message, context
            )

            if not readiness["ready"]:
                # Generate follow-up questions to gather more emotional information
                follow_up_questions = (
                    await self.information_gatherer.generate_visualization_questions(
                        message, readiness["missing_info"]
                    )
                )
                return {
                    "type": "visualization",
                    "status": "gathering_info",
                    "readiness": readiness,
                    "follow_up_questions": follow_up_questions,
                    "visualization_suitable": False,
                    "info_gathering_message": self.information_gatherer.generate_gathering_message(
                        "visualization", readiness["missing_info"]
                    ),
                }

            # We have enough emotional info - use existing emotion visualizer
            result = (
                await self.emotion_visualizer.validate_user_input_for_visualization(
                    user_id, message
                )
            )

            if result.get("suitable", False):
                # Generate image prompt in background
                image_result = await self.emotion_visualizer.create_emotional_image(
                    user_id=user_id,
                    user_input=message,
                    include_long_term=False,  # Keep fast for background
                    save_locally=True,
                )

                return {
                    "visualization_suitable": True,
                    "image_generated": image_result.get("success", False),
                    "visual_prompt": image_result.get("visual_prompt"),
                    "emotion_type": image_result.get("emotion_type"),
                    "image_data": image_result.get("image_data"),
                    "status": "completed",
                    "readiness": readiness,
                }
            else:
                return {
                    "visualization_suitable": False,
                    "reason": result.get(
                        "recommendation", "Not suitable for visualization"
                    ),
                    "status": "not_suitable",
                }

        except Exception as e:
            logger.error(f"Error in visualization background processing: {e}")
            return {"error": str(e), "visualization_suitable": False, "status": "error"}

    async def _process_general_background(
        self, user_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process general mode background tasks with mode suggestions."""
        try:
            # Check for scheduling opportunities using existing extractor
            schedule_opportunity = self.schedule_analyzer.analyze_opportunity(
                message, "", context.get("context", "")
            )

            schedule_suggestion = None
            if schedule_opportunity.get("should_suggest", False):
                schedule_info = await self.schedule_extractor.extract_information(
                    message, "", context.get("context", ""), schedule_opportunity
                )
                schedule_suggestion = schedule_info

            # Check if user might benefit from other modes
            mode_suggestion = await self.mode_detector.suggest_mode_switch(
                "general", message, context
            )

            return {
                "schedule_analysis": schedule_opportunity,
                "schedule_suggestion": schedule_suggestion,
                "mode_suggestion": mode_suggestion,
                "general_processing": "completed",
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Error in general background processing: {e}")
            return {"error": str(e), "general_processing": "failed", "status": "error"}

    async def _enrich_context_background(
        self, user_id: str, message: str, conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Enrich context in background for future fast responses."""
        try:
            # Get comprehensive memory context using existing memory service
            memory_context = await self.memory_service.get_memory_context(
                user_id=user_id, query=message, conversation_id=conversation_id
            )

            # Build enriched context
            enriched_context = self._build_enriched_context(message, memory_context)

            # Cache for future fast responses
            context_hash = await self.cache_manager.generate_context_hash(
                user_id, message
            )
            await self.cache_manager.cache_enriched_context(
                user_id, context_hash, enriched_context
            )

            return {
                "context_enriched": True,
                "short_term_memories": len(memory_context.short_term),
                "long_term_memories": len(memory_context.long_term),
                "cached": True,
            }

        except Exception as e:
            logger.error(f"Error in context enrichment: {e}")
            return {"error": str(e), "context_enriched": False}

    def _build_enriched_context(
        self, current_message: str, memory_context: MemoryContext
    ) -> str:
        """Build enriched context from memory context."""
        context_parts = []

        # Add recent conversation context
        if memory_context.short_term:
            context_parts.append("Recent conversation context:")
            for memory in memory_context.short_term[-5:]:  # Last 5 messages
                context_parts.append(f"- {memory.content}")

        # Add relevant long-term context
        if memory_context.long_term:
            context_parts.append("\nRelevant background information:")
            for memory in memory_context.long_term[:3]:  # Top 3 relevant
                context_parts.append(f"- {memory.content}")

        # Add digest if available
        if memory_context.digest:
            context_parts.append(f"\nOverall context: {memory_context.digest}")

        return (
            "\n".join(context_parts)
            if context_parts
            else "No previous context available."
        )
