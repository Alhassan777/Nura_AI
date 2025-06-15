"""
Centralized Configuration Manager for Nura Backend
Handles all configuration loading and validation in one place to avoid duplicate messages.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Centralized configuration manager to avoid duplicate config messages."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not ConfigurationManager._initialized:
            self._load_all_configs()
            ConfigurationManager._initialized = True

    def _load_all_configs(self):
        """Load and validate all configurations once."""
        self.config_errors = []
        self.config_warnings = []

        # Vector Database Configuration
        self._setup_vector_db_config()

        # Authentication Configuration
        self._setup_auth_config()

        # Audit Configuration
        self._setup_audit_config()

        # Prompt Configuration
        self._setup_prompt_config()

        # Print consolidated configuration status
        self._print_configuration_status()

    def _setup_vector_db_config(self):
        """Setup vector database configuration."""
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "chroma").lower()
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self.use_pinecone = os.getenv("USE_PINECONE", "false").lower() == "true"

        # Check for missing required keys
        if not self.google_api_key:
            self.config_errors.append("GOOGLE_API_KEY")

        if (
            self.vector_db_type == "pinecone" or self.use_pinecone
        ) and not self.pinecone_api_key:
            self.config_errors.append("PINECONE_API_KEY")

        # Add warnings for default configurations
        if self.redis_url == "redis://localhost:6379":
            self.config_warnings.append("REDIS_URL not set - using default local Redis")

        if self.vector_db_type == "pinecone":
            self.config_warnings.append("Using Pinecone vector database")
        else:
            self.config_warnings.append(
                "Using ChromaDB (local) - consider Pinecone for production"
            )

    def _setup_auth_config(self):
        """Setup authentication configuration."""
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")

        if not self.supabase_url:
            self.config_errors.append("SUPABASE_URL")
        if not self.supabase_anon_key:
            self.config_errors.append("SUPABASE_ANON_KEY")

    def _setup_audit_config(self):
        """Setup audit logging configuration."""
        self.audit_log_dir = os.getenv("AUDIT_LOG_DIR", "./logs/audit")
        self.use_google_cloud_logging = (
            os.getenv("USE_GOOGLE_CLOUD_LOGGING", "false").lower() == "true"
        )

        # Create audit logs directory
        os.makedirs(self.audit_log_dir, exist_ok=True)

        if not self.use_google_cloud_logging:
            log_file = os.path.join(self.audit_log_dir, "memory_audit.log")
            self.config_warnings.append(f"Audit logging: local file ({log_file})")

    def _setup_prompt_config(self):
        """Setup prompt file configuration for 3-mode system."""
        # Get the directory where prompts should be located
        config_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(config_dir, "utils", "prompts", "chat")

        # Define the new 3-mode prompt structure
        self.prompt_files = {
            # Mode-specific system prompts
            "system_prompt_general": os.path.join(
                prompts_dir, "system_prompt_general.txt"
            ),
            "system_prompt_action_plan": os.path.join(
                prompts_dir, "system_prompt_action_plan.txt"
            ),
            "system_prompt_visualization": os.path.join(
                prompts_dir, "system_prompt_visualization.txt"
            ),
            # Mode-specific conversation guidelines
            "conversation_guidelines_general": os.path.join(
                prompts_dir, "conversation_guidelines_general.txt"
            ),
            "conversation_guidelines_action_plan": os.path.join(
                prompts_dir, "conversation_guidelines_action_plan.txt"
            ),
            "conversation_guidelines_visualization": os.path.join(
                prompts_dir, "conversation_guidelines_visualization.txt"
            ),
            # Shared prompts
            "crisis_detection": os.path.join(prompts_dir, "crisis_detection.txt"),
            "memory_scoring": os.path.join(prompts_dir, "memory_scoring.txt"),
            "action_plan_generation": os.path.join(
                prompts_dir, "action_plan_generation.txt"
            ),
            "photo_generation": os.path.join(prompts_dir, "photo_generation.txt"),
            "schedule_extraction": os.path.join(prompts_dir, "schedule_extraction.txt"),
        }

        # Check for missing prompt files
        missing_prompts = []
        for prompt_name, file_path in self.prompt_files.items():
            if not os.path.exists(file_path):
                missing_prompts.append(prompt_name.upper())

        # Add summary of prompt configuration
        if missing_prompts:
            self.config_errors.extend(missing_prompts)
        else:
            # Count available modes
            modes_available = []
            for mode in ["general", "action_plan", "visualization"]:
                if os.path.exists(
                    self.prompt_files[f"system_prompt_{mode}"]
                ) and os.path.exists(
                    self.prompt_files[f"conversation_guidelines_{mode}"]
                ):
                    modes_available.append(mode)

            if modes_available:
                self.config_warnings.append(
                    f"Chat modes available: {', '.join(modes_available)}"
                )

            shared_prompts = sum(
                1
                for prompt in [
                    "crisis_detection",
                    "memory_scoring",
                    "action_plan_generation",
                    "photo_generation",
                    "schedule_extraction",
                ]
                if os.path.exists(self.prompt_files[prompt])
            )
            if shared_prompts > 0:
                self.config_warnings.append(
                    f"Shared prompts loaded: {shared_prompts}/5"
                )

    def _print_configuration_status(self):
        """Print consolidated configuration status once."""
        print("\n" + "=" * 80)
        print("🔧 NURA BACKEND CONFIGURATION STATUS")
        print("=" * 80)

        if self.config_errors:
            print("\n❌ CONFIGURATION ERRORS:")
            for error in self.config_errors:
                print(f"   • Missing: {error}")
            print("\n⚠️  Some services may have limited functionality.")
            print("   See .env.example for required environment variables.")
        else:
            print("\n✅ All required configurations are set.")

        if self.config_warnings:
            print(f"\nℹ️  CONFIGURATION NOTICES:")
            for warning in self.config_warnings:
                print(f"   • {warning}")

        print(f"\n📊 Vector Database: {self.vector_db_type.upper()}")
        print(
            f"📝 Audit Logging: {'Google Cloud' if self.use_google_cloud_logging else 'Local File'}"
        )
        print("=" * 80 + "\n")

    def has_errors(self) -> bool:
        """Check if there are any configuration errors."""
        return len(self.config_errors) > 0

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self, key, default)


# Global configuration manager instance
config_manager = ConfigurationManager()
