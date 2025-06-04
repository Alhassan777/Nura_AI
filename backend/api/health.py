"""
Health API Module
Handles health checks, configuration testing, and system status endpoints.
Consolidated health monitoring for the entire Nura application.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])


# Helper function
def get_configuration_status() -> Dict[str, Any]:
    """Get current configuration status for API responses."""
    from services.memory.config import Config

    missing_required = []
    missing_optional = []

    # Check required configs
    if not Config.GOOGLE_API_KEY:
        missing_required.append("GOOGLE_API_KEY")

    # Check vector database requirements
    if Config.VECTOR_DB_TYPE == "pinecone" or Config.USE_PINECONE:
        if not Config.PINECONE_API_KEY:
            missing_required.append("PINECONE_API_KEY")

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


@router.get("/")
async def health_check():
    """Main health check endpoint - used by Docker, frontend, and monitoring."""
    config_status = get_configuration_status()

    return {
        "status": (
            "healthy" if not config_status["has_configuration_issues"] else "degraded"
        ),
        "message": "Nura Backend Service is running",
        "configuration": config_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2025-05-26-consolidated",
        "services": {
            "memory": "active",
            "chat": "active",
            "voice": "active",
            "privacy": "active",
        },
    }


@router.get("/config/test")
async def test_configuration():
    """Test endpoint to verify configuration."""
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
            from utils.redis_client import get_redis_client

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

        # Test chat service (database connection)
        try:
            from services.chat.database import get_db

            db = next(get_db())
            db.execute("SELECT 1")
            services_status["chat"] = {
                "status": "healthy",
                "message": "Chat service database connected",
            }
        except Exception as e:
            services_status["chat"] = {
                "status": "error",
                "message": f"Chat service error: {str(e)}",
            }

        # Test assistant service configuration
        try:
            from services.assistant.mental_health_assistant import MentalHealthAssistant

            assistant = MentalHealthAssistant()
            services_status["assistant"] = {
                "status": "healthy",
                "message": "Assistant service operational",
            }
        except Exception as e:
            services_status["assistant"] = {
                "status": "error",
                "message": f"Assistant service error: {str(e)}",
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
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detailed")
async def get_detailed_health():
    """Get detailed health information including metrics and diagnostics."""
    try:
        basic_health = await health_check()
        service_status = await get_service_status()

        # Add additional diagnostic information
        diagnostic_info = {
            "system_info": {
                "python_version": "3.12+",
                "framework": "FastAPI",
                "architecture": "microservices",
            },
            "feature_flags": {
                "voice_service": True,
                "memory_storage": True,
                "chat_service": True,
                "image_generation": True,
            },
            "security": {
                "jwt_authentication": True,
                "cors_enabled": True,
                "rate_limiting": False,  # Add if implemented
            },
        }

        return {
            **basic_health,
            "service_details": service_status["services"],
            "diagnostics": diagnostic_info,
            "health_check_type": "detailed",
        }

    except Exception as e:
        logger.error(f"Error getting detailed health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
