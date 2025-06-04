"""
Chat Service Configuration.
Extends the base memory service configuration with chat-specific settings.
"""

import os
from ..memory.config import Config as BaseConfig


class ChatConfig(BaseConfig):
    """Chat service configuration extending base memory config."""

    # Supabase Configuration - reuse existing SUPABASE_URL
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_DATABASE_PASSWORD: str = os.getenv("SUPABASE_DATABASE_PASSWORD", "")

    # Legacy: Direct database URL (takes priority if set)
    SUPABASE_DATABASE_URL: str = os.getenv("SUPABASE_DATABASE_URL", "")

    # Fallback individual components
    SUPABASE_DB_HOST: str = os.getenv("SUPABASE_DB_HOST", "localhost")
    SUPABASE_DB_PORT: str = os.getenv("SUPABASE_DB_PORT", "5432")
    SUPABASE_DB_NAME: str = os.getenv("SUPABASE_DB_NAME", "postgres")
    SUPABASE_DB_USER: str = os.getenv("SUPABASE_DB_USER", "postgres")
    SUPABASE_DB_PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")

    # Chat Service Specific Settings
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "100"))
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
    AUTO_ARCHIVE_DAYS: int = int(os.getenv("AUTO_ARCHIVE_DAYS", "30"))

    # Crisis Detection Settings
    CRISIS_KEYWORDS_THRESHOLD: int = int(os.getenv("CRISIS_KEYWORDS_THRESHOLD", "2"))
    ENABLE_CRISIS_INTERVENTION: bool = (
        os.getenv("ENABLE_CRISIS_INTERVENTION", "true").lower() == "true"
    )

    # Memory Extraction Settings
    AUTO_EXTRACT_MEMORIES: bool = (
        os.getenv("AUTO_EXTRACT_MEMORIES", "true").lower() == "true"
    )
    MEMORY_EXTRACTION_DELAY_SECONDS: int = int(
        os.getenv("MEMORY_EXTRACTION_DELAY_SECONDS", "5")
    )

    # Privacy Settings
    DEFAULT_DATA_RETENTION_DAYS: int = int(
        os.getenv("DEFAULT_DATA_RETENTION_DAYS", "365")
    )
    REQUIRE_PRIVACY_CONSENT: bool = (
        os.getenv("REQUIRE_PRIVACY_CONSENT", "true").lower() == "true"
    )

    # Authentication Settings (for the localStorage-based system)
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))

    @classmethod
    def validate_chat_config(cls) -> None:
        """Validate chat-specific configuration."""
        # First validate base config
        cls.validate()

        # Check Supabase configuration
        if not cls.get_database_url():
            raise ValueError(
                "Database configuration missing. Please set either:\n"
                "1. SUPABASE_URL + SUPABASE_DATABASE_PASSWORD, or\n"
                "2. SUPABASE_DATABASE_URL, or\n"
                "3. Individual DB components (SUPABASE_DB_HOST, etc.)"
            )

    @classmethod
    def get_database_url(cls) -> str:
        """Get the complete database URL for Supabase with smart auto-generation."""

        # Option 1: Direct database URL (highest priority)
        if cls.SUPABASE_DATABASE_URL:
            return cls.SUPABASE_DATABASE_URL

        # Option 2: Auto-generate from SUPABASE_URL + password (recommended)
        if cls.SUPABASE_URL and cls.SUPABASE_DATABASE_PASSWORD:
            # Extract project ref from SUPABASE_URL
            # Example: https://ehbrqbzlsabttncyfkkb.supabase.co -> ehbrqbzlsabttncyfkkb
            project_ref = cls.SUPABASE_URL.replace("https://", "").replace(
                ".supabase.co", ""
            )
            return f"postgresql://postgres:{cls.SUPABASE_DATABASE_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"

        # Option 3: Individual components (fallback)
        return f"postgresql://{cls.SUPABASE_DB_USER}:{cls.SUPABASE_DB_PASSWORD}@{cls.SUPABASE_DB_HOST}:{cls.SUPABASE_DB_PORT}/{cls.SUPABASE_DB_NAME}"
