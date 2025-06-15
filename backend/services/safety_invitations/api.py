"""
API endpoints for Safety Network Invitations.

Provides comprehensive REST API for safety network invitations including
privacy controls, permission management, blocking system, and invitation lifecycle.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator

from .manager import SafetyInvitationManager
from .search import UserSearch
from utils.auth import get_current_user_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/safety-invitations", tags=["Safety Network Invitations"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class InvitationRequest(BaseModel):
    recipient_email: str = Field(..., description="Email of user to invite")
    relationship_type: str = Field(..., description="Type of relationship")
    requested_permissions: Dict[str, Any] = Field(
        ..., description="Permissions being requested"
    )
    invitation_message: Optional[str] = Field("", description="Personal message")

    @validator("recipient_email")
    def validate_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @validator("relationship_type")
    def validate_relationship_type(cls, v):
        valid_types = [
            "family",
            "friend",
            "partner",
            "therapist",
            "counselor",
            "colleague",
            "neighbor",
            "other",
        ]
        if v not in valid_types:
            raise ValueError(f"Relationship type must be one of: {valid_types}")
        return v


class InvitationResponse(BaseModel):
    granted_permissions: Optional[Dict[str, Any]] = Field(
        None, description="Permissions being granted"
    )
    response_message: Optional[str] = Field("", description="Response message")


class UserSearchRequest(BaseModel):
    query: str = Field(..., description="Search query (email or name)")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum results")


class BlockUserRequest(BaseModel):
    blocked_user_id: str = Field(..., description="User ID to block")
    block_type: Optional[str] = Field("invitations", description="Type of block")
    reason: Optional[str] = Field("", description="Private reason for blocking")

    @validator("block_type")
    def validate_block_type(cls, v):
        valid_types = ["invitations", "discovery", "all"]
        if v not in valid_types:
            raise ValueError(f"Block type must be one of: {valid_types}")
        return v


class PermissionUpdateRequest(BaseModel):
    safety_contact_id: str = Field(..., description="Safety contact ID")
    new_permissions: Dict[str, Any] = Field(..., description="New permissions")
    change_reason: Optional[str] = Field("", description="Reason for change")


class PrivacySettingsRequest(BaseModel):
    safety_network_privacy: Dict[str, Any] = Field(
        ..., description="Privacy settings to update"
    )


class InvitationPreviewRequest(BaseModel):
    sender_id: str = Field(..., description="Sender user ID")
    relationship_type: str = Field(..., description="Relationship type")
    requested_permissions: Dict[str, Any] = Field(
        ..., description="Requested permissions"
    )


# =============================================================================
# USER SEARCH AND DISCOVERY
# =============================================================================


@router.post("/search/users")
async def search_users(
    request: UserSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Search for users by email or name for safety network invitations.
    Respects privacy settings and blocking system.
    """
    try:
        results = UserSearch.search_users(
            searching_user_id=current_user["user_id"],
            query=request.query,
            limit=request.limit,
        )

        return {
            "success": True,
            "users": results,
            "total_found": len(results),
            "search_query": request.query,
        }

    except Exception as e:
        logger.error(f"Error in user search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/check-eligibility/{user_id}")
async def check_invitation_eligibility(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Check if a specific user can be invited.
    """
    try:
        eligibility = UserSearch.check_invitation_eligibility(
            sender_id=current_user["user_id"],
            recipient_id=user_id,
        )

        return {
            "success": True,
            "eligibility": eligibility,
        }

    except Exception as e:
        logger.error(f"Error checking invitation eligibility: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# INVITATION MANAGEMENT
# =============================================================================


@router.post("/invite")
async def send_invitation(
    request: InvitationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Send a safety network invitation to another user.

    New approach: User has full control over what permissions to request.
    No auto-restrictions based on relationship type.
    """
    try:
        result = SafetyInvitationManager.send_invitation(
            requester_id=current_user["user_id"],
            recipient_email=request.recipient_email,
            relationship_type=request.relationship_type,
            requested_permissions=request.requested_permissions,
            invitation_message=request.invitation_message,
        )

        if not result["success"]:
            if result["error"] == "USER_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            elif result["error"] in [
                "BLOCKED",
                "NOT_ACCEPTING",
                "VERIFICATION_REQUIRED",
            ]:
                raise HTTPException(status_code=403, detail=result["message"])
            elif result["error"] == "RELATIONSHIP_EXISTS":
                raise HTTPException(status_code=409, detail=result["message"])
            elif result["error"] == "INVALID_PERMISSIONS":
                raise HTTPException(status_code=400, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invitation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/invitations/preview")
async def get_invitation_preview(
    request: InvitationPreviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Preview what an invitation would look like for the recipient.
    Only recipient can call this for their own previews.
    """
    try:
        if (
            current_user["user_id"] != current_user["user_id"]
        ):  # Recipient must be current user
            raise HTTPException(
                status_code=403, detail="Can only preview your own invitations"
            )

        preview = SafetyInvitationManager.get_invitation_preview(
            recipient_id=current_user["user_id"],
            sender_id=request.sender_id,
            relationship_type=request.relationship_type,
            requested_permissions=request.requested_permissions,
        )

        if "error" in preview:
            raise HTTPException(status_code=400, detail=preview["error"])

        return {
            "success": True,
            "preview": preview,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invitation preview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: str,
    request: InvitationResponse,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Accept a safety network invitation.

    User can modify the permissions when accepting - they have full control.
    """
    try:
        result = SafetyInvitationManager.accept_invitation(
            user_id=current_user["user_id"],
            invitation_id=invitation_id,
            granted_permissions=request.granted_permissions,
            response_message=request.response_message,
        )

        if not result["success"]:
            if result["error"] == "INVITATION_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            elif result["error"] == "INVALID_PERMISSIONS":
                raise HTTPException(status_code=400, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(
    invitation_id: str,
    request: InvitationResponse,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Decline a safety network invitation.
    """
    try:
        result = SafetyInvitationManager.decline_invitation(
            user_id=current_user["user_id"],
            invitation_id=invitation_id,
            response_message=request.response_message,
        )

        if not result["success"]:
            if result["error"] == "INVITATION_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining invitation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/invitations")
async def get_user_invitations(
    direction: str = Query("incoming", regex="^(incoming|outgoing)$"),
    status: str = Query("pending", regex="^(pending|accepted|declined|all)$"),
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Get invitations for the current user.
    """
    try:
        invitations = SafetyInvitationManager.get_user_invitations(
            user_id=current_user["user_id"],
            direction=direction,
            status=status,
        )

        return {
            "success": True,
            "invitations": invitations,
            "direction": direction,
            "status": status,
            "total_count": len(invitations),
        }

    except Exception as e:
        logger.error(f"Error getting user invitations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# BLOCKING SYSTEM
# =============================================================================


@router.post("/blocks")
async def block_user(
    request: BlockUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Block a user from sending invitations or discovery.
    """
    try:
        # Prevent self-blocking
        if request.blocked_user_id == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot block yourself")

        result = SafetyInvitationManager.block_user(
            blocking_user_id=current_user["user_id"],
            blocked_user_id=request.blocked_user_id,
            block_type=request.block_type,
            reason=request.reason,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/blocks/{blocked_user_id}")
async def unblock_user(
    blocked_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Unblock a previously blocked user.
    """
    try:
        result = SafetyInvitationManager.unblock_user(
            blocking_user_id=current_user["user_id"],
            blocked_user_id=blocked_user_id,
        )

        if not result["success"]:
            if result["error"] == "BLOCK_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/blocks")
async def get_blocked_users(
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Get list of users blocked by the current user.
    """
    try:
        blocked_users = SafetyInvitationManager.get_blocked_users(
            user_id=current_user["user_id"]
        )

        return {
            "success": True,
            "blocked_users": blocked_users,
            "total_count": len(blocked_users),
        }

    except Exception as e:
        logger.error(f"Error getting blocked users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# PRIVACY SETTINGS
# =============================================================================


@router.put("/privacy/settings")
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Update user's privacy settings for safety network.
    """
    try:
        result = SafetyInvitationManager.update_privacy_settings(
            user_id=current_user["user_id"],
            new_settings=request.safety_network_privacy,
        )

        if not result["success"]:
            if result["error"] == "USER_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# PERMISSION MANAGEMENT
# =============================================================================


@router.put("/permissions")
async def update_contact_permissions(
    request: PermissionUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Update permissions for an existing safety contact.
    """
    try:
        result = SafetyInvitationManager.update_contact_permissions(
            user_id=current_user["user_id"],
            safety_contact_id=request.safety_contact_id,
            new_permissions=request.new_permissions,
            change_reason=request.change_reason,
        )

        if not result["success"]:
            if result["error"] == "CONTACT_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================


@router.get("/permissions/available")
async def get_available_permissions():
    """
    Get all available permissions that users can choose from.
    Used for building the permission selection UI.
    """
    try:
        permissions_data = SafetyInvitationManager.get_available_permissions()
        return {
            "success": True,
            "permissions": permissions_data["permissions"],
            "categories": permissions_data["categories"],
        }
    except Exception as e:
        logger.error(f"Error getting available permissions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get available permissions"
        )


@router.get("/relationship-types")
async def get_relationship_types():
    """
    Get available relationship types with suggested permissions.
    Suggestions are just hints - user has full control.
    """
    try:
        relationship_types = SafetyInvitationManager.get_relationship_types()
        return {"success": True, "relationship_types": relationship_types}
    except Exception as e:
        logger.error(f"Error getting relationship types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relationship types")


@router.get("/invitations/{invitation_id}/preview")
async def get_invitation_preview(
    invitation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_session),
):
    """
    Get a preview of an invitation with clear permission breakdown.
    """
    try:
        with get_db_context_local() as db:
            invitation = (
                db.query(SafetyNetworkRequest)
                .filter(
                    and_(
                        SafetyNetworkRequest.id == invitation_id,
                        SafetyNetworkRequest.requested_id == current_user["user_id"],
                        SafetyNetworkRequest.status == "pending",
                    )
                )
                .first()
            )

            if not invitation:
                raise HTTPException(status_code=404, detail="Invitation not found")

            # Get requester info
            requester = (
                db.query(User).filter(User.id == invitation.requester_id).first()
            )

            # Generate permission summary
            permission_summary = SafetyInvitationManager._generate_permission_summary(
                invitation.requested_permissions or {}
            )

            return {
                "success": True,
                "invitation": {
                    "id": invitation.id,
                    "requester": {
                        "name": requester.full_name if requester else "Unknown",
                        "email": requester.email if requester else None,
                    },
                    "relationship_type": invitation.relationship_type,
                    "message": invitation.invitation_message,
                    "requested_permissions": invitation.requested_permissions,
                    "permission_summary": permission_summary,
                    "expires_at": (
                        invitation.expires_at.isoformat()
                        if invitation.expires_at
                        else None
                    ),
                },
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invitation preview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
