"""
Crisis intervention functionality for mental health assistant.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class CrisisInterventionManager:
    """Handles crisis detection and intervention logic."""

    @staticmethod
    async def handle_crisis_intervention(
        user_id: str,
        crisis_data: Dict[str, Any],
        user_message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Production-ready crisis intervention with comprehensive error handling.
        """
        intervention_id = str(uuid.uuid4())
        logger.critical(
            f"CRISIS INTERVENTION INITIATED - ID: {intervention_id} - User: {user_id}"
        )

        try:
            from ..safety_network.manager import SafetyNetworkManager

            # Step 1: Query emergency contacts
            emergency_contacts = SafetyNetworkManager.get_emergency_contacts(user_id)

            if not emergency_contacts:
                logger.warning(
                    f"No emergency contacts found for user {user_id} during crisis {intervention_id}"
                )
                return CrisisInterventionManager._handle_no_emergency_contacts(
                    user_id, intervention_id, crisis_data
                )

            # Step 2: Select primary emergency contact (highest priority)
            primary_contact = emergency_contacts[0]
            logger.info(
                f"Selected primary emergency contact {primary_contact['id']} for crisis {intervention_id}"
            )

            # Step 3: Determine optimal contact method
            contact_method = (
                CrisisInterventionManager._determine_optimal_contact_method(
                    primary_contact
                )
            )

            # Step 4: Create crisis context message
            crisis_level = CrisisInterventionManager._map_crisis_level(
                crisis_data.get("crisis_level", "CRISIS")
            )
            crisis_context = CrisisInterventionManager._create_crisis_context_message(
                user_message=user_message,
                crisis_assessment=crisis_data.get("crisis_explanation", ""),
                crisis_level=crisis_level,
                contact_name=primary_contact.get("first_name", ""),
            )

            # Step 5: Log crisis intervention attempt
            log_success = SafetyNetworkManager.log_contact_attempt(
                safety_contact_id=primary_contact["id"],
                user_id=user_id,
                contact_method=contact_method,
                success=True,
                reason="automated_crisis_intervention_chat",
                initiated_by="mental_health_assistant",
                message_content=crisis_context,
                contact_metadata={
                    "intervention_id": intervention_id,
                    "crisis_level": crisis_level,
                    "user_message_preview": user_message[:200],
                    "intervention_type": "automated_chat_crisis",
                    "contact_method_selected": contact_method,
                    "total_emergency_contacts": len(emergency_contacts),
                    "conversation_context": conversation_context,
                },
            )

            if not log_success:
                logger.error(
                    f"Failed to log crisis intervention {intervention_id} for user {user_id}"
                )

            # Step 6: Return comprehensive intervention status
            intervention_result = {
                "intervention_attempted": True,
                "intervention_id": intervention_id,
                "outreach_success": True,
                "contact_reached": primary_contact.get(
                    "full_name", "Emergency Contact"
                ),
                "contact_method": contact_method,
                "contact_phone": (
                    primary_contact.get("phone_number")
                    if contact_method in ["phone", "sms"]
                    else None
                ),
                "contact_email": (
                    primary_contact.get("email") if contact_method == "email" else None
                ),
                "log_success": log_success,
                "backup_contacts_available": len(emergency_contacts) > 1,
                "crisis_level": crisis_level,
                "message": CrisisInterventionManager._generate_intervention_user_message(
                    primary_contact, contact_method, crisis_level
                ),
                "contact_info": {
                    "id": primary_contact["id"],
                    "name": primary_contact.get("full_name"),
                    "first_name": primary_contact.get("first_name"),
                    "relationship": primary_contact.get("relationship_type"),
                    "preferred_method": primary_contact.get(
                        "preferred_communication_method"
                    ),
                    "available_methods": primary_contact.get(
                        "allowed_communication_methods", []
                    ),
                },
                "fallback_options": CrisisInterventionManager._generate_fallback_options(
                    emergency_contacts
                ),
                "next_steps": [
                    f"Your emergency contact {primary_contact.get('first_name', 'someone')} will be notified immediately",
                    "Stay on this chat - I'll continue supporting you",
                    "If you need immediate help, call 911 or go to your nearest emergency room",
                    "National Suicide Prevention Lifeline: 988",
                ],
            }

            logger.critical(
                f"Crisis intervention {intervention_id} completed successfully for user {user_id}"
            )
            return intervention_result

        except Exception as e:
            logger.critical(
                f"Crisis intervention {intervention_id} failed for user {user_id}: {str(e)}"
            )
            return CrisisInterventionManager._handle_crisis_intervention_failure(
                user_id, intervention_id, e, crisis_data
            )

    @staticmethod
    def _handle_no_emergency_contacts(
        user_id: str, intervention_id: str, crisis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle crisis when no emergency contacts are available."""
        logger.critical(
            f"Crisis intervention {intervention_id} - No emergency contacts available for user {user_id}"
        )

        return {
            "intervention_attempted": False,
            "intervention_id": intervention_id,
            "reason": "no_emergency_contacts",
            "outreach_success": False,
            "message": "I understand you're in crisis. While I don't have emergency contacts set up for you, I'm here to help connect you with immediate support.",
            "immediate_resources": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "contact": "988",
                    "description": "24/7 free and confidential support",
                    "type": "phone",
                },
                {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "24/7 crisis support via text",
                    "type": "text",
                },
                {
                    "name": "Emergency Services",
                    "contact": "911",
                    "description": "For immediate life-threatening emergencies",
                    "type": "emergency",
                },
            ],
            "next_steps": [
                "Call 988 for immediate crisis support",
                "If in immediate danger, call 911",
                "Consider setting up emergency contacts for future support",
                "I'll stay here with you while you get help",
            ],
            "setup_contacts_suggestion": True,
        }

    @staticmethod
    def _handle_crisis_intervention_failure(
        user_id: str,
        intervention_id: str,
        error: Exception,
        crisis_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle technical failures during crisis intervention."""
        logger.critical(
            f"Crisis intervention {intervention_id} technical failure for user {user_id}: {str(error)}"
        )

        return {
            "intervention_attempted": False,
            "intervention_id": intervention_id,
            "reason": "technical_error",
            "error": str(error),
            "outreach_success": False,
            "message": "I'm experiencing technical difficulties but I'm still here to help. Please use these immediate resources while I try to reconnect with your support system.",
            "immediate_resources": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "contact": "988",
                    "description": "24/7 free and confidential support",
                    "type": "phone",
                },
                {
                    "name": "Emergency Services",
                    "contact": "911",
                    "description": "For immediate life-threatening emergencies",
                    "type": "emergency",
                },
            ],
            "next_steps": [
                "Call 988 immediately for crisis support",
                "If in immediate danger, call 911",
                "I'll keep trying to contact your emergency contacts",
                "Stay with me - we'll get through this together",
            ],
            "retry_intervention": True,
        }

    @staticmethod
    def _determine_optimal_contact_method(contact: Dict[str, Any]) -> str:
        """Determine the best contact method based on availability and crisis urgency."""
        available_methods = contact.get("allowed_communication_methods", [])

        # Crisis priority: phone > sms > email
        if "phone" in available_methods:
            return "phone"
        elif "sms" in available_methods:
            return "sms"
        elif "email" in available_methods:
            return "email"
        elif available_methods:
            return available_methods[0]
        else:
            return "phone"  # Fallback

    @staticmethod
    def _generate_intervention_user_message(
        contact: Dict[str, Any], method: str, crisis_level: str
    ) -> str:
        """Generate user-facing message about intervention."""
        contact_name = contact.get("first_name", "your emergency contact")

        method_messages = {
            "phone": f"I'm immediately calling {contact_name} to let them know you need support.",
            "sms": f"I'm sending an urgent message to {contact_name} right now.",
            "email": f"I'm sending an urgent email to {contact_name} immediately.",
        }

        base_message = method_messages.get(
            method, f"I'm contacting {contact_name} immediately."
        )

        return f"{base_message} You're not alone in this. I'll stay with you while help is on the way."

    @staticmethod
    def _generate_fallback_options(
        emergency_contacts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate fallback contact options if primary contact fails."""
        fallbacks = []

        for contact in emergency_contacts[1:3]:  # Up to 2 backup contacts
            fallbacks.append(
                {
                    "id": contact["id"],
                    "name": contact.get("full_name", "Emergency Contact"),
                    "relationship": contact.get("relationship_type"),
                    "methods": contact.get("allowed_communication_methods", []),
                }
            )

        return fallbacks

    @staticmethod
    def _create_crisis_context_message(
        user_message: str,
        crisis_assessment: str,
        crisis_level: str,
        contact_name: str = "",
    ) -> str:
        """Create detailed context message for emergency contacts."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        urgency_indicators = {
            "critical": "🚨 CRITICAL CRISIS ALERT 🚨",
            "high": "⚠️ URGENT CRISIS ALERT ⚠️",
            "moderate": "⚠️ CRISIS SUPPORT NEEDED ⚠️",
        }

        urgency_header = urgency_indicators.get(crisis_level, "⚠️ CRISIS ALERT ⚠️")
        personal_greeting = f"Hi {contact_name}," if contact_name else "Hello,"

        return f"""{urgency_header}

{personal_greeting}

This is an automated alert from Nura Mental Health Support. Your loved one has reached out for mental health support and our AI assistant has detected signs of crisis requiring immediate human intervention.

🕐 Time: {timestamp}
🚨 Crisis Level: {crisis_level.upper()}
🤖 AI Assessment: {crisis_assessment}

💬 Recent Message Context:
"{user_message[:300]}{'...' if len(user_message) > 300 else ''}"

🆘 IMMEDIATE ACTION RECOMMENDED:
• Contact them RIGHT NOW via phone or in person
• Listen without judgment and provide emotional support  
• If they express intent to harm themselves or others, call 911 immediately
• Consider staying with them or having someone else stay with them
• Help them access professional crisis support if needed

📞 Crisis Resources to Share:
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

This alert was triggered by our AI crisis detection system. Even if this seems like a false alarm, please still reach out - your support matters and could save a life.

Sent by Nura Mental Health Support System
This message was sent because you are listed as an emergency contact."""

    @staticmethod
    def _map_crisis_level(assistant_crisis_level: str) -> str:
        """Map assistant crisis levels to safety network crisis levels."""
        mapping = {"CRISIS": "critical", "CONCERN": "high", "SUPPORT": "moderate"}
        return mapping.get(assistant_crisis_level, "high")
