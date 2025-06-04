"""
Safety Network Invitation Management System.

Handles the complete lifecycle of safety network invitations including privacy controls,
permission management, blocking system, and invitation lifecycle.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os
from sqlalchemy import and_, or_

from .database import get_db
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

# Add safety network service path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "safety_network"))
from services.safety_network.manager import SafetyNetworkManager

logger = logging.getLogger(__name__)


class SafetyInvitationManager:
    """Manages safety network invitations with privacy controls and permission management."""

    # Default permission templates
    DEFAULT_PERMISSIONS = {
        "emergency_only": {
            "can_see_status": True,
            "can_see_location": True,
            "emergency_contact": True,
            "can_receive_alerts": True,
            "can_see_mood": False,
            "can_see_activities": False,
            "can_see_goals": False,
            "alert_preferences": {
                "crisis_alerts": True,
                "wellness_check_alerts": False,
                "goal_reminders": False,
                "mood_concerns": False,
            },
        },
        "wellness_support": {
            "can_see_status": True,
            "can_see_location": False,
            "emergency_contact": False,
            "can_receive_alerts": True,
            "can_see_mood": True,
            "can_see_activities": False,
            "can_see_goals": False,
            "alert_preferences": {
                "crisis_alerts": True,
                "wellness_check_alerts": True,
                "goal_reminders": False,
                "mood_concerns": True,
            },
        },
        "basic_support": {
            "can_see_status": True,
            "can_see_location": False,
            "emergency_contact": False,
            "can_receive_alerts": True,
            "can_see_mood": True,
            "can_see_activities": True,
            "can_see_goals": False,
            "alert_preferences": {
                "crisis_alerts": False,
                "wellness_check_alerts": True,
                "goal_reminders": False,
                "mood_concerns": True,
            },
        },
        "family_member": {
            "can_see_status": True,
            "can_see_location": True,
            "emergency_contact": True,
            "can_receive_alerts": True,
            "can_see_mood": True,
            "can_see_activities": True,
            "can_see_goals": True,
            "alert_preferences": {
                "crisis_alerts": True,
                "wellness_check_alerts": True,
                "goal_reminders": True,
                "mood_concerns": True,
            },
        },
    }

    @staticmethod
    def send_invitation(
        requester_id: str,
        recipient_email: str,
        relationship_type: str,
        requested_permissions: Dict[str, Any],
        invitation_message: str = "",
    ) -> Dict[str, Any]:
        """
        Send a safety network invitation to another user.

        Args:
            requester_id: User sending the invitation
            recipient_email: Email of user being invited
            relationship_type: Type of relationship
            requested_permissions: Permissions being requested
            invitation_message: Personal message from requester

        Returns:
            Dictionary with invitation details and success status
        """
        try:
            with get_db() as db:
                # 1. Find recipient by email
                recipient = (
                    db.query(User)
                    .filter(
                        and_(
                            User.email == recipient_email.lower().strip(),
                            User.is_active == True,
                        )
                    )
                    .first()
                )

                if not recipient:
                    return {
                        "success": False,
                        "error": "USER_NOT_FOUND",
                        "message": "No active user found with that email address",
                    }

                # 2. Check invitation eligibility
                eligibility = UserSearch.check_invitation_eligibility(
                    requester_id, recipient.id, db
                )

                if not eligibility["can_invite"]:
                    return {
                        "success": False,
                        "error": eligibility["reason_code"],
                        "message": eligibility["user_message"],
                    }

                # 3. Check for existing relationship
                existing_relationships = UserSearch._get_existing_relationships(
                    db, requester_id
                )

                if recipient.id in existing_relationships:
                    return {
                        "success": False,
                        "error": "RELATIONSHIP_EXISTS",
                        "message": f"You already have a {existing_relationships[recipient.id]} with this user",
                    }

                # 4. Get recipient's default permissions for conflict detection
                recipient_defaults = UserSearch.get_user_defaults_for_relationship(
                    str(recipient.id), relationship_type
                )

                # 5. Detect permission conflicts
                conflicts = SafetyInvitationManager._detect_permission_conflicts(
                    requested_permissions, recipient_defaults
                )

                # 6. Check if invitation is eligible for auto-accept
                auto_accept_eligible = (
                    SafetyInvitationManager._check_auto_accept_eligibility(
                        recipient, requested_permissions, recipient_defaults, conflicts
                    )
                )

                # 7. Create invitation request
                request = SafetyNetworkRequest(
                    requester_id=requester_id,
                    requested_id=str(recipient.id),
                    relationship_type=relationship_type,
                    invitation_message=invitation_message,
                    requested_permissions=requested_permissions,
                    recipient_default_permissions=recipient_defaults,
                    permission_conflicts=conflicts,
                    auto_accept_eligible=auto_accept_eligible,
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

                # 8. Auto-accept if eligible
                if auto_accept_eligible:
                    accept_result = SafetyInvitationManager.accept_invitation(
                        str(recipient.id),
                        request.id,
                        recipient_defaults,
                        auto_accepted=True,
                    )

                    if accept_result["success"]:
                        return {
                            "success": True,
                            "invitation_id": request.id,
                            "status": "auto_accepted",
                            "message": "Invitation was automatically accepted based on user preferences",
                        }

                return {
                    "success": True,
                    "invitation_id": request.id,
                    "status": "pending",
                    "recipient_name": recipient.full_name,
                    "expires_at": request.expires_at.isoformat(),
                    "has_conflicts": len(conflicts) > 0,
                    "conflict_count": len(conflicts),
                }

        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to send invitation",
            }

    @staticmethod
    def get_invitation_preview(
        recipient_id: str,
        sender_id: str,
        relationship_type: str,
        requested_permissions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a preview of what an invitation would look like for the recipient.

        Args:
            recipient_id: User who would receive the invitation
            sender_id: User who would send the invitation
            relationship_type: Type of relationship
            requested_permissions: Permissions that would be requested

        Returns:
            Preview data including conflicts and recommendations
        """
        try:
            with get_db() as db:
                # Get users
                sender = db.query(User).filter(User.id == sender_id).first()
                recipient = db.query(User).filter(User.id == recipient_id).first()

                if not sender or not recipient:
                    return {"error": "Users not found"}

                # Get recipient's defaults for this relationship type
                recipient_defaults = UserSearch.get_user_defaults_for_relationship(
                    recipient_id, relationship_type
                )

                # Detect conflicts
                conflicts = SafetyInvitationManager._detect_permission_conflicts(
                    requested_permissions, recipient_defaults
                )

                # Check auto-accept eligibility
                auto_accept_eligible = (
                    SafetyInvitationManager._check_auto_accept_eligibility(
                        recipient, requested_permissions, recipient_defaults, conflicts
                    )
                )

                return {
                    "sender_name": sender.full_name,
                    "relationship_type": relationship_type,
                    "requested_permissions": requested_permissions,
                    "your_defaults": recipient_defaults,
                    "conflicts": conflicts,
                    "auto_accept_eligible": auto_accept_eligible,
                    "recommendations": SafetyInvitationManager._generate_permission_recommendations(
                        requested_permissions, recipient_defaults, conflicts
                    ),
                }

        except Exception as e:
            logger.error(f"Error generating invitation preview: {e}")
            return {"error": "Failed to generate preview"}

    @staticmethod
    def accept_invitation(
        user_id: str,
        invitation_id: str,
        granted_permissions: Optional[Dict[str, Any]] = None,
        response_message: str = "",
        auto_accepted: bool = False,
    ) -> Dict[str, Any]:
        """
        Accept a safety network invitation.

        Args:
            user_id: User accepting the invitation
            invitation_id: Invitation being accepted
            granted_permissions: Permissions being granted (optional)
            response_message: Optional response message
            auto_accepted: Whether this was auto-accepted

        Returns:
            Dictionary with success status and safety contact details
        """
        try:
            with get_db() as db:
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

                # 2. Use granted permissions or fall back to requested permissions
                final_permissions = (
                    granted_permissions or invitation.requested_permissions
                )

                # 3. Create safety contact for requester
                priority_order = SafetyInvitationManager._get_next_priority_order(
                    invitation.requester_id, db
                )

                safety_contact = SafetyContact(
                    user_id=invitation.requester_id,  # Requester gets the contact
                    contact_user_id=user_id,  # User being contacted
                    priority_order=priority_order,
                    relationship_type=invitation.relationship_type,
                    notes=f"Added via safety network invitation on {datetime.utcnow().strftime('%Y-%m-%d')}",
                    allowed_communication_methods=["phone", "email", "sms"],
                    preferred_communication_method="phone",
                    custom_metadata={
                        "permissions": final_permissions,
                        "invitation_id": invitation_id,
                        "auto_accepted": auto_accepted,
                    },
                )

                db.add(safety_contact)

                # 4. Create response record
                response = SafetyNetworkResponse(
                    request_id=invitation_id,
                    response_type="accept",
                    response_message=response_message,
                    granted_permissions=final_permissions,
                )

                db.add(response)

                # 5. Update invitation status
                invitation.status = SafetyNetworkRequestStatus.ACCEPTED.value
                invitation.updated_at = datetime.utcnow()

                db.commit()

                return {
                    "success": True,
                    "safety_contact_id": safety_contact.id,
                    "granted_permissions": final_permissions,
                    "status": "accepted",
                    "auto_accepted": auto_accepted,
                }

        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to accept invitation",
            }

    @staticmethod
    def decline_invitation(
        user_id: str, invitation_id: str, response_message: str = ""
    ) -> Dict[str, Any]:
        """
        Decline a safety network invitation.

        Args:
            user_id: User declining the invitation
            invitation_id: Invitation being declined
            response_message: Optional response message

        Returns:
            Dictionary with success status
        """
        try:
            with get_db() as db:
                # Get invitation
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

                # Create response record
                response = SafetyNetworkResponse(
                    request_id=invitation_id,
                    response_type="decline",
                    response_message=response_message,
                )

                db.add(response)

                # Update invitation status
                invitation.status = SafetyNetworkRequestStatus.DECLINED.value
                invitation.updated_at = datetime.utcnow()

                db.commit()

                return {"success": True, "status": "declined"}

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
        Get invitations for a user (incoming or outgoing).

        Args:
            user_id: User to get invitations for
            direction: "incoming" or "outgoing"
            status: "pending", "accepted", "declined", "all"

        Returns:
            List of invitation dictionaries
        """
        try:
            with get_db() as db:
                # Build query based on direction
                if direction == "incoming":
                    query = db.query(SafetyNetworkRequest).filter(
                        SafetyNetworkRequest.requested_id == user_id
                    )
                else:  # outgoing
                    query = db.query(SafetyNetworkRequest).filter(
                        SafetyNetworkRequest.requester_id == user_id
                    )

                # Add status filter
                if status != "all":
                    query = query.filter(SafetyNetworkRequest.status == status)

                invitations = query.order_by(
                    SafetyNetworkRequest.created_at.desc()
                ).all()

                # Format invitations with user details
                results = []
                for invitation in invitations:
                    # Get the other user (sender for incoming, recipient for outgoing)
                    other_user_id = (
                        invitation.requester_id
                        if direction == "incoming"
                        else invitation.requested_id
                    )

                    other_user = db.query(User).filter(User.id == other_user_id).first()

                    invitation_data = {
                        "id": invitation.id,
                        "status": invitation.status,
                        "relationship_type": invitation.relationship_type,
                        "invitation_message": invitation.invitation_message,
                        "requested_permissions": invitation.requested_permissions,
                        "permission_conflicts": invitation.permission_conflicts or [],
                        "auto_accept_eligible": invitation.auto_accept_eligible,
                        "created_at": invitation.created_at.isoformat(),
                        "expires_at": (
                            invitation.expires_at.isoformat()
                            if invitation.expires_at
                            else None
                        ),
                        "other_user": (
                            {
                                "id": str(other_user.id),
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

                    # Add response details if invitation is not pending
                    if invitation.status != "pending":
                        response = (
                            db.query(SafetyNetworkResponse)
                            .filter(SafetyNetworkResponse.request_id == invitation.id)
                            .first()
                        )

                        if response:
                            invitation_data["response"] = {
                                "response_type": response.response_type,
                                "response_message": response.response_message,
                                "granted_permissions": response.granted_permissions,
                                "responded_at": response.responded_at.isoformat(),
                            }

                    results.append(invitation_data)

                return results

        except Exception as e:
            logger.error(f"Error getting user invitations: {e}")
            return []

    # =============================================================================
    # BLOCKING SYSTEM
    # =============================================================================

    @staticmethod
    def block_user(
        blocking_user_id: str,
        blocked_user_id: str,
        block_type: str = "invitations",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Block a user from sending invitations or being discovered.

        Args:
            blocking_user_id: User doing the blocking
            blocked_user_id: User being blocked
            block_type: "invitations", "discovery", or "all"
            reason: Private reason for blocking

        Returns:
            Success status and block details
        """
        try:
            with get_db() as db:
                # Check if block already exists
                existing_block = (
                    db.query(UserBlock)
                    .filter(
                        and_(
                            UserBlock.blocking_user_id == blocking_user_id,
                            UserBlock.blocked_user_id == blocked_user_id,
                        )
                    )
                    .first()
                )

                if existing_block:
                    # Update existing block
                    existing_block.block_type = block_type
                    existing_block.blocker_reason = reason
                    existing_block.created_at = datetime.utcnow()
                else:
                    # Create new block
                    new_block = UserBlock(
                        blocking_user_id=blocking_user_id,
                        blocked_user_id=blocked_user_id,
                        block_type=block_type,
                        blocker_reason=reason,
                    )
                    db.add(new_block)

                db.commit()

                return {
                    "success": True,
                    "block_type": block_type,
                    "message": f"User blocked from {block_type}",
                }

        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to block user",
            }

    @staticmethod
    def unblock_user(blocking_user_id: str, blocked_user_id: str) -> Dict[str, Any]:
        """
        Unblock a previously blocked user.

        Args:
            blocking_user_id: User doing the unblocking
            blocked_user_id: User being unblocked

        Returns:
            Success status
        """
        try:
            with get_db() as db:
                block = (
                    db.query(UserBlock)
                    .filter(
                        and_(
                            UserBlock.blocking_user_id == blocking_user_id,
                            UserBlock.blocked_user_id == blocked_user_id,
                        )
                    )
                    .first()
                )

                if not block:
                    return {
                        "success": False,
                        "error": "BLOCK_NOT_FOUND",
                        "message": "No block found for this user",
                    }

                db.delete(block)
                db.commit()

                return {"success": True, "message": "User has been unblocked"}

        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to unblock user",
            }

    @staticmethod
    def get_blocked_users(user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of users blocked by the current user.

        Args:
            user_id: User whose blocks to retrieve

        Returns:
            List of blocked user details
        """
        try:
            with get_db() as db:
                blocks = (
                    db.query(UserBlock)
                    .filter(UserBlock.blocking_user_id == user_id)
                    .all()
                )

                results = []
                for block in blocks:
                    blocked_user = (
                        db.query(User).filter(User.id == block.blocked_user_id).first()
                    )

                    if blocked_user:
                        results.append(
                            {
                                "id": str(blocked_user.id),
                                "full_name": blocked_user.full_name,
                                "display_name": blocked_user.display_name,
                                "block_type": block.block_type,
                                "blocked_at": block.created_at.isoformat(),
                            }
                        )

                return results

        except Exception as e:
            logger.error(f"Error getting blocked users: {e}")
            return []

    # =============================================================================
    # PERMISSION MANAGEMENT
    # =============================================================================

    @staticmethod
    def update_contact_permissions(
        user_id: str,
        safety_contact_id: str,
        new_permissions: Dict[str, Any],
        change_reason: str = "",
    ) -> Dict[str, Any]:
        """
        Update permissions for an existing safety contact.

        Args:
            user_id: User who owns the safety contact
            safety_contact_id: Safety contact to update
            new_permissions: New permission set
            change_reason: Reason for the change

        Returns:
            Success status and updated permissions
        """
        try:
            with get_db() as db:
                # Get safety contact
                contact = (
                    db.query(SafetyContact)
                    .filter(
                        and_(
                            SafetyContact.id == safety_contact_id,
                            SafetyContact.user_id == user_id,
                        )
                    )
                    .first()
                )

                if not contact:
                    return {
                        "success": False,
                        "error": "CONTACT_NOT_FOUND",
                        "message": "Safety contact not found",
                    }

                # Get old permissions
                old_permissions = (
                    contact.custom_metadata.get("permissions", {})
                    if contact.custom_metadata
                    else {}
                )

                # Update permissions
                if not contact.custom_metadata:
                    contact.custom_metadata = {}
                contact.custom_metadata["permissions"] = new_permissions
                contact.updated_at = datetime.utcnow()

                # Log the permission change
                permission_change = SafetyPermissionChange(
                    safety_contact_id=safety_contact_id,
                    user_id=user_id,
                    changed_by_user_id=user_id,
                    old_permissions=old_permissions,
                    new_permissions=new_permissions,
                    change_reason=change_reason,
                )

                db.add(permission_change)
                db.commit()

                return {
                    "success": True,
                    "updated_permissions": new_permissions,
                    "message": "Permissions updated successfully",
                }

        except Exception as e:
            logger.error(f"Error updating contact permissions: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to update permissions",
            }

    # =============================================================================
    # PRIVACY SETTINGS
    # =============================================================================

    @staticmethod
    def update_privacy_settings(
        user_id: str, new_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user's privacy settings for safety network.

        Args:
            user_id: User whose settings to update
            new_settings: New privacy settings

        Returns:
            Success status and updated settings
        """
        try:
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {
                        "success": False,
                        "error": "USER_NOT_FOUND",
                        "message": "User not found",
                    }

                # Initialize privacy settings if they don't exist
                if not user.privacy_settings:
                    user.privacy_settings = {}

                # Update safety network privacy settings
                if "safety_network_privacy" not in user.privacy_settings:
                    user.privacy_settings["safety_network_privacy"] = {}

                # Merge new settings with existing ones
                current_safety_settings = user.privacy_settings[
                    "safety_network_privacy"
                ]
                current_safety_settings.update(new_settings)

                db.commit()

                return {
                    "success": True,
                    "updated_settings": current_safety_settings,
                    "message": "Privacy settings updated successfully",
                }

        except Exception as e:
            logger.error(f"Error updating privacy settings: {e}")
            return {
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "Failed to update privacy settings",
            }

    @staticmethod
    def get_default_permissions_for_relationship(
        relationship_type: str,
    ) -> Dict[str, Any]:
        """
        Get the default permission template for a relationship type.

        Args:
            relationship_type: Type of relationship

        Returns:
            Default permissions dictionary
        """
        return SafetyInvitationManager.DEFAULT_PERMISSIONS.get(
            relationship_type,
            SafetyInvitationManager.DEFAULT_PERMISSIONS["basic_support"],
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    @staticmethod
    def _detect_permission_conflicts(
        requested: Dict[str, Any], defaults: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between requested and default permissions."""
        conflicts = []

        if not defaults:  # No defaults set, no conflicts
            return conflicts

        for key, requested_value in requested.items():
            if key in defaults:
                default_value = defaults[key]

                if isinstance(requested_value, dict) and isinstance(
                    default_value, dict
                ):
                    # Recursively check nested permissions
                    nested_conflicts = (
                        SafetyInvitationManager._detect_permission_conflicts(
                            requested_value, default_value
                        )
                    )
                    for conflict in nested_conflicts:
                        conflict["path"] = f"{key}.{conflict['path']}"
                        conflicts.append(conflict)
                elif requested_value != default_value:
                    conflicts.append(
                        {
                            "path": key,
                            "requested": requested_value,
                            "default": default_value,
                            "severity": (
                                "medium" if isinstance(requested_value, bool) else "low"
                            ),
                        }
                    )

        return conflicts

    @staticmethod
    def _check_auto_accept_eligibility(
        recipient: User,
        requested: Dict[str, Any],
        defaults: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
    ) -> bool:
        """Check if invitation is eligible for auto-accept."""
        try:
            # Get user's auto-accept settings
            privacy_settings = recipient.privacy_settings.get(
                "safety_network_privacy", {}
            )
            invitation_controls = privacy_settings.get("invitation_controls", {})

            auto_accept_settings = invitation_controls.get("auto_accept", {})

            # Check if auto-accept is enabled
            if not auto_accept_settings.get("enabled", False):
                return False

            # Check if there are conflicts and user allows auto-accept with conflicts
            if conflicts and not auto_accept_settings.get(
                "allow_with_conflicts", False
            ):
                return False

            # Check conflict severity threshold
            max_severity = auto_accept_settings.get("max_conflict_severity", "low")
            severity_levels = {"low": 0, "medium": 1, "high": 2}
            max_level = severity_levels.get(max_severity, 0)

            for conflict in conflicts:
                conflict_level = severity_levels.get(conflict.get("severity", "low"), 0)
                if conflict_level > max_level:
                    return False

            return True

        except Exception:
            return False

    @staticmethod
    def _generate_invitation_preview(
        requester_id: str,
        recipient: User,
        relationship_type: str,
        requested_permissions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate preview metadata for invitation."""
        try:
            with get_db() as db:
                requester = db.query(User).filter(User.id == requester_id).first()

                return {
                    "requester_name": requester.full_name if requester else "Unknown",
                    "relationship_type": relationship_type,
                    "permission_summary": SafetyInvitationManager._summarize_permissions(
                        requested_permissions
                    ),
                    "estimated_access_level": SafetyInvitationManager._estimate_access_level(
                        requested_permissions
                    ),
                }

        except Exception:
            return {}

    @staticmethod
    def _summarize_permissions(permissions: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of permission levels."""
        summary = {
            "location_access": permissions.get("can_see_location", False),
            "emergency_contact": permissions.get("emergency_contact", False),
            "mood_tracking": permissions.get("can_see_mood", False),
            "activity_tracking": permissions.get("can_see_activities", False),
            "alert_count": len(
                [k for k, v in permissions.get("alert_preferences", {}).items() if v]
            ),
        }
        return summary

    @staticmethod
    def _estimate_access_level(permissions: Dict[str, Any]) -> str:
        """Estimate the overall access level of permissions."""
        emergency_features = [
            permissions.get("can_see_location", False),
            permissions.get("emergency_contact", False),
            permissions.get("can_receive_alerts", False),
        ]

        personal_features = [
            permissions.get("can_see_mood", False),
            permissions.get("can_see_activities", False),
            permissions.get("can_see_goals", False),
        ]

        if all(emergency_features) and all(personal_features):
            return "comprehensive"
        elif any(emergency_features) and any(personal_features):
            return "moderate"
        elif any(emergency_features):
            return "emergency_only"
        elif any(personal_features):
            return "basic"
        else:
            return "minimal"

    @staticmethod
    def _generate_permission_recommendations(
        requested: Dict[str, Any],
        defaults: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for resolving permission conflicts."""
        recommendations = []

        for conflict in conflicts:
            rec = {
                "path": conflict["path"],
                "recommendation": "consider_default",
                "explanation": f"Your usual preference for this is {conflict['default']}, but they're requesting {conflict['requested']}",
            }

            # Add specific recommendations based on permission type
            if "location" in conflict["path"].lower():
                rec["privacy_note"] = (
                    "Location sharing is sensitive - only grant to trusted contacts"
                )
            elif "emergency" in conflict["path"].lower():
                rec["importance_note"] = (
                    "Emergency contact permissions are crucial for safety"
                )

            recommendations.append(rec)

        return recommendations

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

    @staticmethod
    def get_relationship_types():
        """Get available relationship types."""
        return [
            {
                "value": "family",
                "label": "Family Member",
                "description": "Parent, sibling, child, or other family",
            },
            {
                "value": "friend",
                "label": "Friend",
                "description": "Close personal friend",
            },
            {
                "value": "partner",
                "label": "Partner/Spouse",
                "description": "Romantic partner or spouse",
            },
            {
                "value": "therapist",
                "label": "Therapist",
                "description": "Licensed therapist or counselor",
            },
            {
                "value": "counselor",
                "label": "Counselor",
                "description": "Guidance counselor or mental health professional",
            },
            {
                "value": "colleague",
                "label": "Colleague",
                "description": "Work colleague or professional contact",
            },
            {
                "value": "neighbor",
                "label": "Neighbor",
                "description": "Neighbor or nearby contact",
            },
            {
                "value": "other",
                "label": "Other",
                "description": "Other type of relationship",
            },
        ]

    @staticmethod
    def get_permission_templates():
        """Get permission templates with names and descriptions."""
        templates = {}
        for (
            template_name,
            permissions,
        ) in SafetyInvitationManager.DEFAULT_PERMISSIONS.items():
            templates[template_name] = {
                "name": template_name.replace("_", " ").title(),
                "description": SafetyInvitationManager._get_template_description(
                    template_name
                ),
                "permissions": permissions,
            }
        return templates

    @staticmethod
    def _get_template_description(template_name: str) -> str:
        """Get description for permission template."""
        descriptions = {
            "emergency_only": "Basic emergency contact with location access during crises",
            "wellness_support": "Mental health support with mood tracking but no location access",
            "basic_support": "General support with mood and activity tracking",
            "family_member": "Comprehensive access for trusted family members",
        }
        return descriptions.get(template_name, "Custom permission template")

    @staticmethod
    def get_default_permissions_for_relationship(
        relationship_type: str,
    ) -> Dict[str, Any]:
        """Get default permissions for a relationship type."""
        # Map relationship types to permission templates
        relationship_to_template = {
            "family": "family_member",
            "partner": "family_member",
            "therapist": "wellness_support",
            "counselor": "wellness_support",
            "friend": "basic_support",
            "colleague": "basic_support",
            "neighbor": "emergency_only",
            "other": "basic_support",
        }

        template_name = relationship_to_template.get(relationship_type, "basic_support")
        return SafetyInvitationManager.DEFAULT_PERMISSIONS[template_name]
