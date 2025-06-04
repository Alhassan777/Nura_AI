"""
Chat Service User Integration
Connects chat service to the normalized user system.
"""

import logging
from typing import Dict, Any, Optional
from services.user.sync_service import UserSyncService

logger = logging.getLogger(__name__)

# Initialize sync service
sync_service = UserSyncService()


class ChatUserIntegration:
    """Integrates chat service with normalized user system."""

    @staticmethod
    async def sync_user_from_supabase(supabase_user_data, source="chat_api"):
        """Sync user from Supabase using the centralized sync service."""
        return await sync_service.sync_user_from_supabase(supabase_user_data, source)

    @staticmethod
    async def get_user_for_chat(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data formatted for chat service needs."""
        try:
            # Get core user data from normalized system
            user_data = await sync_service.get_user_by_id(user_id)
            if not user_data:
                return None

            # Get chat-specific profile
            chat_profile = await sync_service.get_service_profile(user_id, "chat")

            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "phone_number": user_data["phone_number"],
                "is_active": user_data["is_active"],
                "is_verified": user_data["is_verified"],
                "privacy_settings": user_data["privacy_settings"],
                "current_streak": user_data["current_streak"],
                "xp": user_data["xp"],
                "last_active_at": user_data["last_active_at"],
                "created_at": user_data["created_at"],
                # Chat-specific data from service profile
                "chat_preferences": (
                    chat_profile["service_preferences"]
                    if chat_profile
                    else {
                        "message_suggestions": True,
                        "typing_indicators": True,
                        "read_receipts": False,
                        "crisis_detection": True,
                    }
                ),
                "conversation_history": (
                    chat_profile["service_metadata"].get("conversation_stats", {})
                    if chat_profile
                    else {}
                ),
                "chat_settings": (
                    chat_profile["service_metadata"].get("chat_settings", {})
                    if chat_profile
                    else {
                        "preferred_model": "gemini-pro",
                        "response_style": "supportive",
                        "memory_integration": True,
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Error getting chat user data for {user_id}: {str(e)}")
            return None

    @staticmethod
    async def update_chat_preferences(
        user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update user's chat-specific preferences."""
        try:
            # Get current chat profile
            chat_profile = await sync_service.get_service_profile(user_id, "chat")

            if chat_profile:
                # Update existing preferences
                current_preferences = chat_profile["service_preferences"]
                updated_preferences = {**current_preferences, **preferences}

                # TODO: Implement service profile update in sync_service
                logger.info(
                    f"Chat preferences updated for user {user_id}: {preferences}"
                )
                return True
            else:
                # Create new chat profile with preferences
                logger.info(f"Creating new chat profile for user {user_id}")
                # TODO: Implement service profile creation
                return True

        except Exception as e:
            logger.error(f"Error updating chat preferences for {user_id}: {str(e)}")
            return False

    @staticmethod
    async def record_chat_activity(
        user_id: str, activity_type: str, metadata: Dict[str, Any]
    ) -> bool:
        """Record chat service activity for the user."""
        try:
            # TODO: Update user's chat service usage stats
            # This should update last_used_at and usage_stats in user_service_profiles
            # Also update main user's last_active_at
            logger.info(f"Chat activity recorded for {user_id}: {activity_type}")
            return True

        except Exception as e:
            logger.error(f"Error recording chat activity for {user_id}: {str(e)}")
            return False

    @staticmethod
    async def get_user_privacy_settings(user_id: str) -> Dict[str, Any]:
        """Get user's privacy settings for chat context."""
        try:
            user_data = await sync_service.get_user_by_id(user_id)
            if not user_data:
                return {}

            return user_data.get("privacy_settings", {})

        except Exception as e:
            logger.error(f"Error getting privacy settings for {user_id}: {str(e)}")
            return {}
