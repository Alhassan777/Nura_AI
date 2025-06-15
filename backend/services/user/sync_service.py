"""
User Synchronization Service
Handles synchronization between Supabase Auth and backend user database.
Provides real-time sync, conflict resolution, and error handling.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import json

# Import from unified models to get the updated User with gamification fields
from models import User, UserServiceProfile, UserSyncLog, ServiceType
from .database import get_db
from utils.database import get_db_context
from ..memory.config import Config

logger = logging.getLogger(__name__)


def make_json_safe(data: Any) -> Any:
    """Convert data to JSON-safe format by handling datetime objects."""
    if data is None:
        return None
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, uuid.UUID):
        return str(data)
    elif isinstance(data, dict):
        return {key: make_json_safe(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_json_safe(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(make_json_safe(item) for item in data)
    else:
        return data


def to_uuid(value: str) -> uuid.UUID:
    """Convert string to UUID object safely."""
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        return uuid.UUID(value)
    raise ValueError(f"Cannot convert {type(value)} to UUID")


class UserSyncService:
    """
    Service to synchronize user data between Supabase Auth and backend database.
    Handles both real-time updates and batch synchronization.
    """

    def __init__(self):
        self.logger = logger

    async def sync_user_from_supabase(
        self,
        supabase_user_data: Dict[str, Any],
        source: str = "supabase_auth",
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sync user from Supabase Auth to backend database.

        Args:
            supabase_user_data: User data from Supabase Auth
            source: Source of the sync operation
            session_id: Optional session ID for tracking
            request_id: Optional request ID for tracing

        Returns:
            Dict with sync result and user data
        """
        with get_db_context() as db:
            try:
                user_id_str = supabase_user_data.get("id")
                if not user_id_str:
                    raise ValueError("User ID is required for sync")

                # Convert user_id to UUID object
                user_id = to_uuid(user_id_str)

                # Check if user exists in backend
                existing_user = db.query(User).filter(User.id == user_id).first()

                if existing_user:
                    # Update existing user
                    result = await self._update_existing_user(
                        db,
                        existing_user,
                        supabase_user_data,
                        source,
                        session_id,
                        request_id,
                    )
                else:
                    # Create new user
                    result = await self._create_new_user(
                        db, supabase_user_data, source, session_id, request_id
                    )

                return result

            except Exception as e:
                self.logger.error(f"Failed to sync user {user_id_str}: {str(e)}")

                # Only log sync failure if we have a valid user_id and the user exists
                try:
                    if user_id_str:
                        user_uuid = to_uuid(user_id_str)
                        existing_user = (
                            db.query(User).filter(User.id == user_uuid).first()
                        )
                        if existing_user:
                            await self._log_sync_operation(
                                db,
                                user_id_str,
                                "create_or_update",
                                source,
                                supabase_user_data,
                                None,
                                False,
                                str(e),
                                session_id,
                                request_id,
                            )
                except Exception as log_error:
                    self.logger.error(f"Failed to log sync error: {str(log_error)}")

                return {"success": False, "error": str(e), "user_id": user_id_str}

    async def _create_new_user(
        self,
        db: Session,
        supabase_user_data: Dict[str, Any],
        source: str,
        session_id: Optional[str],
        request_id: Optional[str],
    ) -> Dict[str, Any]:
        """Create a new user in backend database."""

        user_id_str = supabase_user_data["id"]
        user_id = to_uuid(user_id_str)

        try:
            # Extract user data from Supabase format
            user_data = self._extract_user_data(supabase_user_data)

            # Double-check if user already exists with same ID (handle race conditions)
            existing_user = db.query(User).filter(User.id == user_id).first()
            if existing_user:
                # User was created by another process with same ID, update instead
                return await self._update_existing_user(
                    db,
                    existing_user,
                    supabase_user_data,
                    source,
                    session_id,
                    request_id,
                )

            # Check for existing user with same email (handle email conflicts)
            existing_by_email = (
                db.query(User).filter(User.email == user_data["email"]).first()
            )
            if existing_by_email:
                # Email already exists with different ID - this can happen if user
                # created account before, got deleted, and signed up again with same email
                self.logger.warning(
                    f"User with email {user_data['email']} already exists with different ID {existing_by_email.id}, deleting old user and creating new one"
                )

                # Delete the old user and create fresh with correct ID
                # This ensures JWT tokens work correctly
                db.delete(existing_by_email)
                db.flush()  # Ensure deletion happens before creating new user

                # Continue with creating new user with correct ID
                pass

            # Create new user with all required fields
            new_user = User(
                id=user_id,  # Use UUID object
                email=user_data["email"],
                phone_number=user_data.get("phone"),
                full_name=user_data.get("full_name"),
                display_name=user_data.get("display_name"),
                bio=user_data.get("bio"),
                avatar_url=user_data.get("avatar_url"),
                email_confirmed_at=user_data.get("email_confirmed_at"),
                phone_confirmed_at=user_data.get("phone_confirmed_at"),
                last_sign_in_at=user_data.get("last_sign_in_at"),
                # Set defaults for new users including gamification fields
                is_active=True,
                current_streak=0,
                xp=0,
                freeze_credits=3,  # Default freeze credits
                last_activity=None,  # No activity yet
                privacy_settings={},
            )

            db.add(new_user)

            # Create default service profiles for essential services
            await self._create_default_service_profiles(db, user_id_str)

            db.commit()

            # Log successful sync (with JSON-safe data) - now user exists in DB
            await self._log_sync_operation(
                db,
                user_id_str,
                "create",
                source,
                None,
                self._user_to_dict(new_user),
                True,
                None,
                session_id,
                request_id,
            )

            self.logger.info(f"Successfully created new user: {user_id_str}")

            return {
                "success": True,
                "action": "created",
                "user": self._user_to_dict(new_user),
                "user_id": user_id_str,
            }

        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"SQLAlchemy error creating user {user_id_str}: {str(e)}")

            # If it's a duplicate key error, try to handle it gracefully
            if (
                "duplicate key" in str(e).lower()
                or "unique constraint" in str(e).lower()
            ):
                # Try to get the existing user and update instead
                existing_user = db.query(User).filter(User.id == user_id).first()
                if existing_user:
                    self.logger.info(
                        f"User {user_id_str} already exists, updating instead"
                    )
                    return await self._update_existing_user(
                        db,
                        existing_user,
                        supabase_user_data,
                        source,
                        session_id,
                        request_id,
                    )

            raise e

    async def _update_existing_user(
        self,
        db: Session,
        existing_user: User,
        supabase_user_data: Dict[str, Any],
        source: str,
        session_id: Optional[str],
        request_id: Optional[str],
    ) -> Dict[str, Any]:
        """Update existing user with data from Supabase."""

        user_id_str = str(existing_user.id)
        before_data = self._user_to_dict(existing_user)

        try:
            # Extract updated user data
            user_data = self._extract_user_data(supabase_user_data)

            # Track what fields changed
            changes = {}

            # Update core fields that can be synced from Supabase
            if user_data["email"] != existing_user.email:
                changes["email"] = {
                    "from": existing_user.email,
                    "to": user_data["email"],
                }
                existing_user.email = user_data["email"]

            if user_data.get("phone") != existing_user.phone_number:
                changes["phone_number"] = {
                    "from": existing_user.phone_number,
                    "to": user_data.get("phone"),
                }
                existing_user.phone_number = user_data.get("phone")

            # Update Supabase Auth metadata
            if user_data.get("email_confirmed_at") != existing_user.email_confirmed_at:
                existing_user.email_confirmed_at = user_data.get("email_confirmed_at")
                changes["email_confirmed_at"] = {"updated": True}

            if user_data.get("phone_confirmed_at") != existing_user.phone_confirmed_at:
                existing_user.phone_confirmed_at = user_data.get("phone_confirmed_at")
                changes["phone_confirmed_at"] = {"updated": True}

            if user_data.get("last_sign_in_at") != existing_user.last_sign_in_at:
                existing_user.last_sign_in_at = user_data.get("last_sign_in_at")
                existing_user.last_active_at = datetime.utcnow()
                changes["last_sign_in_at"] = {"updated": True}

            # Only update full_name if it's provided and different
            if (
                user_data.get("full_name")
                and user_data["full_name"] != existing_user.full_name
            ):
                changes["full_name"] = {
                    "from": existing_user.full_name,
                    "to": user_data["full_name"],
                }
                existing_user.full_name = user_data["full_name"]

            if changes:
                existing_user.updated_at = datetime.utcnow()
                db.commit()

                after_data = self._user_to_dict(existing_user)

                # Log successful sync
                await self._log_sync_operation(
                    db,
                    user_id_str,
                    "update",
                    source,
                    before_data,
                    after_data,
                    True,
                    None,
                    session_id,
                    request_id,
                )

                self.logger.info(
                    f"Successfully updated user {user_id_str}: {list(changes.keys())}"
                )

                return {
                    "success": True,
                    "action": "updated",
                    "changes": changes,
                    "user": after_data,
                    "user_id": user_id_str,
                }
            else:
                self.logger.debug(f"No changes needed for user: {user_id_str}")
                return {
                    "success": True,
                    "action": "no_changes",
                    "user": before_data,
                    "user_id": user_id_str,
                }

        except SQLAlchemyError as e:
            db.rollback()
            raise e

    async def _create_default_service_profiles(self, db: Session, user_id: str):
        """Create default service profiles for a new user."""

        default_services = [
            ServiceType.CHAT.value,
            ServiceType.GAMIFICATION.value,
            ServiceType.MEMORY.value,
        ]

        user_uuid = to_uuid(user_id)

        for service_type in default_services:
            profile = UserServiceProfile(
                user_id=user_uuid,  # Use UUID object
                service_type=service_type,
                service_preferences={},
                service_metadata={},
                usage_stats={"created_at": datetime.utcnow().isoformat()},
            )
            db.add(profile)

    def _extract_user_data(self, supabase_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize user data from Supabase Auth format."""

        # Handle different Supabase Auth response formats
        user_metadata = supabase_user_data.get("user_metadata", {})
        app_metadata = supabase_user_data.get("app_metadata", {})

        # Parse timestamps
        email_confirmed_at = None
        if supabase_user_data.get("email_confirmed_at"):
            email_confirmed_value = supabase_user_data["email_confirmed_at"]
            if isinstance(email_confirmed_value, datetime):
                email_confirmed_at = email_confirmed_value
            else:
                email_confirmed_at = datetime.fromisoformat(
                    email_confirmed_value.replace("Z", "+00:00")
                )

        phone_confirmed_at = None
        if supabase_user_data.get("phone_confirmed_at"):
            phone_confirmed_value = supabase_user_data["phone_confirmed_at"]
            if isinstance(phone_confirmed_value, datetime):
                phone_confirmed_at = phone_confirmed_value
            else:
                phone_confirmed_at = datetime.fromisoformat(
                    phone_confirmed_value.replace("Z", "+00:00")
                )

        last_sign_in_at = None
        if supabase_user_data.get("last_sign_in_at"):
            last_sign_in_value = supabase_user_data["last_sign_in_at"]
            if isinstance(last_sign_in_value, datetime):
                last_sign_in_at = last_sign_in_value
            else:
                last_sign_in_at = datetime.fromisoformat(
                    last_sign_in_value.replace("Z", "+00:00")
                )

        extracted_data = {
            "email": supabase_user_data["email"],
            "phone": supabase_user_data.get("phone"),
            "full_name": user_metadata.get("full_name") or user_metadata.get("name"),
            "display_name": user_metadata.get("display_name"),
            "bio": user_metadata.get("bio"),
            "avatar_url": user_metadata.get("avatar_url"),
            "email_confirmed_at": email_confirmed_at,
            "phone_confirmed_at": phone_confirmed_at,
            "last_sign_in_at": last_sign_in_at,
        }

        return extracted_data

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User model to dictionary for logging and responses."""

        def safe_isoformat(dt):
            """Safely convert datetime to ISO format string."""
            if dt is None:
                return None
            if isinstance(dt, (datetime, date)):
                return dt.isoformat()
            return dt

        return {
            "id": str(user.id),  # Ensure UUID is serialized as string
            "email": user.email,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "display_name": user.display_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            # Gamification fields
            "current_streak": user.current_streak,
            "xp": user.xp,
            "freeze_credits": getattr(
                user, "freeze_credits", 3
            ),  # Default if not present
            "last_activity": safe_isoformat(getattr(user, "last_activity", None)),
            # Timestamps - ensure all are properly serialized
            "created_at": safe_isoformat(user.created_at),
            "updated_at": safe_isoformat(user.updated_at),
            "last_active_at": safe_isoformat(user.last_active_at),
            "email_confirmed_at": safe_isoformat(user.email_confirmed_at),
            "phone_confirmed_at": safe_isoformat(user.phone_confirmed_at),
            "last_sign_in_at": safe_isoformat(user.last_sign_in_at),
            "deleted_at": safe_isoformat(user.deleted_at),
            # Settings
            "privacy_settings": user.privacy_settings or {},
        }

    async def _log_sync_operation(
        self,
        db: Session,
        user_id: Optional[str],
        sync_type: str,
        source: str,
        before_data: Optional[Dict[str, Any]],
        after_data: Optional[Dict[str, Any]],
        success: bool,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        """Log synchronization operation for debugging and auditing."""

        try:
            # Convert data to JSON-safe format
            safe_before_data = make_json_safe(before_data) if before_data else None
            safe_after_data = make_json_safe(after_data) if after_data else None

            # Convert user_id to UUID if provided
            user_uuid = None
            if user_id:
                try:
                    user_uuid = to_uuid(user_id)
                except ValueError:
                    self.logger.warning(
                        f"Invalid user_id format for logging: {user_id}"
                    )
                    user_uuid = None

            sync_log = UserSyncLog(
                user_id=user_uuid,  # Use UUID object or None
                sync_type=sync_type,
                source=source,
                before_data=safe_before_data,
                after_data=safe_after_data,
                success=success,
                error_message=error_message,
                session_id=session_id,
                request_id=request_id,
            )

            db.add(sync_log)
            db.commit()

        except Exception as e:
            self.logger.error(f"Failed to log sync operation: {str(e)}")
            # Don't re-raise as this is just logging

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from backend database."""

        with get_db_context() as db:
            try:
                user_uuid = to_uuid(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if user:
                    return self._user_to_dict(user)
                return None

            except SQLAlchemyError as e:
                self.logger.error(f"Failed to get user {user_id}: {str(e)}")
                return None

    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        source: str = "backend_api",
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update user profile data from backend."""

        with get_db_context() as db:
            try:
                user_uuid = to_uuid(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if not user:
                    return {
                        "success": False,
                        "error": "User not found",
                        "user_id": user_id,
                    }

                before_data = self._user_to_dict(user)
                changes = {}

                # Update allowed profile fields
                updatable_fields = [
                    "full_name",
                    "display_name",
                    "bio",
                    "avatar_url",
                    "privacy_settings",
                ]

                for field in updatable_fields:
                    if field in profile_data:
                        old_value = getattr(user, field)
                        new_value = profile_data[field]

                        if old_value != new_value:
                            setattr(user, field, new_value)
                            changes[field] = {"from": old_value, "to": new_value}

                if changes:
                    user.updated_at = datetime.utcnow()
                    db.commit()

                    after_data = self._user_to_dict(user)

                    # Log the update
                    await self._log_sync_operation(
                        db,
                        user_id,
                        "profile_update",
                        source,
                        before_data,
                        after_data,
                        True,
                        None,
                        session_id,
                        request_id,
                    )

                    return {
                        "success": True,
                        "action": "updated",
                        "changes": changes,
                        "user": after_data,
                        "user_id": user_id,
                    }
                else:
                    return {
                        "success": True,
                        "action": "no_changes",
                        "user": before_data,
                        "user_id": user_id,
                    }

            except SQLAlchemyError as e:
                db.rollback()
                self.logger.error(f"Failed to update user profile {user_id}: {str(e)}")
                return {"success": False, "error": str(e), "user_id": user_id}

    async def get_service_profile(
        self, user_id: str, service_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's service-specific profile."""

        with get_db_context() as db:
            try:
                user_uuid = to_uuid(user_id)
                profile = (
                    db.query(UserServiceProfile)
                    .filter(
                        UserServiceProfile.user_id == user_uuid,
                        UserServiceProfile.service_type == service_type,
                    )
                    .first()
                )

                if profile:
                    return {
                        "id": profile.id,
                        "user_id": str(
                            profile.user_id
                        ),  # Convert UUID back to string for response
                        "service_type": profile.service_type,
                        "service_preferences": profile.service_preferences,
                        "service_metadata": profile.service_metadata,
                        "usage_stats": profile.usage_stats,
                        "last_used_at": (
                            profile.last_used_at.isoformat()
                            if profile.last_used_at
                            else None
                        ),
                    }
                return None

            except SQLAlchemyError as e:
                self.logger.error(
                    f"Failed to get service profile {user_id}/{service_type}: {str(e)}"
                )
                return None

    async def health_check(self) -> bool:
        """Health check for sync service - tests database connectivity and basic operations."""
        try:
            with get_db_context() as db:
                # Test basic database operation
                db.execute("SELECT 1")

                # Test if we can query users table structure
                db.execute("SELECT count(*) FROM users")

                return True

        except Exception as e:
            self.logger.error(f"Sync service health check failed: {str(e)}")
            return False


# Global sync service instance
sync_service = UserSyncService()
