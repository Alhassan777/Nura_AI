"""
Integration layer between Vapi tools and our scheduling service.
Handles the actual API calls when Vapi tools are triggered.
"""

import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

from models import ScheduleType, ReminderMethod
from .config import config

logger = logging.getLogger(__name__)


def generate_cron_from_preferences(time_of_day: str, days: list, frequency: str) -> str:
    """
    Generate cron expression from user preferences.
    Moved here from old vapi_tools module.
    """
    # Time mapping
    time_map = {
        "morning": "0 9",  # 9 AM
        "afternoon": "0 14",  # 2 PM
        "evening": "0 18",  # 6 PM
        "flexible": "0 14",  # Default to 2 PM
    }

    # Day mapping
    day_map = {
        "monday": "1",
        "tuesday": "2",
        "wednesday": "3",
        "thursday": "4",
        "friday": "5",
        "saturday": "6",
        "sunday": "0",
    }

    time_part = time_map.get(time_of_day, "0 14")

    if frequency == "daily":
        return f"{time_part} * * *"
    elif frequency == "weekly":
        day = day_map.get(days[0].lower() if days else "monday", "1")
        return f"{time_part} * * {day}"
    elif frequency == "biweekly":
        day = day_map.get(days[0].lower() if days else "monday", "1")
        return f"{time_part} * * {day}/2"
    elif frequency == "monthly":
        day = day_map.get(days[0].lower() if days else "monday", "1")
        return f"{time_part} 1-7 * {day}"
    else:
        # Default weekly
        return f"{time_part} * * 1"


class SchedulingIntegration:
    """Handles integration between Vapi voice assistant and scheduling service."""

    def __init__(self, scheduling_api_base: Optional[str] = None):
        # Use config endpoint or override
        self.api_base = scheduling_api_base or config.get_api_endpoint("scheduling")
        self.headers = {"Content-Type": "application/json"}
        self.timeout = config.WEBHOOK_TIMEOUT

    async def handle_create_schedule(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_schedule_appointment tool call from Vapi."""
        try:
            # Extract user ID from call context
            user_id = call_data.get("user", {}).get("id", "anonymous")

            # Extract parameters from the tool call
            params = call_data.get("toolCallParams", {})

            # Prepare request for our scheduling API
            schedule_request = {
                "name": params.get("name"),
                "description": params.get("description"),
                "schedule_type": params.get("schedule_type", "voice_checkup"),
                "cron_expression": params.get("cron_expression"),
                "timezone": params.get("timezone", "UTC"),
                "reminder_method": params.get("reminder_method"),
                "phone_number": params.get("phone_number"),
                "email": params.get("email"),
                "context_summary": params.get("context_summary"),
                "custom_metadata": {
                    "created_via": "voice_assistant",
                    "call_id": call_data.get("call", {}).get("id"),
                    "assistant_id": call_data.get("assistant", {}).get("id"),
                },
            }

            # Make API call to our scheduling service
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                url = f"{self.api_base}/schedules"
                async with session.post(
                    url,
                    json=schedule_request,
                    params={"user_id": user_id},
                    headers=self.headers,
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"Created schedule {result.get('schedule_id')} for user {user_id}"
                        )

                        return {
                            "success": True,
                            "message": f"I've scheduled your {schedule_request['name']} checkup! You'll receive a {schedule_request['reminder_method']} reminder when it's time.",
                            "schedule_id": result.get("schedule_id"),
                            "next_checkup": "Based on your schedule, I'll check in with you as planned.",
                        }
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to create schedule: {response.status} - {error_text}"
                        )
                        return {
                            "success": False,
                            "message": "I had trouble setting up your schedule. Let me try again or we can set this up manually.",
                            "error": error_text,
                        }

        except Exception as e:
            logger.error(f"Error in handle_create_schedule: {e}")
            return {
                "success": False,
                "message": "I'm having technical difficulties setting up your schedule right now. Please try again in a moment.",
                "error": str(e),
            }

    async def handle_list_schedules(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_user_schedules tool call from Vapi."""
        try:
            user_id = call_data.get("user", {}).get("id", "anonymous")
            params = call_data.get("toolCallParams", {})
            active_only = params.get("active_only", True)

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/schedules"
                async with session.get(
                    url,
                    params={
                        "user_id": user_id,
                        "active_only": str(active_only).lower(),
                    },
                    headers=self.headers,
                ) as response:

                    if response.status == 200:
                        schedules = await response.json()

                        if not schedules:
                            return {
                                "success": True,
                                "message": "You don't have any scheduled checkups right now. Would you like me to set one up for you?",
                                "schedules": [],
                            }

                        # Format schedules for voice response
                        schedule_list = []
                        for schedule in schedules:
                            schedule_list.append(
                                {
                                    "id": schedule["id"],
                                    "name": schedule["name"],
                                    "type": schedule["schedule_type"],
                                    "next_run": schedule["next_run_at"],
                                    "reminder_method": schedule["reminder_method"],
                                }
                            )

                        message = f"You have {len(schedules)} scheduled checkup"
                        if len(schedules) > 1:
                            message += "s"
                        message += ". " + ", ".join([s["name"] for s in schedules])

                        return {
                            "success": True,
                            "message": message,
                            "schedules": schedule_list,
                        }
                    else:
                        return {
                            "success": False,
                            "message": "I'm having trouble accessing your schedule information right now.",
                            "schedules": [],
                        }

        except Exception as e:
            logger.error(f"Error in handle_list_schedules: {e}")
            return {
                "success": False,
                "message": "I can't access your schedules at the moment. Please try again.",
                "error": str(e),
            }

    async def handle_delete_schedule(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_schedule_appointment tool call from Vapi."""
        try:
            user_id = call_data.get("user", {}).get("id", "anonymous")
            params = call_data.get("toolCallParams", {})
            schedule_id = params.get("schedule_id")

            if not schedule_id:
                return {
                    "success": False,
                    "message": "I need to know which schedule to cancel. Can you tell me the name of the checkup you want to cancel?",
                }

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/schedules/{schedule_id}"
                async with session.delete(
                    url, params={"user_id": user_id}, headers=self.headers
                ) as response:

                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "I've cancelled that scheduled checkup for you. You won't receive any more reminders for it.",
                        }
                    elif response.status == 404:
                        return {
                            "success": False,
                            "message": "I couldn't find that scheduled checkup. It might have already been cancelled.",
                        }
                    else:
                        return {
                            "success": False,
                            "message": "I had trouble cancelling that schedule. Please try again.",
                        }

        except Exception as e:
            logger.error(f"Error in handle_delete_schedule: {e}")
            return {
                "success": False,
                "message": "I'm having technical difficulties cancelling your schedule right now.",
                "error": str(e),
            }

    async def handle_check_availability(
        self, call_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle check_user_availability tool call from Vapi."""
        try:
            params = call_data.get("toolCallParams", {})

            # Generate cron expression from preferences
            time_of_day = params.get("preferred_time_of_day", "afternoon")
            days = params.get("preferred_days", ["monday"])
            frequency = params.get("frequency", "weekly")
            timezone = params.get("timezone", "UTC")

            cron_expression = generate_cron_from_preferences(
                time_of_day, days, frequency
            )

            # Generate human-readable schedule description
            time_desc = {
                "morning": "in the morning (around 9 AM)",
                "afternoon": "in the afternoon (around 2 PM)",
                "evening": "in the evening (around 6 PM)",
            }.get(time_of_day, "in the afternoon")

            frequency_desc = {
                "daily": "every day",
                "weekly": f"every {days[0] if days else 'Monday'}",
                "biweekly": f"every other {days[0] if days else 'Monday'}",
                "monthly": f"once a month on {days[0] if days else 'Monday'}s",
            }.get(frequency, "weekly")

            message = f"Based on your preferences, I can schedule checkups {frequency_desc} {time_desc}."

            return {
                "success": True,
                "message": message,
                "recommended_schedule": {
                    "cron_expression": cron_expression,
                    "description": f"{frequency_desc.title()} {time_desc}",
                    "timezone": timezone,
                },
            }

        except Exception as e:
            logger.error(f"Error in handle_check_availability: {e}")
            return {
                "success": False,
                "message": "I'm having trouble processing your availability preferences right now.",
                "error": str(e),
            }


# Webhook handler for Vapi tool calls
async def handle_vapi_tool_call(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main webhook handler for Vapi tool calls."""
    integration = SchedulingIntegration()

    tool_name = (
        webhook_data.get("message", {})
        .get("toolCalls", [{}])[0]
        .get("function", {})
        .get("name")
    )

    if not tool_name:
        return {"error": "No tool name found in webhook data"}

    # Route to appropriate handler
    handlers = {
        "create_schedule_appointment": integration.handle_create_schedule,
        "list_user_schedules": integration.handle_list_schedules,
        "delete_schedule_appointment": integration.handle_delete_schedule,
        "update_schedule_appointment": integration.handle_create_schedule,  # Similar to create
        "check_user_availability": integration.handle_check_availability,
    }

    handler = handlers.get(tool_name)
    if handler:
        return await handler(webhook_data)
    else:
        return {
            "success": False,
            "message": f"Unknown tool: {tool_name}",
            "error": "Tool not found",
        }
