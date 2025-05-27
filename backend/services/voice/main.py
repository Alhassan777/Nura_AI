"""
Standalone FastAPI application for Voice Service.
Use this to run the voice service independently.
For integrated deployment, use the centralized backend/main.py instead.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api import router as voice_router
from .database import create_tables
from .config import config
from .queue_worker import schedule_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting Voice Service (Standalone Mode)...")

    # Validate configuration
    try:
        config.validate()
        logger.info("✅ Voice service configuration validated")
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        # Continue anyway for development

    # Create database tables
    try:
        create_tables()
        logger.info("✅ Voice service database tables ready")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")

    # Start scheduler worker if enabled
    if config.SCHEDULER_ENABLED:
        try:
            worker_task = asyncio.create_task(schedule_worker.start())
            logger.info("✅ Schedule worker started")
        except Exception as e:
            logger.error(f"❌ Failed to start schedule worker: {e}")
            worker_task = None
    else:
        worker_task = None
        logger.info("📝 Schedule worker disabled by configuration")

    logger.info("🎙️ Voice Service is ready (Standalone Mode)!")

    yield

    # Shutdown
    logger.info("Shutting down Voice Service (Standalone Mode)...")

    if worker_task:
        schedule_worker.stop()
        try:
            await asyncio.wait_for(worker_task, timeout=10.0)
            logger.info("✅ Schedule worker stopped gracefully")
        except asyncio.TimeoutError:
            logger.warning("⚠️ Schedule worker shutdown timeout")
            worker_task.cancel()

    logger.info("👋 Voice Service shutdown complete")


def create_voice_app() -> FastAPI:
    """Create and configure the voice service FastAPI app for standalone deployment."""
    app = FastAPI(
        title="Nura Voice Service (Standalone)",
        description="Voice call management and scheduling service - Standalone deployment",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Include voice router
    app.include_router(voice_router)

    return app


# Create app instance
app = create_voice_app()


if __name__ == "__main__":
    import uvicorn

    print("🎙️ Starting Voice Service in Standalone Mode")
    print("📝 For integrated deployment, use backend/main.py instead")

    uvicorn.run(
        "voice_standalone:app",
        host="0.0.0.0",
        port=8001,  # Different port from main memory service
        reload=True,
        log_level="info",
    )
