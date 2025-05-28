"""
Health API Module
Handles health checks, configuration testing, and system status endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio

# Import utilities
from utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])


# Helper function
def get_configuration_status() -> Dict[str, Any]:
    """Get current configuration status for API responses."""
    from services.memory.config import Config

    missing_required = []
    missing_optional = []

    # Check required configs based on actual Config validation logic
    if not Config.GOOGLE_API_KEY:
        missing_required.append("GOOGLE_API_KEY")

    # Check vector database specific requirements
    if Config.VECTOR_DB_TYPE == "pinecone" or Config.USE_PINECONE:
        if not Config.PINECONE_API_KEY:
            missing_required.append("PINECONE_API_KEY")

    # Check optional configs - only flag if they're actually missing/broken
    try:
        prompt = Config.get_mental_health_system_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("MENTAL_HEALTH_SYSTEM_PROMPT")
    except:
        missing_optional.append("MENTAL_HEALTH_SYSTEM_PROMPT")

    try:
        prompt = Config.get_conversation_guidelines()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("CONVERSATION_GUIDELINES")
    except:
        missing_optional.append("CONVERSATION_GUIDELINES")

    try:
        prompt = Config.get_crisis_detection_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("CRISIS_DETECTION_PROMPT")
    except:
        missing_optional.append("CRISIS_DETECTION_PROMPT")

    try:
        prompt = Config.get_memory_comprehensive_scoring_prompt()
        if "CONFIGURATION ERROR" in prompt:
            missing_optional.append("MEMORY_COMPREHENSIVE_SCORING_PROMPT")
    except:
        missing_optional.append("MEMORY_COMPREHENSIVE_SCORING_PROMPT")

    # Only flag these if they're using defaults and might cause issues
    if Config.REDIS_URL == "redis://localhost:6379":
        # Only add as optional if Redis is actually not accessible
        try:
            # Create a simple async function to test Redis connection
            async def test_redis():
                redis_client = await get_redis_client()
                await redis_client.ping()

            # Run the async test
            asyncio.create_task(test_redis())
        except:
            missing_optional.append("REDIS_URL - Redis not accessible")

    has_issues = bool(missing_required or missing_optional)

    return {
        "has_configuration_issues": has_issues,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "status": "degraded" if has_issues else "fully_configured",
        "message": (
            "⚠️ Service running with missing configurations. Some features may not work as expected."
            if has_issues
            else "✅ Service fully configured"
        ),
    }


# Health endpoints
@router.get("/")
async def health_check():
    """Health check endpoint with configuration status."""
    config_status = get_configuration_status()

    return {
        "status": (
            "healthy" if not config_status["has_configuration_issues"] else "degraded"
        ),
        "message": "Nura Backend Service is running",
        "configuration": config_status,
        "timestamp": str(__import__("datetime").datetime.utcnow()),
        "version": "2025-05-26-modular",
        "services": {
            "memory": "active",
            "chat": "active",
            "voice": "active",
            "privacy": "active",
        },
    }


@router.get("/config/test")
async def test_configuration():
    """Test endpoint to verify configuration and demonstrate error handling."""
    config_status = get_configuration_status()

    if config_status["has_configuration_issues"]:
        logger.warning("Configuration test failed - missing environment variables")
        return {
            "status": "CONFIGURATION_ERROR",
            "message": "❌ Configuration test failed. The service is running but some features may not work properly.",
            "details": config_status,
            "recommendations": [
                "Copy .env.example to .env file",
                "Set missing environment variables",
                "Restart the service after configuration",
                "Use /health endpoint for ongoing monitoring",
            ],
        }
    else:
        return {
            "status": "SUCCESS",
            "message": "✅ All configurations are properly set. Service is ready for full functionality.",
            "details": config_status,
        }


@router.get("/services")
async def get_service_status():
    """Get status of all backend services."""
    try:
        services_status = {}

        # Test memory service
        try:
            from services.memory.memoryService import MemoryService

            memory_service = MemoryService()
            services_status["memory"] = {
                "status": "healthy",
                "message": "Memory service operational",
            }
        except Exception as e:
            services_status["memory"] = {
                "status": "error",
                "message": f"Memory service error: {str(e)}",
            }

        # Test voice service
        try:
            from services.voice.config import config as voice_config

            services_status["voice"] = {
                "status": "healthy" if voice_config.VAPI_API_KEY else "degraded",
                "message": (
                    "Voice service operational"
                    if voice_config.VAPI_API_KEY
                    else "Voice service missing API key"
                ),
            }
        except Exception as e:
            services_status["voice"] = {
                "status": "error",
                "message": f"Voice service error: {str(e)}",
            }

        # Test Redis connection
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            services_status["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful",
            }
        except Exception as e:
            services_status["redis"] = {
                "status": "error",
                "message": f"Redis connection failed: {str(e)}",
            }

        # Overall status
        overall_status = "healthy"
        if any(service["status"] == "error" for service in services_status.values()):
            overall_status = "error"
        elif any(
            service["status"] == "degraded" for service in services_status.values()
        ):
            overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "services": services_status,
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        }

    except Exception as e:
        logger.error(f"Error checking service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
