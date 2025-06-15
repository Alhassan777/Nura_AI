"""
Nura App Backend
A comprehensive mental health support platform with voice assistance.
"""

# Load environment variables first, before any other imports
from dotenv import load_dotenv
import os

# Load .env file from the backend directory
load_dotenv()

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from api.health import router as health_router
from services.memory.api import router as memory_router
from services.image_generation.api import router as image_generation_router

# Import service routers
from services.voice.api import router as voice_router
from services.chat.api import (
    router as chat_router,
)  # Full chat service with database integration
from services.chat.multi_modal_api import (
    router as multi_modal_chat_router,
)  # Multi-modal chat service
from services.privacy.api import (
    router as privacy_router,
)  # Privacy and PII detection service
from services.assistant.api import (
    router as assistant_router,
)  # Mental health assistant service
from services.action_plans.api import (
    router as action_plans_router,
)  # AI-powered action plans service
from services.audit.api import router as audit_router  # Audit logging service
from services.scheduling.api import (
    router as scheduling_router,
)  # Schedule management service
from services.safety_network.api import (
    router as safety_network_router,
)  # Safety network service
from services.safety_invitations.api import (
    router as safety_invitations_router,
)  # Safety network invitations service
from services.user.api import router as user_router  # User management service
from services.user.auth_endpoints import (
    router as auth_router,
)  # Authentication endpoints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nura Mental Health Assistant API",
    description="Backend API for Nura mental health application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(memory_router)  # JWT-secured Memory API from services/memory/api.py
app.include_router(
    image_generation_router
)  # Image Generation API from services/image_generation/api.py

# Include service routers
app.include_router(voice_router)
app.include_router(chat_router)
app.include_router(multi_modal_chat_router)
app.include_router(privacy_router)
app.include_router(assistant_router)
app.include_router(action_plans_router)
app.include_router(audit_router)
app.include_router(scheduling_router)
app.include_router(safety_network_router)
app.include_router(safety_invitations_router)
app.include_router(user_router)
app.include_router(auth_router)


# Vapi webhook endpoint - receives ALL webhook calls from Supabase for Vapi
@app.post("/vapi/webhooks")
@app.get("/vapi/webhooks")  # Some webhook services test with GET
async def vapi_webhook_handler(request: Request):
    """
    Vapi webhook endpoint that receives ALL webhook calls from Supabase.
    Supabase edge functions should route Vapi webhook types here.

    This endpoint handles:
    - Vapi voice tool calls (routed from Supabase)
    - Call events and processing
    - All Vapi-related webhooks

    Flow: Vapi → Supabase Edge Function → This Endpoint → Tool Logic
    """
    try:
        # Get request headers and payload
        headers = dict(request.headers)

        # Handle both JSON and form data
        try:
            payload = await request.json()
        except Exception:
            # Fallback for non-JSON requests (like GET health checks)
            if request.method == "GET":
                return {"status": "ok", "message": "Vapi webhook endpoint is active"}
            else:
                raise

        # Determine webhook source/type from payload or headers
        webhook_type = (
            payload.get("webhook_type")
            or payload.get("source")
            or headers.get("x-webhook-type")
            or "vapi"  # Default to vapi since this is the vapi endpoint
        )

        logger.info(f"🎯 Vapi webhook received from Supabase: type={webhook_type}")

        # Route to voice service (all webhooks on this endpoint are vapi-related)
        from services.voice.vapi_webhook_router import vapi_webhook_router

        result = await vapi_webhook_router.process_webhook(payload, headers)
        return result

    except Exception as e:
        logger.error(f"Vapi webhook processing error: {e}")
        # Always return success to prevent retries for transient errors
        return {
            "status": "error",
            "message": "Webhook processed with errors",
            "error": str(e),
        }


# Legacy webhook endpoints - for backward compatibility
@app.post("/webhooks")
async def legacy_webhooks_redirect(request: Request):
    """
    LEGACY: Redirects to the specific /vapi/webhooks endpoint.
    This maintains backward compatibility for any existing integrations.
    """
    logger.warning("⚠️ Legacy /webhooks call detected - redirecting to /vapi/webhooks")

    try:
        # Forward to the vapi webhook handler
        return await vapi_webhook_handler(request)

    except Exception as e:
        logger.error(f"Legacy webhook redirect error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Nura Mental Health Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "memory": "/memory (includes search & push for Vapi)",
            "chat": "/chat",
            "chat_v2": "/chat-v2 (multi-modal chat with ultra-fast responses)",
            "privacy": "/privacy",
            "assistant": "/assistant",
            "action_plans": "/action-plans (AI-powered action plans)",
            "audit": "/audit",
            "image_generation": "/image-generation",
            "voice": "/voice",
            "scheduling": "/scheduling",
            "safety_network": "/safety_network",
            "safety_invitations": "/safety-invitations",
            "users": "/users",
            "auth": "/auth (login, signup, logout)",
        },
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Nura API v1.0.0",
        "available_endpoints": [
            "/health",
            "/memory",
            "/chat",
            "/chat-v2",
            "/privacy",
            "/assistant",
            "/audit",
            "/image-generation",
            "/voice",
            "/scheduling",
            "/safety_network",
            "/safety-invitations",
            "/users",
            "/auth",
        ],
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Starting Nura Backend API - Clean Modular Architecture")
    logger.info(
        "📋 Available services: Memory, Chat, Privacy, Assistant, Audit, Voice, Image Generation, Safety Network, Safety Invitations"
    )
    logger.info("🔗 API Documentation: /docs")
    logger.info("❤️  Health Check: /health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 Shutting down Nura Backend API")


if __name__ == "__main__":
    import uvicorn

    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"🌐 Starting server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, reload=True, log_level="info")
