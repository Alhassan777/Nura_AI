"""
Chat Service Configuration.
Extends the base memory service configuration with chat-specific settings.
"""

import os
from ..memory.config import Config as BaseConfig


class ChatConfig(BaseConfig):
    """Chat service configuration extending base memory config."""

    # Supabase Database Configuration
    SUPABASE_DATABASE_URL: str = os.getenv("SUPABASE_DATABASE_URL", "")
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
        if not cls.SUPABASE_DATABASE_URL:
            if not all(
                [cls.SUPABASE_DB_HOST, cls.SUPABASE_DB_NAME, cls.SUPABASE_DB_USER]
            ):
                raise ValueError(
                    "Either SUPABASE_DATABASE_URL or individual Supabase DB components "
                    "(SUPABASE_DB_HOST, SUPABASE_DB_NAME, SUPABASE_DB_USER) must be set"
                )

    @classmethod
    def get_database_url(cls) -> str:
        """Get the complete database URL for Supabase."""
        if cls.SUPABASE_DATABASE_URL:
            return cls.SUPABASE_DATABASE_URL

        return f"postgresql://{cls.SUPABASE_DB_USER}:{cls.SUPABASE_DB_PASSWORD}@{cls.SUPABASE_DB_HOST}:{cls.SUPABASE_DB_PORT}/{cls.SUPABASE_DB_NAME}"
