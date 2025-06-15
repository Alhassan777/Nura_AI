"""
Safety Network Invitation Management System.

Handles the complete lifecycle of safety network invitations with full user autonomy
over permissions. No pre-assumptions based on relationship types.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os
from sqlalchemy import and_, or_

from .database import get_db, get_db_context_local
from .search import UserSearch
from models import (
    SafetyNetworkRequest,
    SafetyNetworkResponse,
    SafetyNetworkRequestStatus,
    SafetyContact,
    User,
    UserBlock,
    SafetyPermissionChange,
)

# Import safety network manager
from services.safety_network.manager import SafetyNetworkManager

logger = logging.getLogger(__name__)


class SafetyInvitationManager:
    """Manages safety network invitations with full user control over permissions."""

    # Available permission categories for users to choose from
    AVAILABLE_PERMISSIONS = {
        "location_access": {
            "key": "can_see_location",
            "name": "Location Access",
            "description": "Can see your location during crisis situations for emergency response",
            "privacy_level": "high",
            "category": "emergency",
        },
        "mood_tracking": {
            "key": "can_see_mood",
            "name": "Mood Tracking",
            "description": "Can see your daily mood entries and emotional patterns",
            "privacy_level": "medium",
            "category": "wellness",
        },
        "activity_tracking": {
            "key": "can_see_activities",
            "name": "Activity Tracking",
            "description": "Can see your daily activities and behavioral patterns",
            "privacy_level": "medium",
            "category": "wellness",
        },
        "goals_progress": {
            "key": "can_see_goals",
            "name": "Goals & Progress",
            "description": "Can see your mental health goals and progress tracking",
            "privacy_level": "low",
            "category": "wellness",
        },
        "status_updates": {
            "key": "can_see_status",
            "name": "Status Updates",
            "description": "Can see your general wellness status and check-ins",
            "privacy_level": "low",
            "category": "wellness",
        },
        "crisis_alerts": {
            "key": "crisis_alerts",
            "name": "Crisis Alerts",
            "description": "Gets notified immediately during mental health crises or emergencies",
            "privacy_level": "high",
            "category": "alerts",
        },
        "wellness_alerts": {
            "key": "wellness_check_alerts",
            "name": "Wellness Check Alerts",
            "description": "Gets notified for regular wellness check-ins and concerning patterns",
            "privacy_level": "medium",
            "category": "alerts",
        },
        "mood_concern_alerts": {
            "key": "mood_concerns",
            "name": "Mood Concern Alerts",
            "description": "Gets notified when your mood shows concerning patterns",
            "privacy_level": "medium",
            "category": "alerts",
        },
        "goal_reminders": {
            "key": "goal_reminders",
            "name": "Goal Reminder Alerts",
            "description": "Gets notified to help remind you about your mental health goals",
            "privacy_level": "low",
            "category": "alerts",
        },
    }

    # Relationship types - purely descriptive, no permission restrictions
    RELATIONSHIP_TYPES = [
        {
            "value": "family",
            "label": "Family Member",
            "description": "Parent, sibling, child, or other family member",
            "suggested_permissions": [
                "crisis_alerts",
                "wellness_alerts",
                "mood_tracking",
            ],
        },
        {
            "value": "partner",
            "label": "Partner/Spouse",
            "description": "Romantic partner, spouse, or life partner",
            "suggested_permissions": [
                "crisis_alerts",
                "wellness_alerts",
                "mood_tracking",
                "activity_tracking",
            ],
        },
        {
            "value": "friend",
            "label": "Close Friend",
            "description": "Close personal friend you trust with your wellness",
            "suggested_permissions": [
                "wellness_alerts",
                "mood_tracking",
                "status_updates",
            ],
        },
        {
            "value": "therapist",
            "label": "Therapist",
            "description": "Licensed therapist, counselor, or mental health professional",
            "suggested_permissions": [
                "mood_tracking",
                "goals_progress",
                "status_updates",
            ],
        },
        {
            "value": "counselor",
            "label": "Counselor",
            "description": "Guidance counselor, peer counselor, or support professional",
            "suggested_permissions": [
                "mood_tracking",
                "wellness_alerts",
                "status_updates",
            ],
        },
        {
            "value": "colleague",
            "label": "Colleague",
            "description": "Work colleague or professional contact",
            "suggested_permissions": ["status_updates"],
        },
        {
            "value": "neighbor",
            "label": "Neighbor",
            "description": "Neighbor or nearby contact for emergencies",
            "suggested_permissions": ["crisis_alerts", "location_access"],
        },
        {
            "value": "other",
            "label": "Other",
            "description": "Other type of supportive relationship",
            "suggested_permissions": ["status_updates"],
        },
    ]

    @staticmethod
    def send_invitation(
        requester_id: str,
        recipient_email: str,
        relationship_type: str,
        requested_permissions: Dict[str, Any],
        invitation_message: str = "",
        priority_order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a safety network invitation with improved error handling.

        Returns user-friendly error messages for common scenarios.
        """
        try:
            with get_db_context_local() as db:
                # 1. Find recipient by email
                recipient = db.query(User).filter(User.email == recipient_email).first()

                if not recipient:
                    return {
                        "success": False,
                        "error": "USER_NOT_FOUND",
                        "message": f"No user found with email {recipient_email}. They may need to create a Nura account first.",
                        "user_friendly": True,
                    }

                recipient_id = str(recipient.id)

                # Prevent self-invitation
                if requester_id == recipient_id:
                    return {
                        "success": False,
                        "error": "SELF_INVITATION",
                        "message": "You cannot send a safety network invitation to yourself.",
                        "user_friendly": True,
                    }

                # 2. Check for existing relationships - provide specific error messages
                # Check for pending invitation
                existing_pending = (
                    db.query(SafetyNetworkRequest)
                    .filter(
                        and_(
                            SafetyNetworkRequest.requester_id == requester_id,
                            SafetyNetworkRequest.requested_id == recipient_id,
                            SafetyNetworkRequest.status == "pending",
                        )
                    )
                    .first()
                )

                if existing_pending:
                    days_ago = (datetime.utcnow() - existing_pending.created_at).days
                    return {
                        "success": False,
                        "error": "PENDING_INVITATION_EXISTS",
                        "message": f"You already sent an invitation to {recipient.full_name or recipient_email} {days_ago} days ago. Please wait for them to respond before sending another invitation.",
                        "user_friendly": True,
                        "existing_invitation": {
                            "sent_date": existing_pending.created_at.isoformat(),
                            "expires_date": (
                                existing_pending.expires_at.isoformat()
                                if existing_pending.expires_at
                                else None
                            ),
                        },
                    }

                # Check for existing active safety contact
                existing_contact = (
                    db.query(SafetyContact)
                    .filter(
                        and_(
                            SafetyContact.user_id == requester_id,
                            SafetyContact.contact_user_id == recipient_id,
                            SafetyContact.is_active == True,
                        )
                    )
                    .first()
                )

                if existing_contact:
                    return {
                        "success": False,
                        "error": "ALREADY_IN_NETWORK",
                        "message": f"{recipient.full_name or recipient_email} is already in your safety network as a {existing_contact.relationship_type}. You can manage their permissions in your safety network settings.",
                        "user_friendly": True,
                        "existing_contact": {
                            "relationship_type": existing_contact.relationship_type,
                            "added_date": existing_contact.created_at.isoformat(),
                            "is_emergency_contact": existing_contact.is_emergency_contact,
                        },
                    }

                # 3. Check invitation eligibility (privacy settings, blocks, etc.)
                eligibility = UserSearch.check_invitation_eligibility(
                    requester_id, recipient_id, db
                )

                if not eligibility["can_invite"]:
                    # Map technical reasons to user-friendly messages
                    friendly_messages = {
                        "BLOCKED": f"{recipient.full_name or recipient_email} has blocked invitations from you.",
                        "NOT_ACCEPTING": f"{recipient.full_name or recipient_email} is not accepting safety network invitations at this time.",
                        "VERIFICATION_REQUIRED": "You need to verify your account before sending invitations. Please check your email for verification instructions.",
                        "NOT_DISCOVERABLE": f"{recipient.full_name or recipient_email} has limited their discoverability and cannot receive invitations.",
                        "NO_MUTUAL_CONNECTIONS": f"You need mutual connections to invite {recipient.full_name or recipient_email}. Try connecting through friends first.",
                    }

                    user_message = friendly_messages.get(
                        eligibility["reason_code"],
                        eligibility.get(
                            "user_message", "Unable to send invitation at this time."
                        ),
                    )

                    return {
                        "success": False,
                        "error": eligibility["reason_code"],
                        "message": user_message,
                        "user_friendly": True,
                    }

                # 4. Validate requested permissions
                validation_result = SafetyInvitationManager._validate_permissions(
                    requested_permissions
                )
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "INVALID_PERMISSIONS",
                        "message": "The permissions you selected are invalid. Please try again.",
                        "user_friendly": True,
                        "details": validation_result["message"],
                    }

                # 5. Create invitation request (clean, no legacy fields)
                request = SafetyNetworkRequest(
                    requester_id=requester_id,
                    requested_id=str(recipient.id),
                    relationship_type=relationship_type,
                    invitation_message=invitation_message,
                    requested_permissions=requested_permissions,
                    requested_priority_order=priority_order,
                    invitation_preview=SafetyInvitationManager._generate_invitation_preview(
                        requester_id,
                        recipient,
                        relationship_type,
                        requested_permissions,
                    ),
                    expires_at=datetime.utcnow() + timedelta(days=30),
                )

                db.add(request)
                db.commit()

                # 6. Generate user-friendly invitation summary
                permission_summary = (
                    SafetyInvitationManager._generate_permission_summary(
                        requested_permissions
                    )
                )

                return {
                    "success": True,
                    "invitation_id": request.id,
                    "status": "pending",
                    "recipient_name": recipient.full_name or recipient_email,
                    "expires_at": request.expires_at.isoformat(),
                    "permission_summary": permission_summary,
                    "relationship_type": relationship_type,
                    "message": f"Safety network invitation sent to {recipient.full_name or recipient_email}! They have 30 days to respond.",
                    "user_friendly": True,
                }

        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Unable to send invitation at this time. Please try again later.",
                "user_friendly": True,
                "technical_details": str(e),
            }

    @staticmethod
    def _validate_permissions(permissions: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that requested permissions are valid and properly formatted."""
        try:
            # Check if permissions object is properly structured
            if not isinstance(permissions, dict):
                return {"valid": False, "message": "Permissions must be a dictionary"}

            # Validate individual permissions
            valid_permission_keys = set()
            for perm_info in SafetyInvitationManager.AVAILABLE_PERMISSIONS.values():
                valid_permission_keys.add(perm_info["key"])

            # Check for invalid permission keys
            invalid_keys = (
                set(permissions.keys()) - valid_permission_keys - {"alert_preferences"}
            )
            if invalid_keys:
                return {
                    "valid": False,
                    "message": f"Invalid permission keys: {list(invalid_keys)}",
                }

            # Validate alert preferences if present
            if "alert_preferences" in permissions:
                alert_prefs = permissions["alert_preferences"]
                if not isinstance(alert_prefs, dict):
                    return {
                        "valid": False,
                        "message": "Alert preferences must be a dictionary",
                    }

            return {"valid": True, "message": "Permissions are valid"}

        except Exception as e:
            logger.error(f"Error validating permissions: {e}")
            return {"valid": False, "message": "Error validating permissions"}

    @staticmethod
    def _generate_permission_summary(permissions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a user-friendly summary of what's being shared."""
        summary = {
            "data_access": [],
            "alert_types": [],
            "privacy_level": "minimal",
            "total_permissions": 0,
        }

        # Count data access permissions
        data_permissions = [
            "can_see_location",
            "can_see_mood",
            "can_see_activities",
            "can_see_goals",
            "can_see_status",
        ]
        for perm_key in data_permissions:
            if permissions.get(perm_key, False):
                # Find the permission info
                for (
                    perm_name,
                    perm_info,
                ) in SafetyInvitationManager.AVAILABLE_PERMISSIONS.items():
                    if perm_info["key"] == perm_key:
                        summary["data_access"].append(
                            {
                                "name": perm_info["name"],
                                "description": perm_info["description"],
                            }
                        )
                        break

        # Count alert permissions
        alert_prefs = permissions.get("alert_preferences", {})
        for alert_key, alert_enabled in alert_prefs.items():
            if alert_enabled:
                # Find the alert info
                for (
                    perm_name,
                    perm_info,
                ) in SafetyInvitationManager.AVAILABLE_PERMISSIONS.items():
                    if perm_info["key"] == alert_key:
                        summary["alert_types"].append(
                            {
                                "name": perm_info["name"],
                                "description": perm_info["description"],
                            }
                        )
                        break

        # Calculate privacy level
        total_permissions = len(summary["data_access"]) + len(summary["alert_types"])
        summary["total_permissions"] = total_permissions

        if total_permissions == 0:
            summary["privacy_level"] = "none"
        elif total_permissions <= 2:
            summary["privacy_level"] = "minimal"
        elif total_permissions <= 4:
            summary["privacy_level"] = "moderate"
        else:
            summary["privacy_level"] = "comprehensive"

        return summary

    @staticmethod
    def accept_invitation(
        user_id: str,
        invitation_id: str,
        granted_permissions: Optional[Dict[str, Any]] = None,
        response_message: str = "",
        priority_order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Accept a safety network invitation.

        New approach: User can modify permissions when accepting.

        Args:
            user_id: User accepting the invitation
            invitation_id: Invitation being accepted
            granted_permissions: Permissions user is willing to grant (can be different from requested)
            response_message: Optional response message

        Returns:
            Dictionary with success status and safety contact details
        """
        try:
            with get_db_context_local() as db:
                # 1. Get invitation
                invitation = (
                    db.query(SafetyNetworkRequest)
                    .filter(
                        and_(
                            SafetyNetworkRequest.id == invitation_id,
                            SafetyNetworkRequest.requested_id == user_id,
                            SafetyNetworkRequest.status == "pending",
                        )
                    )
                    .first()
                )

                if not invitation:
                    return {
                        "success": False,
                        "error": "INVITATION_NOT_FOUND",
                        "message": "Invitation not found or already processed",
                    }

                # Store invitation data before deletion
                requester_id = invitation.requester_id
                relationship_type = invitation.relationship_type

                # 2. Use granted permissions or fall back to requested permissions
                final_permissions = (
                    granted_permissions or invitation.requested_permissions
                )

                # 3. Validate the final permissions
                validation_result = SafetyInvitationManager._validate_permissions(
                    final_permissions
                )
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "INVALID_PERMISSIONS",
                        "message": validation_result["message"],
                    }

                # 4. Determine priority order for the new contact
                # Use provided priority, or requested priority, or fall back to next available
                final_priority_order = (
                    priority_order
                    or invitation.requested_priority_order
                    or SafetyInvitationManager._get_next_priority_order(
                        requester_id, db
                    )
                )

                # 5. Create safety contact using SafetyNetworkManager
                logger.info(
                    f"Creating safety contact for invitation {invitation_id}: requester={requester_id}, contact={user_id}, relationship={relationship_type}"
                )

                safety_contact = SafetyNetworkManager.add_safety_contact(
                    user_id=requester_id,  # Requester gets the contact
                    contact_user_id=user_id,  # User being contacted
                    priority_order=final_priority_order,
                    relationship_type=relationship_type,
                    allowed_communication_methods=["phone", "email", "sms"],
                    preferred_communication_method="phone",
                    is_emergency_contact=False,  # User can set this later via separate action
                    custom_metadata={
                        "permissions": final_permissions,
                        "invitation_id": invitation_id,
                    },
                )

                if not safety_contact:
                    logger.error(
                        f"SafetyNetworkManager.add_safety_contact returned None for invitation {invitation_id}"
                    )
                    return {
                        "success": False,
                        "error": "CONTACT_CREATION_FAILED",
                        "message": "Failed to create safety contact",
                    }

                # 6. Create response record (temporary - will be deleted with invitation)
                response = SafetyNetworkResponse(
                    request_id=invitation_id,
                    response_type="accept",
                    response_message=response_message,
                    granted_permissions=final_permissions,
                )

                db.add(response)
                db.flush()  # Make sure response is saved before deletion

                # 7. DELETE the invitation and response records to allow future invitations
                # This is the key change - delete rather than just update status
                logger.info(
                    f"Deleting accepted invitation {invitation_id} to allow future re-invitations"
                )
                db.delete(response)
                db.delete(invitation)

                db.commit()

                # 8. Generate summary of what was shared
                permission_summary = (
                    SafetyInvitationManager._generate_permission_summary(
                        final_permissions
                    )
                )

                return {
                    "success": True,
                    "safety_contact_id": safety_contact,
                    "granted_permissions": final_permissions,
                    "permission_summary": permission_summary,
                    "status": "accepted",
                }

        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to accept invitation",
            }

    @staticmethod
    def get_available_permissions() -> Dict[str, Any]:
        """Get all available permissions that users can choose from."""
        return {
            "permissions": SafetyInvitationManager.AVAILABLE_PERMISSIONS,
            "categories": {
                "emergency": {
                    "name": "Emergency & Crisis",
                    "description": "Permissions related to emergency situations and crisis response",
                    "privacy_note": "High privacy impact - only share with trusted contacts",
                },
                "wellness": {
                    "name": "Wellness & Tracking",
                    "description": "Permissions related to ongoing wellness monitoring and support",
                    "privacy_note": "Medium privacy impact - sharing helps with ongoing support",
                },
                "alerts": {
                    "name": "Notifications & Alerts",
                    "description": "When and how contacts get notified about your wellness",
                    "privacy_note": "Choose based on how much you want this person involved",
                },
            },
        }

    @staticmethod
    def get_relationship_types() -> List[Dict[str, Any]]:
        """Get available relationship types with suggestions."""
        return SafetyInvitationManager.RELATIONSHIP_TYPES

    @staticmethod
    def decline_invitation(
        user_id: str, invitation_id: str, response_message: str = ""
    ) -> Dict[str, Any]:
        """Decline a safety network invitation."""
        try:
            with get_db_context_local() as db:
                invitation = (
                    db.query(SafetyNetworkRequest)
                    .filter(
                        and_(
                            SafetyNetworkRequest.id == invitation_id,
                            SafetyNetworkRequest.requested_id == user_id,
                            SafetyNetworkRequest.status == "pending",
                        )
                    )
                    .first()
                )

                if not invitation:
                    return {
                        "success": False,
                        "error": "INVITATION_NOT_FOUND",
                        "message": "Invitation not found or already processed",
                    }

                # Create response record (temporary - will be deleted with invitation)
                response = SafetyNetworkResponse(
                    request_id=invitation_id,
                    response_type="decline",
                    response_message=response_message,
                )

                db.add(response)
                db.flush()  # Make sure response is saved before deletion

                # DELETE the invitation and response records to allow future invitations
                # This allows users to send fresh invitations after being declined
                logger.info(
                    f"Deleting declined invitation {invitation_id} to allow future re-invitations"
                )
                db.delete(response)
                db.delete(invitation)

                db.commit()

                return {
                    "success": True,
                    "status": "declined",
                    "message": "Invitation declined successfully",
                }

        except Exception as e:
            logger.error(f"Error declining invitation: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to decline invitation",
            }

    @staticmethod
    def get_user_invitations(
        user_id: str, direction: str = "incoming", status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """
        Get user's invitations with full permission details.

        Note: Since accepted/declined invitations are deleted, only pending invitations are available.
        """
        try:
            with get_db_context_local() as db:
                # Build query based on direction
                if direction == "incoming":
                    query = db.query(SafetyNetworkRequest).filter(
                        SafetyNetworkRequest.requested_id == user_id
                    )
                else:  # outgoing
                    query = db.query(SafetyNetworkRequest).filter(
                        SafetyNetworkRequest.requester_id == user_id
                    )

                # Filter by status - only pending invitations exist in database now
                if status == "all":
                    # All that exist are pending, so no additional filter needed
                    pass
                elif status in ["accepted", "declined"]:
                    # These are deleted from database, so return empty list
                    logger.info(
                        f"Requested {status} invitations, but these are deleted after processing"
                    )
                    return []
                else:
                    # For "pending" or any other status, filter to pending
                    query = query.filter(SafetyNetworkRequest.status == "pending")

                invitations = query.order_by(
                    SafetyNetworkRequest.created_at.desc()
                ).all()

                results = []
                for invitation in invitations:
                    # Get the other user (sender for incoming, recipient for outgoing)
                    other_user_id = (
                        invitation.requester_id
                        if direction == "incoming"
                        else invitation.requested_id
                    )

                    other_user = db.query(User).filter(User.id == other_user_id).first()

                    # Generate permission summary
                    permission_summary = (
                        SafetyInvitationManager._generate_permission_summary(
                            invitation.requested_permissions or {}
                        )
                    )

                    invitation_data = {
                        "id": invitation.id,
                        "status": invitation.status,  # Will always be "pending"
                        "relationship_type": invitation.relationship_type,
                        "invitation_message": invitation.invitation_message,
                        "requested_permissions": invitation.requested_permissions,
                        "permission_summary": permission_summary,
                        "created_at": invitation.created_at.isoformat(),
                        "expires_at": (
                            invitation.expires_at.isoformat()
                            if invitation.expires_at
                            else None
                        ),
                        "other_user": (
                            {
                                "id": str(other_user.id),
                                "email": other_user.email,
                                "full_name": other_user.full_name,
                                "display_name": other_user.display_name,
                                "avatar_url": other_user.avatar_url,
                                "verification_status": (
                                    "verified"
                                    if other_user.is_verified
                                    else "unverified"
                                ),
                            }
                            if other_user
                            else None
                        ),
                    }

                    # Note: No response details since accepted/declined invitations are deleted
                    results.append(invitation_data)

                return results

        except Exception as e:
            logger.error(f"Error getting user invitations: {e}")
            return []

    # Utility methods
    @staticmethod
    def _generate_invitation_preview(
        requester_id: str,
        recipient: User,
        relationship_type: str,
        requested_permissions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate preview metadata for invitation."""
        try:
            with get_db_context_local() as db:
                requester = db.query(User).filter(User.id == requester_id).first()
                permission_summary = (
                    SafetyInvitationManager._generate_permission_summary(
                        requested_permissions
                    )
                )

                return {
                    "requester_name": requester.full_name if requester else "Unknown",
                    "relationship_type": relationship_type,
                    "permission_summary": permission_summary,
                }

        except Exception:
            return {}

    @staticmethod
    def _get_next_priority_order(user_id: str, db) -> int:
        """Get next priority order for new safety contact."""
        try:
            highest_priority = (
                db.query(SafetyContact.priority_order)
                .filter(SafetyContact.user_id == user_id)
                .order_by(SafetyContact.priority_order.desc())
                .first()
            )

            return (highest_priority[0] + 1) if highest_priority else 1

        except Exception as e:
            logger.error(f"Error getting next priority order: {e}")
            return 1
