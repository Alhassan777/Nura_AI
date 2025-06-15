"""
Configuration for Voice Service.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class VoiceConfig:
    """Configuration for voice assistant service."""

    def __init__(self):
        # Vapi Configuration
        self.VAPI_API_KEY = os.getenv("VAPI_API_KEY")
        self.VAPI_PUBLIC_KEY = os.getenv("NEXT_PUBLIC_VAPI_PUBLIC_KEY", "")
        self.VAPI_SERVER_SECRET = os.getenv("VAPI_SERVER_SECRET", "")
        self.VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")
        self.VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
        self.VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
        self.WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
        self.DEFAULT_ASSISTANT_ID = os.getenv(
            "VAPI_DEFAULT_ASSISTANT_ID", "default-assistant"
        )

        # Supabase Configuration - reuse existing SUPABASE_URL
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_DATABASE_PASSWORD = os.getenv("SUPABASE_DATABASE_PASSWORD", "")

        # Legacy Database URLs (for backward compatibility)
        self.VOICE_DATABASE_URL = self._get_database_url()
        self.SCHEDULING_DATABASE_URL = os.getenv("SCHEDULING_DATABASE_URL")
        self.SAFETY_NETWORK_DATABASE_URL = os.getenv("SAFETY_NETWORK_DATABASE_URL")
        self.MEMORY_DATABASE_URL = os.getenv("MEMORY_DATABASE_URL")

        # Redis Configuration
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # API Endpoints Configuration
        self.SCHEDULING_API_BASE = os.getenv(
            "SCHEDULING_API_BASE", "http://localhost:8000/scheduling"
        )
        self.SAFETY_NETWORK_API_BASE = os.getenv(
            "SAFETY_NETWORK_API_BASE", "http://localhost:8000/safety_network"
        )
        self.MEMORY_API_BASE = os.getenv(
            "MEMORY_API_BASE", "http://localhost:8000/memory"
        )
        self.IMAGE_GENERATION_API_BASE = os.getenv(
            "IMAGE_GENERATION_API_BASE", "http://localhost:8000/image-generation"
        )
        self.USER_API_BASE = os.getenv("USER_API_BASE", "http://localhost:8000/users")

        # External Service APIs
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.HUGGING_FACE_TOKEN = os.getenv("HF_TOKEN")

        # Webhook Configuration
        self.WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
        self.MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

        # Queue settings
        self.QUEUE_NAME = "voice_calls"
        self.MAX_RETRIES = 3

        # Webhook settings
        self.WEBHOOK_PATH = "/vapi/webhooks"

        # Call limits
        self.MAX_CALL_DURATION_MINUTES = int(
            os.getenv("MAX_CALL_DURATION_MINUTES", "30")
        )
        self.MAX_CONCURRENT_CALLS_PER_USER = int(
            os.getenv("MAX_CONCURRENT_CALLS_PER_USER", "1")
        )

        # Scheduling
        self.SCHEDULER_ENABLED = (
            os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
        )
        self.SCHEDULER_CHECK_INTERVAL_SECONDS = int(
            os.getenv("SCHEDULER_CHECK_INTERVAL_SECONDS", "60")
        )

    def _get_database_url(self) -> str:
        """Get database URL with smart auto-generation from SUPABASE_URL."""

        # Option 1: Direct database URL (highest priority)
        direct_url = os.getenv("VOICE_DATABASE_URL")
        if direct_url:
            return direct_url

        # Option 2: Auto-generate from SUPABASE_URL + password (recommended)
        if self.SUPABASE_URL and self.SUPABASE_DATABASE_PASSWORD:
            # Extract project ref from SUPABASE_URL
            # Example: https://ehbrqbzlsabttncyfkkb.supabase.co -> ehbrqbzlsabttncyfkkb
            project_ref = self.SUPABASE_URL.replace("https://", "").replace(
                ".supabase.co", ""
            )
            return f"postgresql://postgres:{self.SUPABASE_DATABASE_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"

        # Option 3: Fallback to legacy individual components
        db_host = os.getenv("SUPABASE_DB_HOST", "localhost")
        db_port = os.getenv("SUPABASE_DB_PORT", "5432")
        db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        db_user = os.getenv("SUPABASE_DB_USER", "postgres")
        db_password = os.getenv("SUPABASE_DB_PASSWORD", "")

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        missing_fields = []

        if not self.VAPI_API_KEY:
            missing_fields.append("VAPI_API_KEY")

        if not self.VOICE_DATABASE_URL:
            missing_fields.append(
                "Database configuration (SUPABASE_URL + SUPABASE_DATABASE_PASSWORD)"
            )

        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}"
            )

        return True

    def get_api_endpoint(self, service: str) -> str:
        """Get API endpoint for a specific service."""
        endpoints = {
            "scheduling": self.SCHEDULING_API_BASE,
            "safety_network": self.SAFETY_NETWORK_API_BASE,
            "memory": self.MEMORY_API_BASE,
            "image_generation": self.IMAGE_GENERATION_API_BASE,
            "user": self.USER_API_BASE,
        }

        if service not in endpoints:
            raise ValueError(
                f"Unknown service: {service}. Available: {list(endpoints.keys())}"
            )

        return endpoints[service]


# Global config instance
config = VoiceConfig()
