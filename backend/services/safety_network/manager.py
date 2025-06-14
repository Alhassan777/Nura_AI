"""
Safety Network Manager for Nura Mental Health Application.

Manages safety contacts, emergency contacts, and communication tracking.
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .database import get_db
from models import SafetyContact, ContactLog, CommunicationMethod, User

logger = logging.getLogger(__name__)


class SafetyNetworkManager:
    """Manages safety network contacts for users."""

    @staticmethod
    def add_safety_contact(
        user_id: str,
        priority_order: int,
        allowed_communication_methods: List[str],
        preferred_communication_method: str,
        relationship_type: Optional[str] = None,
        notes: Optional[str] = None,
        preferred_contact_time: Optional[str] = None,
        timezone: str = "UTC",
        is_emergency_contact: bool = False,
        custom_metadata: Optional[Dict[str, Any]] = None,
        # For existing users in system
        contact_user_id: Optional[str] = None,
        # For external contacts (not in our system)
        external_first_name: Optional[str] = None,
        external_last_name: Optional[str] = None,
        external_phone_number: Optional[str] = None,
        external_email: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add a new safety contact for a user.

        Contact can be either:
        1. An existing user (provide contact_user_id)
        2. An external contact (provide external_* fields)

        Returns:
            Contact ID if successful, None if failed
        """
        try:
            with get_db() as db:
                # Validate communication methods
                valid_methods = [method.value for method in CommunicationMethod]
                if not all(
                    method in valid_methods for method in allowed_communication_methods
                ):
                    logger.error(
                        f"Invalid communication methods: {allowed_communication_methods}"
                    )
                    return None

                # Validate that we have either contact_user_id OR external contact info
                if contact_user_id:
                    # Verify the contact user exists in central database
                    contact_user = (
                        db.query(User).filter(User.id == contact_user_id).first()
                    )
                    if not contact_user:
                        logger.error(
                            f"Contact user {contact_user_id} not found in central database"
                        )
                        return None
                elif not (
                    external_first_name and (external_phone_number or external_email)
                ):
                    logger.error(
                        "Must provide either contact_user_id or external contact info"
                    )
                    return None

                # Validate preferred method is in allowed methods
                if preferred_communication_method not in allowed_communication_methods:
                    logger.error(
                        f"Preferred method {preferred_communication_method} not in allowed methods"
                    )
                    return None

                # Create safety contact
                contact = SafetyContact(
                    user_id=user_id,
                    contact_user_id=contact_user_id,
                    external_first_name=external_first_name,
                    external_last_name=external_last_name,
                    external_phone_number=external_phone_number,
                    external_email=external_email,
                    allowed_communication_methods=allowed_communication_methods,
                    preferred_communication_method=preferred_communication_method,
                    priority_order=priority_order,
                    relationship_type=relationship_type,
                    notes=notes,
                    preferred_contact_time=preferred_contact_time,
                    timezone=timezone,
                    is_emergency_contact=is_emergency_contact,
                    custom_metadata=custom_metadata,
                )

                db.add(contact)
                db.commit()  # Commit the transaction to save the contact

                logger.info(f"Added safety contact {contact.id} for user {user_id}")
                return contact.id

        except Exception as e:
            logger.error(f"Error adding safety contact: {e}")
            return None

    @staticmethod
    def get_user_safety_contacts(
        user_id: str,
        active_only: bool = True,
        emergency_only: bool = False,
        ordered_by_priority: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all safety contacts for a user with resolved contact information.

        Returns enriched contact data with actual names, emails, phones from central user DB.
        """
        try:
            with get_db() as db:
                query = db.query(SafetyContact).filter(SafetyContact.user_id == user_id)

                if active_only:
                    query = query.filter(SafetyContact.is_active == True)

                if emergency_only:
                    query = query.filter(SafetyContact.is_emergency_contact == True)

                if ordered_by_priority:
                    query = query.order_by(SafetyContact.priority_order.asc())
                else:
                    query = query.order_by(SafetyContact.created_at.desc())

                contacts = query.all()

                # Enrich contacts with user data from central database
                enriched_contacts = []
                for contact in contacts:
                    enriched_contact = SafetyNetworkManager._enrich_contact_data(
                        contact, db
                    )
                    enriched_contacts.append(enriched_contact)

                return enriched_contacts

        except Exception as e:
            logger.error(f"Error getting safety contacts: {e}")
            return []

    @staticmethod
    def _enrich_contact_data(contact: SafetyContact, db) -> Dict[str, Any]:
        """
        Enrich safety contact with user data from central database.
        """
        contact_data = {
            "id": contact.id,
            "user_id": contact.user_id,
            "contact_user_id": contact.contact_user_id,
            "priority_order": contact.priority_order,
            "allowed_communication_methods": contact.allowed_communication_methods,
            "preferred_communication_method": contact.preferred_communication_method,
            "relationship_type": contact.relationship_type,
            "notes": contact.notes,
            "preferred_contact_time": contact.preferred_contact_time,
            "timezone": contact.timezone,
            "is_active": contact.is_active,
            "is_emergency_contact": contact.is_emergency_contact,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "last_contacted_at": contact.last_contacted_at,
            "last_contact_method": contact.last_contact_method,
            "last_contact_successful": contact.last_contact_successful,
        }

        # Get contact details
        if contact.contact_user_id:
            # Contact is a user in our system - get data from central user DB
            try:
                contact_user = (
                    db.query(User).filter(User.id == contact.contact_user_id).first()
                )
                if contact_user:
                    # Extract all data immediately while in session
                    contact_data.update(
                        {
                            "first_name": contact_user.first_name,
                            "last_name": contact_user.last_name,
                            "phone_number": contact_user.phone_number,
                            "email": contact_user.email,
                            "full_name": contact_user.full_name,
                        }
                    )
                else:
                    logger.warning(
                        f"Contact user {contact.contact_user_id} not found in central database"
                    )
                    contact_data.update(
                        {
                            "first_name": f"User {contact.contact_user_id}",
                            "last_name": "",
                            "phone_number": None,
                            "email": None,
                            "full_name": f"User {contact.contact_user_id}",
                        }
                    )
            except Exception as e:
                logger.error(f"Error fetching contact user data: {e}")
                contact_data.update(
                    {
                        "first_name": f"User {contact.contact_user_id}",
                        "last_name": "",
                        "phone_number": None,
                        "email": None,
                        "full_name": f"User {contact.contact_user_id}",
                    }
                )
        else:
            # External contact - use stored external data
            contact_data.update(
                {
                    "first_name": contact.external_first_name,
                    "last_name": contact.external_last_name,
                    "phone_number": contact.external_phone_number,
                    "email": contact.external_email,
                    "full_name": f"{contact.external_first_name or ''} {contact.external_last_name or ''}".strip(),
                }
            )

        return contact_data

    @staticmethod
    def get_emergency_contacts(user_id: str) -> List[Dict[str, Any]]:
        """Get emergency contacts for a user, ordered by priority."""
        return SafetyNetworkManager.get_user_safety_contacts(
            user_id=user_id,
            active_only=True,
            emergency_only=True,
            ordered_by_priority=True,
        )

    @staticmethod
    def update_safety_contact(contact_id: str, user_id: str, **updates) -> bool:
        """Update an existing safety contact."""
        try:
            with get_db() as db:
                contact = (
                    db.query(SafetyContact)
                    .filter(
                        SafetyContact.id == contact_id, SafetyContact.user_id == user_id
                    )
                    .first()
                )

                if not contact:
                    logger.warning(
                        f"Safety contact {contact_id} not found for user {user_id}"
                    )
                    return False

                # Update fields
                for field, value in updates.items():
                    if hasattr(contact, field):
                        setattr(contact, field, value)

                contact.updated_at = datetime.utcnow()

                db.commit()  # Commit the transaction to save changes

                logger.info(f"Updated safety contact {contact_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating safety contact: {e}")
            return False

    @staticmethod
    def remove_safety_contact(contact_id: str, user_id: str) -> bool:
        """Remove a safety contact."""
        try:
            with get_db() as db:
                contact = (
                    db.query(SafetyContact)
                    .filter(
                        SafetyContact.id == contact_id, SafetyContact.user_id == user_id
                    )
                    .first()
                )

                if not contact:
                    logger.warning(
                        f"Safety contact {contact_id} not found for user {user_id}"
                    )
                    return False

                db.delete(contact)
                db.commit()  # Commit the transaction to save changes
                logger.info(f"Removed safety contact {contact_id}")
                return True

        except Exception as e:
            logger.error(f"Error removing safety contact: {e}")
            return False

    @staticmethod
    def deactivate_safety_contact(contact_id: str, user_id: str) -> bool:
        """Deactivate a safety contact instead of deleting it."""
        return SafetyNetworkManager.update_safety_contact(
            contact_id=contact_id, user_id=user_id, is_active=False
        )

    @staticmethod
    def log_contact_attempt(
        safety_contact_id: str,
        user_id: str,
        contact_method: str,
        success: bool,
        reason: str,
        initiated_by: str,
        message_content: Optional[str] = None,
        error_message: Optional[str] = None,
        response_received: Optional[bool] = None,
        response_time_minutes: Optional[int] = None,
        response_summary: Optional[str] = None,
        contact_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log a contact attempt with a safety network contact."""
        try:
            with get_db() as db:
                contact_log = ContactLog(
                    safety_contact_id=safety_contact_id,
                    user_id=user_id,
                    contact_method=contact_method,
                    success=success,
                    reason=reason,
                    initiated_by=initiated_by,
                    message_content=message_content,
                    error_message=error_message,
                    response_received=response_received,
                    response_time_minutes=response_time_minutes,
                    response_summary=response_summary,
                    contact_metadata=contact_metadata,
                )

                db.add(contact_log)

                # Update the safety contact's last contact info
                safety_contact = (
                    db.query(SafetyContact)
                    .filter(SafetyContact.id == safety_contact_id)
                    .first()
                )
                if safety_contact:
                    safety_contact.last_contacted_at = datetime.utcnow()
                    safety_contact.last_contact_method = contact_method
                    safety_contact.last_contact_successful = success

                db.commit()  # Commit the transaction to save changes

                logger.info(
                    f"Logged contact attempt for safety contact {safety_contact_id}: {success}"
                )
                return True

        except Exception as e:
            logger.error(f"Error logging contact attempt: {e}")
            return False

    @staticmethod
    def get_contact_history(
        user_id: str, safety_contact_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get contact history for a user or specific contact."""
        try:
            with get_db() as db:
                query = db.query(ContactLog).filter(ContactLog.user_id == user_id)

                if safety_contact_id:
                    query = query.filter(
                        ContactLog.safety_contact_id == safety_contact_id
                    )

                contact_logs = (
                    query.order_by(ContactLog.attempted_at.desc()).limit(limit).all()
                )

                # Convert ORM objects to dictionaries to avoid session binding issues
                history_data = []
                for log in contact_logs:
                    history_data.append(
                        {
                            "id": log.id,
                            "safety_contact_id": log.safety_contact_id,
                            "user_id": log.user_id,
                            "attempted_at": log.attempted_at,
                            "contact_method": log.contact_method,
                            "success": log.success,
                            "reason": log.reason,
                            "initiated_by": log.initiated_by,
                            "response_received": log.response_received,
                            "response_time_minutes": log.response_time_minutes,
                            "response_summary": log.response_summary,
                            "message_content": log.message_content,
                            "error_message": log.error_message,
                            "contact_metadata": log.contact_metadata,
                        }
                    )

                return history_data

        except Exception as e:
            logger.error(f"Error getting contact history: {e}")
            return []

    @staticmethod
    def reorder_contacts(user_id: str, contact_priorities: Dict[str, int]) -> bool:
        """
        Reorder safety contacts by updating their priority values.

        Args:
            user_id: User ID
            contact_priorities: Dict mapping contact_id to new priority order
        """
        try:
            with get_db() as db:
                for contact_id, new_priority in contact_priorities.items():
                    contact = (
                        db.query(SafetyContact)
                        .filter(
                            SafetyContact.id == contact_id,
                            SafetyContact.user_id == user_id,
                        )
                        .first()
                    )

                    if contact:
                        contact.priority_order = new_priority
                        contact.updated_at = datetime.utcnow()

                db.commit()  # Commit the transaction to save changes

                logger.info(
                    f"Reordered {len(contact_priorities)} contacts for user {user_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Error reordering contacts: {e}")
            return False
