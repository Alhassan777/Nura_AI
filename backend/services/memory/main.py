import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .api import app
from .config import Config


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def main():
    """Run the memory service."""
    # Validate configuration
    Config.validate()

    # Create application
    app = create_app()

    # Run server
    uvicorn.run(
        "src.services.memory.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
    )


if __name__ == "__main__":
    main()
