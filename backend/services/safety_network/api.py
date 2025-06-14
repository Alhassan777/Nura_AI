"""
Safety Network API endpoints for managing emergency contacts and safety checkups.
SECURE: All endpoints use JWT authentication - users can only access their own safety data.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

from .scheduler import safety_scheduler, CheckupType, CheckupMethod
from .manager import SafetyNetworkManager
from models import CommunicationMethod

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/safety-network", tags=["safety_network"])


# Request/Response models
class ContactOutreachRequest(BaseModel):
    contact_id: str
    crisis_level: str
    message: str
    preferred_method: str = "phone"


class CrisisLogRequest(BaseModel):
    contact_id: str
    contact_method: str
    contact_success: bool
    crisis_summary: str
    next_steps: Optional[str] = None


class AddContactRequest(BaseModel):
    contact_id: str
    relationship_type: str


class UpdateEmergencyContactRequest(BaseModel):
    is_emergency_contact: bool


class UpdateContactPriorityRequest(BaseModel):
    priority_order: int = Field(
        ..., ge=1, le=100, description="New priority order (1 = highest priority)"
    )


class ReorderContactsRequest(BaseModel):
    contact_priorities: Dict[str, int] = Field(
        ..., description="Mapping of contact_id to new priority order"
    )

    @validator("contact_priorities")
    def validate_priorities(cls, v):
        if not v:
            raise ValueError("At least one contact priority must be specified")

        # Check that all priorities are valid
        for contact_id, priority in v.items():
            if priority < 1 or priority > 100:
                raise ValueError(
                    f"Priority for contact {contact_id} must be between 1 and 100"
                )

        return v


# 🔐 SECURE SAFETY ENDPOINTS - JWT Authentication Required


@router.get("/contacts")
async def get_user_safety_contacts(
    emergency_only: bool = Query(False, description="Only return emergency contacts"),
    active_only: bool = Query(True, description="Only return active contacts"),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get user's safety network contacts for crisis intervention.
    This endpoint is called by VAPI webhook during crisis situations.
    """
    try:
        contacts = SafetyNetworkManager.get_user_safety_contacts(
            user_id=user_id,
            active_only=active_only,
            emergency_only=emergency_only,
            ordered_by_priority=True,
        )

        logger.info(
            f"Retrieved {len(contacts)} contacts for user {user_id} (emergency_only: {emergency_only})"
        )

        return {
            "success": True,
            "contacts": contacts,
            "count": len(contacts),
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error getting safety contacts for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve contacts: {str(e)}"
        )


@router.get("/helping")
async def get_who_am_i_helping(
    active_only: bool = Query(True, description="Only return active relationships"),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get relationships where current user is a safety contact for others.
    Shows who the current user is helping in their safety network.
    """
    try:
        helping_relationships = SafetyNetworkManager.get_helping_relationships(
            contact_user_id=user_id,
            active_only=active_only,
        )

        logger.info(
            f"Retrieved {len(helping_relationships)} helping relationships for user {user_id}"
        )

        return {
            "success": True,
            "helping": helping_relationships,
            "count": len(helping_relationships),
            "message": f"You are helping {len(helping_relationships)} people in their safety network",
        }

    except Exception as e:
        logger.error(f"Error getting helping relationships for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve helping relationships: {str(e)}",
        )


@router.post("/contacts")
async def add_safety_contact(
    request: AddContactRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Add a contact to user's safety network.
    """
    try:
        # Get next priority order
        existing_contacts = SafetyNetworkManager.get_user_safety_contacts(
            user_id=user_id, active_only=True
        )
        priority_order = len(existing_contacts) + 1

        contact_id = SafetyNetworkManager.add_safety_contact(
            user_id=user_id,
            contact_user_id=request.contact_id,
            priority_order=priority_order,
            relationship_type=request.relationship_type,
            allowed_communication_methods=["phone", "email", "sms"],
            preferred_communication_method="phone",
            is_emergency_contact=False,
        )

        if not contact_id:
            raise HTTPException(status_code=400, detail="Failed to add safety contact")

        logger.info(f"Added safety contact {contact_id} for user {user_id}")

        return {
            "success": True,
            "contact_id": contact_id,
            "message": "Contact added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding safety contact for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add contact: {str(e)}")


@router.delete("/contacts/{contact_id}")
async def remove_safety_contact(
    contact_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Remove a contact from user's safety network.
    """
    try:
        success = SafetyNetworkManager.remove_safety_contact(
            contact_id=contact_id, user_id=user_id
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Contact not found or already removed"
            )

        logger.info(f"Removed safety contact {contact_id} for user {user_id}")

        return {
            "success": True,
            "message": "Contact removed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing safety contact for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to remove contact: {str(e)}"
        )


@router.put("/contacts/{contact_id}")
async def update_emergency_contact_status(
    contact_id: str,
    request: UpdateEmergencyContactRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Update emergency contact status for a safety contact.
    """
    try:
        success = SafetyNetworkManager.update_safety_contact(
            contact_id=contact_id,
            user_id=user_id,
            is_emergency_contact=request.is_emergency_contact,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")

        logger.info(
            f"Updated emergency status for contact {contact_id} (user {user_id}): {request.is_emergency_contact}"
        )

        return {
            "success": True,
            "message": "Emergency contact status updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating emergency contact status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update contact: {str(e)}"
        )


@router.post("/contact-outreach")
async def initiate_contact_outreach(
    request: ContactOutreachRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Initiate contact outreach to a safety network contact during crisis.
    This endpoint coordinates the actual outreach (returns contact info for VAPI SMS/call).
    """
    try:
        # Get the specific contact
        contacts = SafetyNetworkManager.get_user_safety_contacts(
            user_id=user_id,
            active_only=True,
            emergency_only=True,  # Crisis situations only use emergency contacts
        )

        # Find the requested contact
        target_contact = None
        for contact in contacts:
            if contact["id"] == request.contact_id:
                target_contact = contact
                break

        if not target_contact:
            logger.warning(f"Contact {request.contact_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Emergency contact not found")

        # Determine best contact method
        available_methods = target_contact.get("allowed_communication_methods", [])
        preferred_method = request.preferred_method

        if preferred_method not in available_methods:
            # Fall back to first available method
            preferred_method = available_methods[0] if available_methods else "phone"

        # Get contact details based on method
        contact_info = {
            "contact_id": target_contact["id"],
            "contact_name": target_contact.get("full_name", "Emergency Contact"),
            "method": preferred_method,
            "crisis_level": request.crisis_level,
            "message": request.message,
        }

        if preferred_method == "phone":
            contact_info["phone_number"] = target_contact.get("phone_number")
        elif preferred_method == "sms":
            contact_info["phone_number"] = target_contact.get("phone_number")
        elif preferred_method == "email":
            contact_info["email"] = target_contact.get("email")

        # Log the outreach attempt initiation
        SafetyNetworkManager.log_contact_attempt(
            safety_contact_id=request.contact_id,
            user_id=user_id,
            contact_method=CommunicationMethod(preferred_method),
            success=True,  # Initiation successful, actual contact pending
            reason=f"Crisis intervention: {request.crisis_level}",
            initiated_by="vapi_webhook",
            message_content=request.message,
            contact_metadata={"crisis_level": request.crisis_level},
        )

        logger.info(
            f"Initiated contact outreach to {request.contact_id} for user {user_id} via {preferred_method}"
        )

        return {
            "success": True,
            "contact_info": contact_info,
            "outreach_initiated": True,
            "method": preferred_method,
            "message": f"Outreach initiated to {contact_info['contact_name']} via {preferred_method}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating contact outreach for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate outreach: {str(e)}"
        )


@router.post("/crisis-log")
async def log_crisis_intervention(
    request: CrisisLogRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Log the outcome of a crisis intervention contact attempt.
    Called by VAPI webhook after attempting to contact emergency contact.
    """
    try:
        # Convert string to enum
        method_enum = CommunicationMethod(request.contact_method)

        # Log the contact attempt outcome
        log_success = SafetyNetworkManager.log_contact_attempt(
            safety_contact_id=request.contact_id,
            user_id=user_id,
            contact_method=method_enum,
            success=request.contact_success,
            reason="Crisis intervention outcome",
            initiated_by="vapi_webhook",
            message_content=request.crisis_summary,
            contact_metadata={
                "next_steps": request.next_steps,
                "logged_via": "crisis_intervention_api",
            },
        )

        if log_success:
            logger.info(
                f"Crisis intervention logged for user {user_id}, contact {request.contact_id}: success={request.contact_success}"
            )

            return {
                "success": True,
                "logged": True,
                "contact_id": request.contact_id,
                "method": request.contact_method,
                "outcome": "successful" if request.contact_success else "failed",
                "message": "Crisis intervention logged successfully",
            }
        else:
            logger.error(f"Failed to log crisis intervention for user {user_id}")
            raise HTTPException(
                status_code=500, detail="Failed to log crisis intervention"
            )

    except ValueError as e:
        logger.error(f"Invalid communication method: {request.contact_method}")
        raise HTTPException(
            status_code=400, detail=f"Invalid contact method: {request.contact_method}"
        )
    except Exception as e:
        logger.error(f"Error logging crisis intervention for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to log intervention: {str(e)}"
        )


# 🔐 SECURE SAFETY ENDPOINTS - JWT Authentication Required


@router.post("/checkup/schedules")
async def schedule_safety_checkup(
    contact_id: str = Query(..., description="Safety contact ID"),
    checkup_type: str = Query("wellness_check", description="Type of checkup"),
    method: str = Query("voice_call", description="Checkup method"),
    frequency: str = Query("weekly", description="Frequency (daily/weekly/monthly)"),
    time_of_day: str = Query("afternoon", description="Time preference"),
    days_of_week: Optional[List[str]] = Query(
        None, description="Days of week for weekly/monthly"
    ),
    custom_message: Optional[str] = Query(None, description="Custom message template"),
    timezone: str = Query("UTC", description="User timezone"),
    user_id: str = Depends(get_current_user_id),
):
    """Schedule recurring checkups with a safety contact. JWT secured - user manages their own checkups."""
    try:
        # Validate enum values
        checkup_type_enum = CheckupType(checkup_type)
        method_enum = CheckupMethod(method)

        result = await safety_scheduler.schedule_safety_checkup(
            user_id=user_id,
            contact_id=contact_id,
            checkup_type=checkup_type_enum,
            method=method_enum,
            frequency=frequency,
            time_of_day=time_of_day,
            days_of_week=days_of_week,
            custom_message=custom_message,
            timezone=timezone,
        )

        if result["success"]:
            logger.info(f"Scheduled safety checkup for user {user_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        logger.error(f"Error scheduling safety checkup for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkup/schedules")
async def get_safety_checkup_schedules(
    active_only: bool = Query(True, description="Only return active schedules"),
    user_id: str = Depends(get_current_user_id),
):
    """Get all safety checkup schedules for a user. JWT secured - user can only see their own schedules."""
    try:
        schedules = await safety_scheduler.get_user_safety_schedules(
            user_id=user_id, active_only=active_only
        )

        return {"schedules": schedules, "count": len(schedules)}

    except Exception as e:
        logger.error(f"Error getting safety schedules for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/checkup/schedules/{schedule_id}")
async def cancel_safety_checkup(
    schedule_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel a safety checkup schedule. JWT secured - user can only cancel their own schedules."""
    try:
        result = await safety_scheduler.cancel_safety_checkup(
            user_id=user_id, schedule_id=schedule_id, reason=reason
        )

        if result["success"]:
            logger.info(f"Cancelled safety schedule {schedule_id} for user {user_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(
            f"Error cancelling safety schedule {schedule_id} for user {user_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PRIORITY MANAGEMENT
# =============================================================================


@router.put("/contacts/{contact_id}/priority")
async def update_contact_priority(
    contact_id: str,
    request: UpdateContactPriorityRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Update the priority order for a specific safety contact.
    """
    try:
        success = SafetyNetworkManager.update_safety_contact(
            contact_id=contact_id,
            user_id=user_id,
            priority_order=request.priority_order,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")

        return {
            "success": True,
            "message": "Contact priority updated successfully",
            "contact_id": contact_id,
            "priority_order": request.priority_order,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact priority: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/contacts/reorder")
async def reorder_safety_contacts(
    request: ReorderContactsRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Reorder multiple safety contacts by updating their priority values.
    """
    try:
        success = SafetyNetworkManager.reorder_contacts(
            user_id=user_id,
            contact_priorities=request.contact_priorities,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to reorder contacts")

        return {
            "success": True,
            "message": f"Successfully reordered {len(request.contact_priorities)} contacts",
            "updated_contacts": len(request.contact_priorities),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering contacts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
