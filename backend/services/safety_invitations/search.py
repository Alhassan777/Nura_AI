"""
User Search and Discovery for Safety Network Invitations.

Provides secure user search functionality with privacy protections and blocking system.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_, Boolean

from .database import get_db, get_db_context_local
from models import User, SafetyNetworkRequest, SafetyContact, UserBlock

logger = logging.getLogger(__name__)


class UserSearch:
    """Handles user search and discovery for safety network invitations with privacy controls."""

    @staticmethod
    def search_users(
        searching_user_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for users by email, full name, or display name.
        Respects user privacy settings for discoverability and invitation preferences.
        Includes blocking system and invitation eligibility checking.

        Args:
            searching_user_id: ID of user performing the search
            query: Search query (email, name, etc.)
            limit: Maximum number of results

        Returns:
            List of user dictionaries with safe information and invitation eligibility
        """
        try:
            with get_db_context_local() as db:
                # 1. Check if searching user is blocked from discovery by anyone
                blocked_from_discovery = (
                    db.query(UserBlock)
                    .filter(
                        and_(
                            UserBlock.blocked_user_id == searching_user_id,
                            UserBlock.block_type.in_(["discovery", "all"]),
                        )
                    )
                    .all()
                )

                blocked_user_ids = [
                    block.blocking_user_id for block in blocked_from_discovery
                ]

                # 2. Build privacy-aware search conditions
                search_conditions = []

                # Check if query looks like an email for exact email search
                is_email_search = "@" in query and "." in query.split("@")[-1]

                if is_email_search:
                    # Email search - only return if user allows email discovery
                    search_conditions.append(
                        and_(
                            User.email.ilike(f"%{query}%"),
                            User.privacy_settings["safety_network_privacy"][
                                "discoverability"
                            ]["can_be_found_by_email"].astext.cast(Boolean)
                            == True,
                        )
                    )
                else:
                    # Name search - only return if user allows name discovery
                    search_conditions.append(
                        and_(
                            or_(
                                User.full_name.ilike(f"%{query}%"),
                                User.display_name.ilike(f"%{query}%"),
                            ),
                            User.privacy_settings["safety_network_privacy"][
                                "discoverability"
                            ]["can_be_found_by_name"].astext.cast(Boolean)
                            == True,
                        )
                    )

                # 3. Execute base user query with privacy filtering
                search_query = (
                    db.query(User)
                    .filter(
                        and_(
                            User.id != searching_user_id,  # Don't return self
                            User.is_active == True,  # Only active accounts
                            (
                                User.id.notin_(blocked_user_ids)
                                if blocked_user_ids
                                else True
                            ),  # Exclude users who blocked searcher
                            # Privacy: Can accept invitations
                            User.privacy_settings["safety_network_privacy"][
                                "invitation_controls"
                            ]["accept_invitations"].astext.cast(Boolean)
                            == True,
                            # Privacy: Searchability settings
                            or_(*search_conditions) if search_conditions else False,
                        )
                    )
                    .limit(limit)
                )

                users = search_query.all()

                # 4. Get existing relationships to exclude from results
                existing_requests = UserSearch._get_existing_relationships(
                    db, searching_user_id
                )

                # 5. Format results with privacy protection and invitation capability
                results = []
                for user in users:
                    # Skip users with existing relationships
                    if user.id in existing_requests:
                        continue

                    # Check detailed invitation eligibility
                    eligibility = UserSearch.check_invitation_eligibility(
                        searching_user_id, user.id, db
                    )

                    user_data = {
                        "id": str(user.id),
                        "email": (
                            user.email if is_email_search else None
                        ),  # Only show email for email searches
                        "full_name": user.full_name,
                        "display_name": user.display_name,
                        "avatar_url": user.avatar_url,
                        "verification_status": (
                            "verified" if user.is_verified else "unverified"
                        ),
                        # Invitation eligibility
                        "can_invite": eligibility["can_invite"],
                        "invitation_hint": eligibility.get("user_message", ""),
                        "privacy_level": UserSearch._get_user_privacy_level(user),
                    }
                    results.append(user_data)

                logger.info(
                    f"User search by {searching_user_id}: {len(results)} results for '{query}'"
                )
                return results

        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    @staticmethod
    def check_invitation_eligibility(
        sender_id: str, recipient_id: str, db=None
    ) -> Dict[str, Any]:
        """
        Check if a user can be invited based on privacy settings and blocks.

        Args:
            sender_id: User wanting to send invitation
            recipient_id: User being invited
            db: Database session (optional)

        Returns:
            Dict with can_invite boolean and user_message
        """
        try:
            should_close_db = db is None
            if db is None:
                db = get_db().__enter__()

            try:
                # 1. Check if recipient has blocked sender
                is_blocked = (
                    db.query(UserBlock)
                    .filter(
                        and_(
                            UserBlock.blocking_user_id == recipient_id,
                            UserBlock.blocked_user_id == sender_id,
                            UserBlock.block_type.in_(["invitations", "all"]),
                        )
                    )
                    .first()
                )

                if is_blocked:
                    return {
                        "can_invite": False,
                        "reason_code": "BLOCKED",
                        "user_message": "This user is not accepting invitations from you",
                    }

                # 2. Get recipient's privacy settings
                recipient = db.query(User).filter(User.id == recipient_id).first()
                if not recipient:
                    return {
                        "can_invite": False,
                        "reason_code": "USER_NOT_FOUND",
                        "user_message": "User not found",
                    }

                privacy_settings = recipient.privacy_settings.get(
                    "safety_network_privacy", {}
                )
                invitation_controls = privacy_settings.get("invitation_controls", {})

                # 3. Check if accepting invitations
                if not invitation_controls.get("accept_invitations", True):
                    return {
                        "can_invite": False,
                        "reason_code": "NOT_ACCEPTING",
                        "user_message": "This user is not accepting safety network invitations",
                    }

                # 4. Check verification requirement
                if invitation_controls.get("require_verification", False):
                    sender = db.query(User).filter(User.id == sender_id).first()
                    if not sender or not sender.is_verified:
                        return {
                            "can_invite": False,
                            "reason_code": "VERIFICATION_REQUIRED",
                            "user_message": "Please verify your account to send invitations",
                        }

                # 5. Check searchability restrictions
                discoverability = privacy_settings.get("discoverability", {})
                searchable_by = discoverability.get("searchable_by", "everyone")

                if searchable_by == "nobody":
                    return {
                        "can_invite": False,
                        "reason_code": "NOT_DISCOVERABLE",
                        "user_message": "This user is not accepting invitations",
                    }
                elif searchable_by == "verified_users":
                    sender = db.query(User).filter(User.id == sender_id).first()
                    if not sender or not sender.is_verified:
                        return {
                            "can_invite": False,
                            "reason_code": "VERIFICATION_REQUIRED",
                            "user_message": "Please verify your account to send invitations",
                        }
                elif searchable_by == "mutual_connections":
                    if not UserSearch._have_mutual_connections(
                        recipient_id, sender_id, db
                    ):
                        return {
                            "can_invite": False,
                            "reason_code": "NO_MUTUAL_CONNECTIONS",
                            "user_message": "You need mutual connections to invite this user",
                        }

                # 6. All checks passed
                return {
                    "can_invite": True,
                    "reason_code": "ELIGIBLE",
                    "user_message": "You can send an invitation to this user",
                }

            finally:
                if should_close_db:
                    db.__exit__(None, None, None)

        except Exception as e:
            logger.error(f"Error checking invitation eligibility: {e}")
            return {
                "can_invite": True,  # Default to allowing on error
                "reason_code": "ERROR",
                "user_message": "Unable to verify invitation eligibility",
            }

    @staticmethod
    def _get_existing_relationships(db, user_id: str) -> Dict[str, str]:
        """
        Get existing relationships that should BLOCK sending new invitations.

        Business Rules:
        - BLOCK: Pending invitations (can't send duplicate)
        - BLOCK: Active safety contacts (relationship already exists)
        - ALLOW: Declined invitations (user can try again)
        - ALLOW: Accepted but removed contacts (relationship ended)

        Note: This only blocks outgoing requests and existing contacts.
        Incoming requests do NOT block sending invitations (allows bidirectional invitations).

        Returns:
            Dict mapping user_id to relationship status (only blocking relationships)
        """
        relationships = {}

        # 1. Check PENDING outgoing requests (blocks sending another invitation)
        pending_requests = (
            db.query(SafetyNetworkRequest)
            .filter(
                and_(
                    SafetyNetworkRequest.requester_id == user_id,
                    SafetyNetworkRequest.status
                    == "pending",  # Only pending, not accepted
                )
            )
            .all()
        )

        for request in pending_requests:
            relationships[request.requested_id] = "pending_request"

        # 2. Check ACTIVE safety contacts (blocks sending invitation to existing contacts)
        existing_contacts = (
            db.query(SafetyContact)
            .filter(
                and_(
                    SafetyContact.user_id == user_id,
                    SafetyContact.contact_user_id.isnot(None),
                    SafetyContact.is_active == True,  # Only active contacts
                )
            )
            .all()
        )

        for contact in existing_contacts:
            if contact.contact_user_id:
                relationships[contact.contact_user_id] = "existing_contact"

        # NOTE: We do NOT include:
        # - Declined invitations (user can try again)
        # - Accepted invitations without active safety contact (relationship was removed)
        # - Incoming requests (allows bidirectional invitations)

        return relationships

    @staticmethod
    def _have_mutual_connections(user1_id: str, user2_id: str, db) -> bool:
        """Check if two users have mutual safety network connections."""
        try:
            # Get safety contacts for both users
            user1_contacts = (
                db.query(SafetyContact.contact_user_id)
                .filter(
                    and_(
                        SafetyContact.user_id == user1_id,
                        SafetyContact.is_active == True,
                        SafetyContact.contact_user_id.isnot(None),
                    )
                )
                .all()
            )

            user2_contacts = (
                db.query(SafetyContact.contact_user_id)
                .filter(
                    and_(
                        SafetyContact.user_id == user2_id,
                        SafetyContact.is_active == True,
                        SafetyContact.contact_user_id.isnot(None),
                    )
                )
                .all()
            )

            user1_contact_ids = {contact[0] for contact in user1_contacts}
            user2_contact_ids = {contact[0] for contact in user2_contacts}

            # Check for mutual connections
            return bool(user1_contact_ids.intersection(user2_contact_ids))

        except Exception as e:
            logger.error(f"Error checking mutual connections: {e}")
            return False

    @staticmethod
    def _get_user_privacy_level(user: User) -> str:
        """Get user's privacy level for display."""
        try:
            privacy_settings = user.privacy_settings.get("safety_network_privacy", {})
            discoverability = privacy_settings.get("discoverability", {})
            searchable_by = discoverability.get("searchable_by", "everyone")

            if searchable_by == "everyone":
                return "open"
            elif searchable_by == "verified_users":
                return "verified_only"
            elif searchable_by == "mutual_connections":
                return "connections_only"
            else:
                return "private"

        except Exception:
            return "open"

    @staticmethod
    def check_user_exists(user_id: str) -> bool:
        """
        Check if a user exists and is active.

        Args:
            user_id: User ID to check

        Returns:
            True if user exists and is active
        """
        try:
            with get_db_context_local() as db:
                user = (
                    db.query(User)
                    .filter(
                        and_(
                            User.id == user_id,
                            User.is_active == True,
                        )
                    )
                    .first()
                )

                return user is not None

        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return False
