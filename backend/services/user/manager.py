"""
Central User Manager for CRUD operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid

from models import User, UserPrivacySettings
from .database import get_db
from utils.database import get_db_context

logger = logging.getLogger(__name__)


class UserManager:
    """Manages central user database operations."""

    @staticmethod
    def create_user(
        user_id: str,  # Supabase Auth UUID
        email: str,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        privacy_settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a new user in the central database using Supabase Auth ID.

        Returns:
            User ID if successful, None if failed
        """
        try:
            with get_db_context() as db:
                # Check if user already exists
                existing_user = db.query(User).filter(User.id == user_id).first()
                if existing_user:
                    logger.warning(f"User with ID {user_id} already exists")
                    return None

                # Create new user with normalized schema
                user = User(
                    id=user_id,  # Use Supabase Auth UUID directly
                    email=email,
                    full_name=full_name,
                    phone_number=phone_number,
                    privacy_settings=privacy_settings or {},
                    last_active_at=datetime.utcnow(),
                )

                db.add(user)
                db.flush()  # Get the ID

                # Create default privacy settings
                privacy_settings_obj = UserPrivacySettings(
                    user_id=user.id,
                    consent_version="1.0",
                    consent_date=datetime.utcnow(),
                )
                db.add(privacy_settings_obj)

                logger.info(f"Created user {user.id} with email {email}")
                return user.id

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            with get_db_context() as db:
                return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        try:
            with get_db_context() as db:
                return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    @staticmethod
    def update_user(user_id: str, **updates) -> bool:
        """Update user information."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found")
                    return False

                # Update fields
                for field, value in updates.items():
                    if hasattr(user, field):
                        setattr(user, field, value)

                user.updated_at = datetime.utcnow()
                logger.info(f"Updated user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    @staticmethod
    def update_last_active(user_id: str) -> bool:
        """Update user's last active timestamp."""
        return UserManager.update_user(user_id, last_active_at=datetime.utcnow())

    @staticmethod
    def deactivate_user(user_id: str) -> bool:
        """Deactivate a user account."""
        return UserManager.update_user(user_id, is_active=False)

    @staticmethod
    def verify_user_email(user_id: str) -> bool:
        """Mark user's email as verified."""
        return UserManager.update_user(user_id, email_confirmed_at=datetime.utcnow())

    @staticmethod
    def verify_user_phone(user_id: str) -> bool:
        """Mark user's phone as verified."""
        return UserManager.update_user(user_id, phone_confirmed_at=datetime.utcnow())

    @staticmethod
    def get_all_users(
        active_only: bool = True, limit: int = 100, offset: int = 0
    ) -> List[User]:
        """Get list of users with pagination."""
        try:
            with get_db_context() as db:
                query = db.query(User)

                if active_only:
                    query = query.filter(User.is_active == True)

                return query.offset(offset).limit(limit).all()

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
