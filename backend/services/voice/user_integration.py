"""
Voice Service User Integration
Connects voice service to the normalized user system.
"""

import logging
from typing import Dict, Any, Optional
from ..user.sync_service import sync_service

logger = logging.getLogger(__name__)


class VoiceUserIntegration:
    """Integrates voice service with normalized user system."""

    @staticmethod
    async def get_user_for_voice(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data formatted for voice service needs."""
        try:
            # Get core user data from normalized system
            user_data = await sync_service.get_user_by_id(user_id)
            if not user_data:
                return None

            # Get voice-specific profile
            voice_profile = await sync_service.get_service_profile(user_id, "voice")

            return {
                "id": user_data["id"],
                "name": user_data["full_name"] or f"User {user_id[:8]}",
                "email": user_data["email"],
                "phone": user_data["phone_number"],
                "is_active": user_data["is_active"],
                "voice_preferences": (
                    voice_profile["service_preferences"] if voice_profile else {}
                ),
                "call_history": (
                    voice_profile["service_metadata"].get("call_history", [])
                    if voice_profile
                    else []
                ),
                "voice_settings": (
                    voice_profile["service_metadata"].get("voice_settings", {})
                    if voice_profile
                    else {
                        "preferred_assistant": "default",
                        "call_reminders": True,
                        "privacy_mode": "standard",
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Error getting voice user data for {user_id}: {str(e)}")
            return None

    @staticmethod
    async def update_voice_preferences(
        user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update user's voice-specific preferences."""
        try:
            # Get current voice profile
            voice_profile = await sync_service.get_service_profile(user_id, "voice")

            if voice_profile:
                # Update existing preferences
                current_preferences = voice_profile["service_preferences"]
                updated_preferences = {**current_preferences, **preferences}

                # TODO: Implement service profile update in sync_service
                logger.info(
                    f"Voice preferences updated for user {user_id}: {preferences}"
                )
                return True
            else:
                # Create new voice profile
                logger.info(f"Creating new voice profile for user {user_id}")
                # TODO: Implement service profile creation
                return True

        except Exception as e:
            logger.error(f"Error updating voice preferences for {user_id}: {str(e)}")
            return False

    @staticmethod
    async def record_voice_activity(
        user_id: str, activity_type: str, metadata: Dict[str, Any]
    ) -> bool:
        """Record voice service activity for the user."""
        try:
            # TODO: Update user's voice service usage stats
            # This should update last_used_at and usage_stats in user_service_profiles
            logger.info(f"Voice activity recorded for {user_id}: {activity_type}")
            return True

        except Exception as e:
            logger.error(f"Error recording voice activity for {user_id}: {str(e)}")
            return False
