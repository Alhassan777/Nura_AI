"""
Unified Authentication System for Nura
Single source of truth for JWT validation and user authentication.
Simplified and consolidated from multiple auth files.
"""

import jwt
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError
import requests
from pydantic import BaseModel

# Import from unified models
from models import User

logger = logging.getLogger(__name__)

# Configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_ALGORITHM = "HS256"

if not SUPABASE_JWT_SECRET:
    logger.warning("SUPABASE_JWT_SECRET not configured - JWT validation will fail")

# Initialize security scheme
security = HTTPBearer()


class AuthenticatedUser:
    """Wrapper class for authenticated user information."""

    def __init__(self, session_info: Dict[str, Any]):
        self.user_id = session_info["user_id"]
        self.email = session_info["email"]
        self.role = session_info.get("role", "authenticated")
        self.session_id = session_info.get("session_id")
        self.is_anonymous = session_info.get("is_anonymous", False)
        self.expires_at = session_info.get("exp")
        self.issued_at = session_info.get("iat")

    def __str__(self):
        return f"AuthenticatedUser(user_id={self.user_id}, email={self.email})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "session_id": self.session_id,
            "is_anonymous": self.is_anonymous,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
        }


class Auth:
    """Core authentication functionality."""

    @staticmethod
    def validate_jwt_token(token: str) -> Dict[str, Any]:
        """
        Core JWT validation function.

        Args:
            token: JWT token string

        Returns:
            Dict containing token payload

        Raises:
            HTTPException: If token is invalid
        """
        if not SUPABASE_JWT_SECRET:
            logger.error("SUPABASE_JWT_SECRET not configured")
            raise HTTPException(
                status_code=500, detail="Authentication configuration error"
            )

        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                audience="authenticated",
                options={"verify_exp": True},
            )

            user_id = payload.get("sub")
            if not user_id:
                logger.warning("JWT token missing user ID (sub claim)")
                raise HTTPException(
                    status_code=401, detail="Invalid token: missing user ID"
                )

            logger.debug(f"Successfully authenticated user: {user_id}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidAudienceError:
            logger.warning("JWT token has invalid audience")
            raise HTTPException(status_code=401, detail="Invalid token audience")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def verify_user_exists_in_db(user_id: str) -> bool:
        """
        Verify user exists in our normalized database.

        Args:
            user_id: User ID to verify

        Returns:
            bool: True if user exists and is active

        Raises:
            HTTPException: If user not found or inactive
        """
        try:
            from utils.database import get_db_context
            from services.user.sync_service import to_uuid
            from models import User

            with get_db_context("user") as db:
                user_uuid = to_uuid(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if not user:
                    logger.warning(f"User {user_id} not found in normalized database")
                    raise HTTPException(
                        status_code=401,
                        detail="User not found. Please sync your account.",
                    )

                if not user.is_active:
                    logger.warning(f"User {user_id} is inactive")
                    raise HTTPException(status_code=401, detail="Account is inactive")

                return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying user in database: {str(e)}")
            raise HTTPException(status_code=500, detail="Database verification failed")

    @staticmethod
    def authenticate_user(credentials: HTTPAuthorizationCredentials) -> str:
        """
        Authenticate user and return user_id.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            str: Validated user ID
        """
        payload = Auth.validate_jwt_token(credentials.credentials)
        user_id = payload["sub"]
        Auth.verify_user_exists_in_db(user_id)
        return user_id

    @staticmethod
    def get_user_session(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """
        Get full user session information.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            Dict containing user session information
        """
        payload = Auth.validate_jwt_token(credentials.credentials)

        session_info = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "session_id": payload.get("session_id"),
            "is_anonymous": payload.get("is_anonymous", False),
        }

        Auth.verify_user_exists_in_db(session_info["user_id"])
        return session_info

    @staticmethod
    def authenticate_user_from_token(token: str) -> str:
        """
        Authenticate user directly from token string.

        Args:
            token: JWT token string

        Returns:
            str: Validated user ID
        """
        payload = Auth.validate_jwt_token(token)
        user_id = payload["sub"]
        Auth.verify_user_exists_in_db(user_id)
        return user_id

    @staticmethod
    def get_user_from_token(token: str) -> AuthenticatedUser:
        """
        Get AuthenticatedUser object from token string.

        Args:
            token: JWT token string

        Returns:
            AuthenticatedUser object
        """
        payload = Auth.validate_jwt_token(token)

        session_info = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "session_id": payload.get("session_id"),
            "is_anonymous": payload.get("is_anonymous", False),
        }

        Auth.verify_user_exists_in_db(session_info["user_id"])
        return AuthenticatedUser(session_info)

    @staticmethod
    def is_service_role_token(token: str) -> bool:
        """
        Check if token is a service role token.

        Args:
            token: JWT token or service role key

        Returns:
            bool: True if service role token
        """
        try:
            if token == SUPABASE_SERVICE_ROLE_KEY:
                return True

            payload = jwt.decode(
                token, options={"verify_signature": False, "verify_exp": False}
            )
            return payload.get("role") == "service_role"

        except Exception:
            return False

    @staticmethod
    def verify_user_access(resource_user_id: str, current_user_id: str) -> bool:
        """
        Verify user has access to specific resources.

        Args:
            resource_user_id: User ID that owns the resource
            current_user_id: Currently authenticated user ID

        Returns:
            bool: True if access allowed

        Raises:
            HTTPException: If access denied
        """
        if resource_user_id != current_user_id:
            logger.warning(
                f"Access denied: User {current_user_id} tried to access resources of user {resource_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own resources",
            )
        return True


# FastAPI Dependencies
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency to get authenticated user ID.

    Usage:
        @router.get("/memories")
        async def get_memories(user_id: str = Depends(get_current_user_id)):
            return await memory_service.get_memories(user_id)
    """
    try:
        return Auth.authenticate_user(credentials)
    except HTTPException as e:
        logger.warning(f"Authentication failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


def get_current_user_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get full user session information.

    Usage:
        @router.get("/profile")
        async def get_profile(session: dict = Depends(get_current_user_session)):
            user_id = session["user_id"]
            email = session["email"]
            return {"user_id": user_id, "email": email}
    """
    try:
        return Auth.get_user_session(credentials)
    except HTTPException as e:
        logger.warning(f"Session validation failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected session validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session validation failed"
        )


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """
    FastAPI dependency to get AuthenticatedUser object.

    Usage:
        @router.get("/user-info")
        async def get_user_info(user: AuthenticatedUser = Depends(get_authenticated_user)):
            return {"user_id": user.user_id, "email": user.email}
    """
    session_info = get_current_user_session(credentials)
    return AuthenticatedUser(session_info)


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    FastAPI dependency for optional authentication.

    Usage:
        @router.get("/public-data")
        async def get_public_data(user_id: Optional[str] = Depends(get_optional_user_id)):
            if user_id:
                return await get_personalized_data(user_id)
            else:
                return await get_public_data()
    """
    if not credentials:
        return None

    try:
        return Auth.authenticate_user(credentials)
    except HTTPException:
        logger.debug("Optional authentication failed - proceeding without auth")
        return None
    except Exception as e:
        logger.warning(f"Optional authentication error: {str(e)}")
        return None


# Utility functions
def verify_user_access(resource_user_id: str, current_user_id: str) -> bool:
    """Convenience function for user access verification."""
    return Auth.verify_user_access(resource_user_id, current_user_id)


def authenticate_token(token: str) -> str:
    """Convenience function for direct token authentication."""
    return Auth.authenticate_user_from_token(token)


def get_user_from_token(token: str) -> AuthenticatedUser:
    """Convenience function to get user object from token."""
    return Auth.get_user_from_token(token)
