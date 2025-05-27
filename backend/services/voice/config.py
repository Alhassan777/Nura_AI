"""
Configuration for Voice Service.
"""

import os
from typing import Optional


class VoiceConfig:
    """Voice service configuration."""

    # Database
    DATABASE_URL: str = os.getenv(
        "VOICE_DATABASE_URL", "postgresql://localhost:5432/nura_voice"
    )

    # Vapi Configuration
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PUBLIC_KEY: str = os.getenv("NEXT_PUBLIC_VAPI_PUBLIC_KEY", "")
    VAPI_SERVER_SECRET: str = os.getenv("VAPI_SERVER_SECRET", "")
    VAPI_BASE_URL: str = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

    # Default assistant (can be overridden per call)
    DEFAULT_ASSISTANT_ID: str = os.getenv("NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID", "")

    # Redis for job queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Queue settings
    QUEUE_NAME: str = "voice_calls"
    MAX_RETRIES: int = 3

    # Webhook settings
    WEBHOOK_PATH: str = "/api/vapi/webhooks"
    WEBHOOK_SECRET: str = os.getenv("VAPI_WEBHOOK_SECRET", "")

    # Call limits
    MAX_CALL_DURATION_MINUTES: int = int(os.getenv("MAX_CALL_DURATION_MINUTES", "30"))
    MAX_CONCURRENT_CALLS_PER_USER: int = int(
        os.getenv("MAX_CONCURRENT_CALLS_PER_USER", "1")
    )

    # Scheduling
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_CHECK_INTERVAL_SECONDS: int = int(
        os.getenv("SCHEDULER_CHECK_INTERVAL_SECONDS", "60")
    )

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        required_vars = [
            cls.VAPI_API_KEY,
            cls.VAPI_SERVER_SECRET,
            cls.DEFAULT_ASSISTANT_ID,
        ]

        missing = [var for var in required_vars if not var]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

        return True


# Global config instance
config = VoiceConfig()
