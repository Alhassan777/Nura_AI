"""
Main FastAPI Application
Centralized backend API that combines all modular components.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import modular API routers
from api.memory import router as memory_router
from api.chat import router as chat_router
from api.privacy import router as privacy_router
from api.health import router as health_router

# Import service routers
from services.voice.api import router as voice_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nura Backend API",
    description="Modular mental health chat application backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular API routers
app.include_router(health_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(privacy_router, prefix="/api")

# Include service routers
app.include_router(voice_router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Nura Backend API - Modular Architecture",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "modules": {
            "memory": "/api/memory",
            "chat": "/api/chat",
            "privacy": "/api/privacy",
            "voice": "/api/voice",
        },
        "architecture": "modular",
        "description": "Mental health chat application with voice integration",
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Starting Nura Backend API - Modular Architecture")
    logger.info("📋 Available modules: Memory, Chat, Privacy, Voice")
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

    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info")
