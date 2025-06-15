"""
Multi-Modal Chat API
Ultra-fast messaging endpoints with background processing integration.
Integrates with all existing Nura services.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Import authentication
from utils.auth import get_current_user_id

# Import the service
from .multi_modal_chat import MultiModalChatService

# Import existing service integrations for direct endpoints
from ..memory.memoryService import MemoryService
from ..privacy.processors.privacy_processor import PrivacyProcessor
from ..image_generation.emotion_visualizer import EmotionVisualizer
from ..scheduling.scheduler import ScheduleManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/chat-v2", tags=["multi-modal-chat"])

# Initialize service
multi_modal_service = MultiModalChatService()


# Pydantic models
class FastMessageRequest(BaseModel):
    message: str = Field(..., description="User's message")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for context"
    )
    mode: str = Field(
        "general", description="Chat mode: general, action_plan, visualization"
    )


class FastMessageResponse(BaseModel):
    response: str = Field(..., description="Immediate assistant response")
    mode: str = Field(..., description="Detected or specified chat mode")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    background_task_id: str = Field(
        ..., description="ID for background processing results"
    )
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    cache_performance: Dict[str, Any] = Field(
        ..., description="Cache hit/miss information"
    )
    immediate_flags: Dict[str, bool] = Field(
        ..., description="Immediate crisis/resource flags"
    )
    timestamp: str = Field(..., description="Response timestamp")


class BackgroundResultsResponse(BaseModel):
    task_id: str = Field(..., description="Background task ID")
    user_id: str = Field(..., description="User ID")
    mode: str = Field(..., description="Chat mode processed")
    started_at: str = Field(..., description="Task start timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
    tasks: Dict[str, Any] = Field(..., description="Individual task results")


class ModeInfo(BaseModel):
    name: str = Field(..., description="Human-readable mode name")
    description: str = Field(..., description="Mode description")
    keywords: List[str] = Field(..., description="Keywords that trigger this mode")


class AvailableModesResponse(BaseModel):
    modes: Dict[str, ModeInfo] = Field(..., description="Available chat modes")
    auto_detection: bool = Field(..., description="Whether auto-detection is enabled")
    mode_switching: bool = Field(..., description="Whether mode switching is supported")


class CacheStatsResponse(BaseModel):
    cache_status: str = Field(..., description="Overall cache health")
    performance_metrics: Dict[str, Any] = Field(
        ..., description="Cache performance data"
    )
    user_cache_stats: Dict[str, Any] = Field(
        ..., description="User-specific cache statistics"
    )


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall system health")
    services: Dict[str, Any] = Field(..., description="Individual service health")
    healthy_services: int = Field(..., description="Number of healthy services")
    total_services: int = Field(..., description="Total number of services")
    timestamp: str = Field(..., description="Health check timestamp")


# Cache warming request
class CacheWarmRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID to warm cache for")
    conversation_id: Optional[str] = Field(None, description="Conversation ID to warm")
    priority: str = Field("normal", description="Warming priority: low, normal, high")


# ===============================
# CORE CHAT ENDPOINTS
# ===============================


@router.post("/messages/fast", response_model=FastMessageResponse)
async def send_fast_message(
    request: FastMessageRequest,
    user_id: str = Depends(get_current_user_id),
) -> FastMessageResponse:
    """
    Ultra-fast messaging endpoint (target: 50-200ms).

    Provides immediate response while processing heavy operations in background.
    Use /background-results/{task_id} to get comprehensive results.
    """
    try:
        logger.info(f"Fast message request from user {user_id}: mode={request.mode}")

        # Process message with ultra-fast response
        result = await multi_modal_service.process_message(
            user_id=user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            mode=request.mode,
        )

        return FastMessageResponse(**result)

    except Exception as e:
        logger.error(f"Fast message processing failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


@router.get("/background-results/{task_id}", response_model=BackgroundResultsResponse)
async def get_background_results(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
) -> BackgroundResultsResponse:
    """
    Get comprehensive background processing results.

    Returns detailed analysis including:
    - Memory processing results
    - Crisis assessment
    - Mode-specific processing (action plans, visualizations)
    - Context enrichment status
    """
    try:
        results = await multi_modal_service.get_background_results(task_id)

        if not results:
            raise HTTPException(
                status_code=404,
                detail="Background task results not found or still processing",
            )

        # Verify user owns this task
        if results.get("user_id") != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied: task belongs to different user"
            )

        return BackgroundResultsResponse(**results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get background results {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve background results"
        )


# ===============================
# SYSTEM INFORMATION ENDPOINTS
# ===============================


@router.get("/modes", response_model=AvailableModesResponse)
async def get_available_modes() -> AvailableModesResponse:
    """Get information about available chat modes and their capabilities."""
    try:
        modes_info = await multi_modal_service.get_available_modes()
        return AvailableModesResponse(**modes_info)

    except Exception as e:
        logger.error(f"Failed to get available modes: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve mode information"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all integrated services.

    Checks:
    - Cache manager health
    - Memory service connectivity
    - Image generation service
    - Privacy/PII detection
    - Scheduling service
    """
    try:
        health_info = await multi_modal_service.health_check()
        return HealthCheckResponse(**health_info)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# ===============================
# CACHE MANAGEMENT ENDPOINTS
# ===============================


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    user_id: str = Depends(get_current_user_id),
) -> CacheStatsResponse:
    """Get cache performance statistics and metrics."""
    try:
        cache_health = await multi_modal_service.cache_manager.health_check()
        performance_metrics = (
            await multi_modal_service.cache_manager.get_performance_metrics()
        )
        user_stats = await multi_modal_service.cache_manager.get_user_cache_stats(
            user_id
        )

        return CacheStatsResponse(
            cache_status=cache_health.get("status", "unknown"),
            performance_metrics=performance_metrics,
            user_cache_stats=user_stats,
        )

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve cache statistics"
        )


@router.post("/cache/warm")
async def warm_cache(
    request: CacheWarmRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Proactively warm cache for better performance.

    Useful before starting a conversation session or after login.
    """
    try:
        # Use current user if no user_id specified
        target_user_id = request.user_id or current_user_id

        # Verify user can warm cache for target user
        if target_user_id != current_user_id:
            raise HTTPException(
                status_code=403, detail="Can only warm cache for your own user"
            )

        # Start cache warming in background
        background_tasks.add_task(
            multi_modal_service.cache_manager.warm_user_cache,
            target_user_id,
            request.conversation_id,
            request.priority,
        )

        return {
            "message": "Cache warming initiated",
            "user_id": target_user_id,
            "conversation_id": request.conversation_id,
            "priority": request.priority,
            "estimated_completion": "30-60 seconds",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate cache warming")


@router.delete("/cache/clear")
async def clear_user_cache(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Clear user's cache entries."""
    try:
        cleared_count = await multi_modal_service.cache_manager.clear_user_cache(
            user_id
        )

        return {
            "message": "User cache cleared successfully",
            "user_id": user_id,
            "cleared_entries": cleared_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Cache clearing failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear user cache")


# ===============================
# DIRECT SERVICE INTEGRATIONS
# ===============================


@router.get("/services/memory/stats")
async def get_memory_service_stats(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get memory service statistics using existing memory service."""
    try:
        memory_service = MemoryService()
        stats = await memory_service.get_memory_stats(user_id)

        return {
            "user_id": user_id,
            "memory_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get memory stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve memory statistics"
        )


@router.get("/services/privacy/pending-consent")
async def get_pending_privacy_consent(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get pending privacy consent requests using existing privacy service."""
    try:
        from ..privacy.processors.privacy_processor import PrivacyProcessor
        from ..memory.storage.redis_store import redis_store
        from ..memory.storage.vector_store import get_vector_store
        from ..privacy.security.pii_detector import PIIDetector
        from ..audit.audit_logger import AuditLogger

        # Initialize privacy processor with existing services
        vector_store = await get_vector_store()
        pii_detector = PIIDetector()
        audit_logger = AuditLogger()

        privacy_processor = PrivacyProcessor(
            redis_store, vector_store, pii_detector, audit_logger
        )

        pending_consents = await privacy_processor.get_pending_consent_memories(user_id)

        return {
            "user_id": user_id,
            "pending_consents": pending_consents,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get pending consent for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve pending consent information"
        )


@router.get("/services/scheduling/active")
async def get_active_schedules(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get active schedules using existing scheduling service."""
    try:
        active_schedules = ScheduleManager.get_user_schedules(user_id, active_only=True)

        return {
            "user_id": user_id,
            "active_schedules": [
                {
                    "id": schedule.id,
                    "name": schedule.name,
                    "description": schedule.description,
                    "schedule_type": schedule.schedule_type.value,
                    "next_run_at": (
                        schedule.next_run_at.isoformat()
                        if schedule.next_run_at
                        else None
                    ),
                    "reminder_method": schedule.reminder_method.value,
                }
                for schedule in active_schedules
            ],
            "total_count": len(active_schedules),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get active schedules for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve active schedules"
        )


@router.get("/services/image-generation/status")
async def get_image_generation_status(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get image generation service status using existing service."""
    try:
        emotion_visualizer = EmotionVisualizer()
        status = await emotion_visualizer.get_generation_status(user_id)

        return {
            "user_id": user_id,
            "generation_status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get image generation status for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve image generation status"
        )


# ===============================
# CONVERSATION MANAGEMENT
# ===============================


@router.post("/conversations/end")
async def end_conversation(
    conversation_id: str = Query(..., description="Conversation ID to end"),
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    End a conversation session and promote important memories.

    Uses existing memory service to handle session cleanup and memory promotion.
    """
    try:
        memory_service = MemoryService()
        result = await memory_service.end_conversation_session(conversation_id, user_id)

        # Clear conversation cache
        await multi_modal_service.cache_manager.clear_conversation_cache(
            conversation_id
        )

        return {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_end_result": result,
            "cache_cleared": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Failed to end conversation {conversation_id} for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to end conversation session"
        )


@router.get("/conversations/{conversation_id}/preview")
async def get_conversation_preview(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get a preview of conversation memories before ending session."""
    try:
        memory_service = MemoryService()
        preview = await memory_service.get_chat_session_preview(user_id)

        return {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_preview": preview,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get conversation preview for {conversation_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve conversation preview"
        )


# ===============================
# PERFORMANCE MONITORING
# ===============================


@router.get("/performance/metrics")
async def get_performance_metrics(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get detailed performance metrics for the multi-modal chat system."""
    try:
        # Get cache performance
        cache_metrics = (
            await multi_modal_service.cache_manager.get_performance_metrics()
        )

        # Get user-specific stats
        user_cache_stats = await multi_modal_service.cache_manager.get_user_cache_stats(
            user_id
        )

        # Get memory service stats
        memory_service = MemoryService()
        memory_stats = await memory_service.get_memory_stats(user_id)

        return {
            "user_id": user_id,
            "performance_metrics": {
                "cache": cache_metrics,
                "user_cache": user_cache_stats,
                "memory": memory_stats,
            },
            "system_targets": {
                "response_time_target_ms": "50-200",
                "cache_hit_rate_target": 0.85,
                "background_processing_target_ms": "1000-3000",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance metrics"
        )


# ===============================
# DEBUG AND DEVELOPMENT
# ===============================


@router.get("/debug/service-status")
async def get_debug_service_status() -> Dict[str, Any]:
    """
    Debug endpoint to check status of all integrated services.
    Useful for development and troubleshooting.
    """
    try:
        services_status = {}

        # Check each service
        try:
            memory_service = MemoryService()
            await memory_service.get_memory_stats("debug_check")
            services_status["memory_service"] = {"status": "healthy", "error": None}
        except Exception as e:
            services_status["memory_service"] = {"status": "unhealthy", "error": str(e)}

        try:
            emotion_visualizer = EmotionVisualizer()
            await emotion_visualizer.get_generation_status("debug_check")
            services_status["image_generation"] = {"status": "healthy", "error": None}
        except Exception as e:
            services_status["image_generation"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        try:
            schedules = ScheduleManager.get_user_schedules(
                "debug_check", active_only=True
            )
            services_status["scheduling"] = {"status": "healthy", "error": None}
        except Exception as e:
            services_status["scheduling"] = {"status": "unhealthy", "error": str(e)}

        # Check cache manager
        try:
            cache_health = await multi_modal_service.cache_manager.health_check()
            services_status["cache_manager"] = {
                "status": cache_health.get("status", "unknown"),
                "error": None,
            }
        except Exception as e:
            services_status["cache_manager"] = {"status": "unhealthy", "error": str(e)}

        # Overall health
        healthy_count = sum(
            1 for s in services_status.values() if s["status"] == "healthy"
        )
        total_count = len(services_status)

        return {
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Debug service status check failed: {e}")
        raise HTTPException(status_code=500, detail="Debug service status check failed")


@router.post("/action-plans/create-from-background")
async def create_action_plan_from_background(
    task_id: str = Query(..., description="Background task ID with action plan data"),
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Create an action plan from background processing results.

    This endpoint is called when the user accepts an action plan suggestion
    from the chat interface.
    """
    try:
        # Get background results
        results = await multi_modal_service.get_background_results(task_id)

        if not results:
            raise HTTPException(
                status_code=404, detail="Background task results not found"
            )

        # Verify user owns this task
        if results.get("user_id") != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied: task belongs to different user"
            )

        # Check if action plan was already created in background
        mode_specific = results.get("tasks", {}).get("mode_specific", {})

        if mode_specific.get("action_plan_created"):
            # Action plan already exists
            return {
                "action_plan_id": mode_specific.get("action_plan_id"),
                "already_created": True,
                "message": "Action plan was already created during background processing",
            }

        # Check if we have action plan data to create from
        if not mode_specific.get("should_suggest_action_plan"):
            raise HTTPException(
                status_code=400,
                detail="No action plan data available in background results",
            )

        # If we have extraction data but no database plan, create it now
        action_plan_data = mode_specific.get("action_plan", {})
        if not action_plan_data:
            raise HTTPException(
                status_code=400,
                detail="No action plan data found in background results",
            )

        # Import action plan service and create the plan
        from ...action_plans.service import ActionPlanService
        from database import get_db

        action_plan_service = ActionPlanService()
        db = next(get_db())

        try:
            # Create action plan from the background extraction
            # We'll need to reconstruct the conversation context
            conversation_context = (
                results.get("tasks", {})
                .get("context_enrichment", {})
                .get("context", "")
            )
            user_message = "Create action plan from chat conversation"  # Placeholder

            result = await action_plan_service.generate_action_plan_from_conversation(
                user_id=user_id,
                conversation_context=conversation_context,
                user_message=user_message,
                db=db,
            )

            if result and result.get("should_suggest"):
                created_plan = result["action_plan"]

                return {
                    "action_plan_id": created_plan.id,
                    "action_plan": {
                        "id": created_plan.id,
                        "title": created_plan.title,
                        "description": created_plan.description,
                        "plan_type": created_plan.plan_type,
                        "steps_count": len(created_plan.steps),
                        "generated_by_ai": created_plan.generated_by_ai,
                    },
                    "created": True,
                    "message": "Action plan created successfully",
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create action plan from background data",
                )

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create action plan from background {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create action plan from background results",
        )


@router.get("/background-results/{task_id}")
async def get_background_results(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get background processing results for a task.

    This endpoint allows the frontend to retrieve the results of background
    processing tasks, including action plan suggestions, crisis assessments, etc.
    """
    try:
        results = await multi_modal_service.get_background_results(task_id)

        if not results:
            raise HTTPException(
                status_code=404, detail="Background task results not found"
            )

        # Verify user owns this task
        if results.get("user_id") != user_id:
            raise HTTPException(
                status_code=403, detail="Access denied: task belongs to different user"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get background results for task {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve background results"
        )
