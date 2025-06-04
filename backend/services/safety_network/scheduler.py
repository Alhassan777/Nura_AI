"""
Safety Checkup Scheduler - Bridge between Safety Network and Voice Scheduling.

This service connects safety network contacts with the voice scheduling system
to enable recurring checkups via calls, SMS, or email with safety contacts.

Works with both:
- Chat assistant (mental_health_assistant.py)
- Voice assistant (Vapi tools)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

# Import existing services
from .manager import SafetyNetworkManager
from models import CommunicationMethod, VoiceSchedule
from ..voice.database import get_db as get_voice_db
from ..voice.queue_worker import voice_queue

logger = logging.getLogger(__name__)


class CheckupType(Enum):
    """Types of safety checkups."""

    WELLNESS_CHECK = "wellness_check"
    CRISIS_FOLLOWUP = "crisis_followup"
    ROUTINE_CHECKIN = "routine_checkin"
    THERAPY_REMINDER = "therapy_reminder"


class CheckupMethod(Enum):
    """Methods for conducting checkups."""

    VOICE_CALL = "voice_call"  # Call the safety contact
    SMS_MESSAGE = "sms_message"  # SMS to safety contact
    EMAIL_MESSAGE = "email_message"  # Email to safety contact
    USER_REMINDER = "user_reminder"  # Remind user to contact them


class SafetyCheckupScheduler:
    """Manages recurring checkups with safety network contacts."""

    def __init__(self):
        self.safety_manager = SafetyNetworkManager()

    async def schedule_safety_checkup(
        self,
        user_id: str,
        contact_id: str,
        checkup_type: CheckupType,
        method: CheckupMethod,
        frequency: str,  # "daily", "weekly", "monthly"
        time_of_day: str = "afternoon",  # "morning", "afternoon", "evening"
        days_of_week: Optional[List[str]] = None,  # ["monday", "friday"]
        custom_message: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """
        Schedule recurring checkups with a safety contact.

        Args:
            user_id: User who owns the safety network
            contact_id: Safety contact to check in with
            checkup_type: Type of checkup (wellness, crisis followup, etc.)
            method: How to conduct checkup (call, SMS, email, remind user)
            frequency: How often (daily, weekly, monthly)
            time_of_day: When during day (morning, afternoon, evening)
            days_of_week: Which days (for weekly/monthly)
            custom_message: Custom message template
            timezone: User's timezone

        Returns:
            Dict with schedule info or error
        """
        try:
            # 1. Validate safety contact exists and is active
            contacts = self.safety_manager.get_user_safety_contacts(
                user_id=user_id, active_only=True
            )

            contact = next((c for c in contacts if c["id"] == contact_id), None)
            if not contact:
                return {
                    "success": False,
                    "error": "Safety contact not found or inactive",
                }

            # 2. Validate contact supports the chosen method
            allowed_methods = contact["allowed_communication_methods"]
            method_mapping = {
                CheckupMethod.VOICE_CALL: "phone",
                CheckupMethod.SMS_MESSAGE: "sms",
                CheckupMethod.EMAIL_MESSAGE: "email",
                CheckupMethod.USER_REMINDER: "any",  # Doesn't need contact method
            }

            required_method = method_mapping[method]
            if required_method != "any" and required_method not in allowed_methods:
                return {
                    "success": False,
                    "error": f"Contact doesn't support {required_method} communication",
                }

            # 3. Generate cron expression
            cron_expression = self._generate_checkup_cron(
                frequency, time_of_day, days_of_week
            )

            # 4. Create schedule name and description
            schedule_name = f"{checkup_type.value.replace('_', ' ').title()} - {contact['first_name']}"
            description = self._generate_checkup_description(
                checkup_type, contact, method, frequency
            )

            # 5. Create voice schedule with safety checkup metadata
            schedule_metadata = {
                "checkup_type": "safety_checkup",
                "safety_contact_id": contact_id,
                "checkup_method": method.value,
                "checkup_category": checkup_type.value,
                "contact_name": contact["full_name"],
                "contact_relationship": contact["relationship_type"],
                "custom_message": custom_message,
                "created_by": "safety_scheduler",
                "user_initiated": True,
            }

            # 6. Use voice scheduling infrastructure
            with get_voice_db() as db:
                from croniter import croniter

                # Calculate next run time
                cron = croniter(cron_expression, datetime.utcnow())
                next_run = cron.get_next(datetime)

                # Create schedule in voice service
                voice_schedule = VoiceSchedule(
                    user_id=user_id,
                    assistant_id="safety_checkup_assistant",  # Special assistant for checkups
                    name=schedule_name,
                    cron_expression=cron_expression,
                    timezone=timezone,
                    next_run_at=next_run,
                    custom_metadata=schedule_metadata,
                )

                db.add(voice_schedule)
                db.flush()

                logger.info(
                    f"Created safety checkup schedule {voice_schedule.id} for user {user_id}"
                )

                return {
                    "success": True,
                    "schedule_id": voice_schedule.id,
                    "schedule_name": schedule_name,
                    "description": description,
                    "next_checkup": next_run.isoformat(),
                    "frequency": frequency,
                    "contact": {
                        "name": contact["full_name"],
                        "relationship": contact["relationship_type"],
                    },
                    "method": method.value,
                }

        except Exception as e:
            logger.error(f"Error scheduling safety checkup: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_safety_schedules(
        self, user_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all safety checkup schedules for a user."""
        try:
            with get_voice_db() as db:
                query = db.query(VoiceSchedule).filter(
                    VoiceSchedule.user_id == user_id,
                    VoiceSchedule.custom_metadata["checkup_type"].astext
                    == "safety_checkup",
                )

                if active_only:
                    query = query.filter(VoiceSchedule.is_active == True)

                schedules = query.order_by(VoiceSchedule.next_run_at.asc()).all()

                # Enrich with contact data
                result = []
                for schedule in schedules:
                    metadata = schedule.custom_metadata or {}
                    contact_id = metadata.get("safety_contact_id")

                    # Get current contact info
                    contacts = self.safety_manager.get_user_safety_contacts(user_id)
                    contact = next((c for c in contacts if c["id"] == contact_id), None)

                    schedule_info = {
                        "id": schedule.id,
                        "name": schedule.name,
                        "checkup_type": metadata.get("checkup_category"),
                        "method": metadata.get("checkup_method"),
                        "frequency": self._extract_frequency_from_cron(
                            schedule.cron_expression
                        ),
                        "next_run": schedule.next_run_at.isoformat(),
                        "last_run": (
                            schedule.last_run_at.isoformat()
                            if schedule.last_run_at
                            else None
                        ),
                        "is_active": schedule.is_active,
                        "contact": (
                            {
                                "id": contact_id,
                                "name": (
                                    contact["full_name"]
                                    if contact
                                    else "Unknown Contact"
                                ),
                                "relationship": (
                                    contact["relationship_type"] if contact else None
                                ),
                                "active": contact["is_active"] if contact else False,
                            }
                            if contact_id
                            else None
                        ),
                        "timezone": schedule.timezone,
                    }
                    result.append(schedule_info)

                return result

        except Exception as e:
            logger.error(f"Error getting safety schedules for user {user_id}: {e}")
            return []

    async def cancel_safety_checkup(
        self, user_id: str, schedule_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a safety checkup schedule."""
        try:
            with get_voice_db() as db:
                schedule = (
                    db.query(VoiceSchedule)
                    .filter(
                        VoiceSchedule.id == schedule_id,
                        VoiceSchedule.user_id == user_id,
                        VoiceSchedule.custom_metadata["checkup_type"].astext
                        == "safety_checkup",
                    )
                    .first()
                )

                if not schedule:
                    return {
                        "success": False,
                        "error": "Safety checkup schedule not found",
                    }

                # Deactivate instead of delete to preserve history
                schedule.is_active = False
                schedule.updated_at = datetime.utcnow()

                # Add cancellation reason to metadata
                if schedule.custom_metadata:
                    schedule.custom_metadata["cancelled_at"] = (
                        datetime.utcnow().isoformat()
                    )
                    schedule.custom_metadata["cancellation_reason"] = reason

                logger.info(f"Cancelled safety checkup schedule {schedule_id}")

                return {
                    "success": True,
                    "message": f"Cancelled checkup schedule: {schedule.name}",
                    "cancelled_schedule": {"id": schedule_id, "name": schedule.name},
                }

        except Exception as e:
            logger.error(f"Error cancelling safety checkup {schedule_id}: {e}")
            return {"success": False, "error": str(e)}

    def _generate_checkup_cron(
        self, frequency: str, time_of_day: str, days_of_week: Optional[List[str]] = None
    ) -> str:
        """Generate cron expression for checkup schedule."""
        # Map time preferences to hours
        time_map = {
            "morning": "9",  # 9 AM
            "afternoon": "14",  # 2 PM
            "evening": "18",  # 6 PM
        }

        # Map day names to cron values
        day_map = {
            "monday": "1",
            "tuesday": "2",
            "wednesday": "3",
            "thursday": "4",
            "friday": "5",
            "saturday": "6",
            "sunday": "0",
        }

        hour = time_map.get(time_of_day, "14")

        if frequency == "daily":
            return f"0 {hour} * * *"

        elif frequency == "weekly":
            day = day_map.get(days_of_week[0] if days_of_week else "monday", "1")
            return f"0 {hour} * * {day}"

        elif frequency == "biweekly":
            day = day_map.get(days_of_week[0] if days_of_week else "monday", "1")
            return f"0 {hour} * * {day}/2"

        elif frequency == "monthly":
            day = day_map.get(days_of_week[0] if days_of_week else "monday", "1")
            return f"0 {hour} 1-7 * {day}"  # First occurrence of day in month

        # Default to weekly Monday afternoon
        return f"0 {hour} * * 1"

    def _generate_checkup_description(
        self,
        checkup_type: CheckupType,
        contact: Dict,
        method: CheckupMethod,
        frequency: str,
    ) -> str:
        """Generate human-readable description of the checkup schedule."""
        method_desc = {
            CheckupMethod.VOICE_CALL: f"call {contact['first_name']}",
            CheckupMethod.SMS_MESSAGE: f"send SMS to {contact['first_name']}",
            CheckupMethod.EMAIL_MESSAGE: f"send email to {contact['first_name']}",
            CheckupMethod.USER_REMINDER: f"remind you to contact {contact['first_name']}",
        }

        type_desc = {
            CheckupType.WELLNESS_CHECK: "wellness check",
            CheckupType.CRISIS_FOLLOWUP: "crisis follow-up",
            CheckupType.ROUTINE_CHECKIN: "routine check-in",
            CheckupType.THERAPY_REMINDER: "therapy reminder",
        }

        return f"{frequency.title()} {type_desc[checkup_type]} - {method_desc[method]}"

    def _extract_frequency_from_cron(self, cron_expression: str) -> str:
        """Extract human-readable frequency from cron expression."""
        parts = cron_expression.split()
        if len(parts) != 5:
            return "custom"

        minute, hour, day, month, weekday = parts

        if day == "*" and month == "*" and weekday == "*":
            return "daily"
        elif day == "*" and month == "*" and "/" in weekday:
            return "biweekly"
        elif day == "*" and month == "*":
            return "weekly"
        elif weekday != "*" and "-" in day:
            return "monthly"
        else:
            return "custom"


# Global instance
safety_scheduler = SafetyCheckupScheduler()
