import os
import logging
from typing import Dict, Any

# Load environment variables from .env
try:
    from dotenv import load_dotenv

    # Try .env first, then .env.local as fallback
    if os.path.exists(".env"):
        load_dotenv(".env")
    elif os.path.exists(".env.local"):
        load_dotenv(".env.local")
except ImportError:
    # dotenv not available, continue without it
    pass

# Set up logging
logger = logging.getLogger(__name__)


def load_prompt_from_file(file_path: str, fallback_content: str = "") -> str:
    """Load prompt content from a file, with fallback to environment variable or default."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    logger.info(f"Loaded prompt from file: {file_path}")
                    return content

        logger.warning(f"Prompt file not found: {file_path}, using fallback")
        return fallback_content
    except Exception as e:
        logger.error(f"Error loading prompt file {file_path}: {e}")
        return fallback_content


class Config:
    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Chroma configuration
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma")

    # Google Cloud configuration
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    USE_VERTEX_AI: bool = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

    # Pinecone configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "nura-memories")
    USE_PINECONE: bool = os.getenv("USE_PINECONE", "false").lower() == "true"

    # Vector database selection (pinecone, vertex, or chroma)
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma").lower()

    # Model configuration
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv(
        "GEMINI_EMBEDDING_MODEL", "models/gemini-2.0-flash"
    )

    # JWT configuration (optional - not used currently)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Service configuration
    SHORT_TERM_MEMORY_SIZE: int = int(os.getenv("SHORT_TERM_MEMORY_SIZE", "100"))
    LONG_TERM_MEMORY_SIZE: int = int(os.getenv("LONG_TERM_MEMORY_SIZE", "1000"))
    RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.6"))
    STABILITY_THRESHOLD: float = float(os.getenv("STABILITY_THRESHOLD", "0.7"))
    EXPLICITNESS_THRESHOLD: float = float(os.getenv("EXPLICITNESS_THRESHOLD", "0.5"))
    MIN_SCORE_THRESHOLD: float = float(os.getenv("MIN_SCORE_THRESHOLD", "0.6"))

    # Prompt file paths
    MENTAL_HEALTH_SYSTEM_PROMPT_FILE: str = os.getenv(
        "MENTAL_HEALTH_SYSTEM_PROMPT_FILE",
        "services/memory/prompts/system_prompt.txt",
    )
    CONVERSATION_GUIDELINES_FILE: str = os.getenv(
        "CONVERSATION_GUIDELINES_FILE",
        "services/memory/prompts/conversation_guidelines.txt",
    )
    CRISIS_DETECTION_PROMPT_FILE: str = os.getenv(
        "CRISIS_DETECTION_PROMPT_FILE",
        "services/memory/prompts/crisis_detection.txt",
    )
    MEMORY_COMPREHENSIVE_SCORING_PROMPT_FILE: str = os.getenv(
        "MEMORY_COMPREHENSIVE_SCORING_PROMPT_FILE",
        "services/memory/prompts/memory_scoring.txt",
    )

    @classmethod
    def get_mental_health_system_prompt(cls) -> str:
        """Get the mental health system prompt from file or environment."""
        # Try file first, then environment variable, then fallback
        prompt = load_prompt_from_file(
            cls.MENTAL_HEALTH_SYSTEM_PROMPT_FILE,
            os.getenv("MENTAL_HEALTH_SYSTEM_PROMPT", ""),
        )

        if not prompt:
            logger.error("MENTAL_HEALTH_SYSTEM_PROMPT not configured")
            return "⚠️ CONFIGURATION ERROR: Mental health assistant system prompt not configured."

        return prompt

    @classmethod
    def get_conversation_guidelines(cls) -> str:
        """Get the conversation guidelines from file or environment."""
        prompt = load_prompt_from_file(
            cls.CONVERSATION_GUIDELINES_FILE, os.getenv("CONVERSATION_GUIDELINES", "")
        )

        if not prompt:
            logger.error("CONVERSATION_GUIDELINES not configured")
            return "⚠️ CONFIGURATION ERROR: Conversation guidelines not configured."

        return prompt

    @classmethod
    def get_crisis_detection_prompt(cls) -> str:
        """Get the crisis detection prompt from file or environment."""
        prompt = load_prompt_from_file(
            cls.CRISIS_DETECTION_PROMPT_FILE, os.getenv("CRISIS_DETECTION_PROMPT", "")
        )

        if not prompt:
            logger.error("CRISIS_DETECTION_PROMPT not configured")
            return "⚠️ CONFIGURATION ERROR: Crisis detection not properly configured."

        return prompt

    @classmethod
    def get_memory_comprehensive_scoring_prompt(cls) -> str:
        """Get the memory comprehensive scoring prompt from file or environment."""
        prompt = load_prompt_from_file(
            cls.MEMORY_COMPREHENSIVE_SCORING_PROMPT_FILE,
            os.getenv("MEMORY_COMPREHENSIVE_SCORING_PROMPT", ""),
        )

        if not prompt:
            logger.error("MEMORY_COMPREHENSIVE_SCORING_PROMPT not configured")
            return "⚠️ CONFIGURATION ERROR: Comprehensive memory scoring not configured."

        return prompt

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        required_vars = ["GOOGLE_API_KEY"]  # Always need this for embeddings

        # Add vector database specific requirements
        if cls.VECTOR_DB_TYPE == "pinecone" or cls.USE_PINECONE:
            required_vars.append("PINECONE_API_KEY")
        elif cls.VECTOR_DB_TYPE == "vertex" or cls.USE_VERTEX_AI:
            required_vars.append("GOOGLE_CLOUD_PROJECT")

        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            error_msg = f"""
⚠️  CONFIGURATION ERROR: Memory Service cannot start due to missing environment variables.

Missing required variables:
{chr(10).join(f"  - {var}" for var in missing_vars)}

REQUIRED ACTION:
1. Copy env.example to .env: cp env.example .env
2. Set the missing environment variables in your .env file
3. For Pinecone setup, visit: https://www.pinecone.io/
4. For Google Cloud setup, visit: https://console.cloud.google.com/
5. For Gemini API key, visit: https://ai.google.dev/

Current values:
  - GOOGLE_API_KEY: {'[SET]' if cls.GOOGLE_API_KEY else '[NOT SET]'}
  - VECTOR_DB_TYPE: {cls.VECTOR_DB_TYPE}
  - PINECONE_API_KEY: {'[SET]' if cls.PINECONE_API_KEY else '[NOT SET]'}
  - GOOGLE_CLOUD_PROJECT: {'[SET]' if cls.GOOGLE_CLOUD_PROJECT else '[NOT SET]'}

The Memory Service will not function properly without these configurations.
"""
            logger.error(error_msg)
            print(error_msg)
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. See error message above for setup instructions."
            )

    @classmethod
    def check_optional_config(cls) -> None:
        """Check optional configuration and warn if defaults are being used."""
        warnings = []

        if cls.REDIS_URL == "redis://localhost:6379":
            warnings.append("REDIS_URL not set - using default local Redis")

        if cls.VECTOR_DB_TYPE == "chroma" and cls.CHROMA_PERSIST_DIR == "./chroma":
            warnings.append(
                "CHROMA_PERSIST_DIR not set - using default ./chroma directory"
            )

        if cls.GEMINI_MODEL == "gemini-pro":
            warnings.append("GEMINI_MODEL not set - using default gemini-pro")

        # Vector database warnings
        if cls.VECTOR_DB_TYPE == "chroma":
            warnings.append(
                "Using ChromaDB (local) - consider Pinecone or Vertex AI for production"
            )
        elif cls.VECTOR_DB_TYPE == "pinecone":
            warnings.append("Using Pinecone vector database")
        elif cls.VECTOR_DB_TYPE == "vertex":
            warnings.append("Using Google Vertex AI vector database")

        if warnings:
            warning_msg = f"""
ℹ️  CONFIGURATION NOTICE: Current vector database setup:

{chr(10).join(f"  - {warning}" for warning in warnings)}

Vector Database Type: {cls.VECTOR_DB_TYPE.upper()}
See env.example for all available configuration options.
"""
            logger.info(warning_msg)
            print(warning_msg)

    @classmethod
    def get_memory_config(cls) -> Dict[str, Any]:
        """Get memory service configuration."""
        return {
            "short_term_size": cls.SHORT_TERM_MEMORY_SIZE,
            "long_term_size": cls.LONG_TERM_MEMORY_SIZE,
            "relevance_threshold": cls.RELEVANCE_THRESHOLD,
            "stability_threshold": cls.STABILITY_THRESHOLD,
            "explicitness_threshold": cls.EXPLICITNESS_THRESHOLD,
            "min_score_threshold": cls.MIN_SCORE_THRESHOLD,
        }
