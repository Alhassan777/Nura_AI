"""
Main FastAPI application for Nura backend.
Includes all API routers and middleware.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import API routers
from api.health import router as health_router
from api.memory import router as memory_router
from api.chat import router as chat_router
from api.privacy import router as privacy_router
# from api.image_generation import router as image_generation_router

# Import service routers
from services.voice.api import router as voice_router

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
app.include_router(health_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(privacy_router, prefix="/api")
# The line `app.include_router(image_generation_router, prefix="/api")` is including the router
# defined in the `image_generation_router` module into the FastAPI application `app`.
# app.include_router(image_generation_router, prefix="/api")

# Include service routers
app.include_router(voice_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Nura Mental Health Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "memory": "/api/memory",
            "chat": "/api/chat",
            "privacy": "/api/privacy",
            "image_generation": "/api/image-generation",
        },
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Nura API v1.0.0",
        "available_endpoints": [
            "/api/health",
            "/api/memory",
            "/api/chat",
            "/api/privacy",
            "/api/image-generation",
        ],
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Starting Nura Backend API - Modular Architecture")
    logger.info("📋 Available modules: Memory, Chat, Privacy, Voice, Image Generation")
    logger.info("🔗 API Documentation: /docs")
    logger.info("❤️  Health Check: /api/health")


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
