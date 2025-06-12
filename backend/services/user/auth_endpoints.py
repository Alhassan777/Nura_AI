"""
User Authentication Endpoints
Handles user authentication, registration, and session management.
UNIFIED: Uses the centralized auth system from utils/auth.py
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
import os
import asyncio

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

# Import Supabase client for server-side operations
from supabase import create_client, Client

# Import user sync service
from .sync_service import sync_service

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.error("Supabase configuration missing: URL or Service Role Key not set")

# Initialize Supabase admin client with basic configuration
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# Helper function to retry Supabase operations with exponential backoff
async def retry_supabase_operation(operation, max_retries=3, base_delay=1):
    """Retry a Supabase operation with exponential backoff for network issues."""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if (
                "handshake" in str(e).lower()
                or "timeout" in str(e).lower()
                or "ssl" in str(e).lower()
            ):
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Supabase operation failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                    continue
            # Re-raise if not a network error or max retries reached
            raise e
    return None


# Router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserLoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    session: Optional[Dict[str, Any]] = None


class UserSignupResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    email_verification_sent: bool = False


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetResponse(BaseModel):
    success: bool
    message: str


# Authentication endpoints
@router.post("/login", response_model=UserLoginResponse)
async def login_user(request: UserLoginRequest) -> UserLoginResponse:
    """
    Authenticate user via Supabase and sync with normalized database.
    Returns JWT token for subsequent API calls.
    """
    try:
        # Authenticate with Supabase
        auth_response = await retry_supabase_operation(
            lambda: supabase_admin.auth.sign_in_with_password(
                {"email": request.email, "password": request.password}
            )
        )

        if not auth_response.user:
            return UserLoginResponse(success=False, message="Invalid email or password")

        # Get user data
        user_data = auth_response.user

        # Sync user with normalized database
        sync_result = await sync_service.sync_user_from_supabase(
            supabase_user_data={
                "id": user_data.id,
                "email": user_data.email,
                "user_metadata": user_data.user_metadata or {},
                "phone": user_data.phone,
                "email_confirmed_at": user_data.email_confirmed_at,
                "created_at": user_data.created_at,
                "updated_at": user_data.updated_at,
            },
            source="login",
        )

        if not sync_result["success"]:
            logger.error(f"User sync failed during login: {sync_result['error']}")
            # Continue with login even if sync fails - user still authenticated

        return UserLoginResponse(
            success=True,
            message="Login successful",
            user={
                "id": user_data.id,
                "email": user_data.email,
                "full_name": (
                    user_data.user_metadata.get("full_name")
                    if user_data.user_metadata
                    else None
                ),
                "phone_number": user_data.phone,
                "is_verified": bool(user_data.email_confirmed_at),
            },
            session={
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "expires_at": auth_response.session.expires_at,
                "token_type": "Bearer",
            },
        )

    except Exception as e:
        logger.error(f"Login failed for {request.email}: {str(e)}")
        return UserLoginResponse(
            success=False,
            message="Login failed. Please check your credentials and try again.",
        )


@router.post("/signup", response_model=UserSignupResponse)
async def signup_user(request: UserSignupRequest) -> UserSignupResponse:
    """
    Register a new user via Supabase and sync with normalized database.
    Sends email verification if enabled.
    """
    try:
        # Create user in Supabase
        auth_response = await retry_supabase_operation(
            lambda: supabase_admin.auth.sign_up(
                {
                    "email": request.email,
                    "password": request.password,
                    "options": {
                        "data": {
                            "full_name": request.full_name,
                            "phone_number": request.phone_number,
                        }
                    },
                }
            )
        )

        if not auth_response.user:
            return UserSignupResponse(
                success=False, message="Failed to create user account"
            )

        user_data = auth_response.user

        # Sync user with normalized database
        sync_result = await sync_service.sync_user_from_supabase(
            supabase_user_data={
                "id": user_data.id,
                "email": user_data.email,
                "user_metadata": user_data.user_metadata or {},
                "phone": user_data.phone,
                "email_confirmed_at": user_data.email_confirmed_at,
                "created_at": user_data.created_at,
                "updated_at": user_data.updated_at,
            },
            source="signup",
        )

        if not sync_result["success"]:
            logger.error(f"User sync failed during signup: {sync_result['error']}")
            # Continue with signup - Supabase user created successfully

        # Check if email verification is required
        email_verification_sent = not bool(user_data.email_confirmed_at)

        return UserSignupResponse(
            success=True,
            message=(
                "Account created successfully! Please check your email to verify your account."
                if email_verification_sent
                else "Account created and verified successfully!"
            ),
            user={
                "id": user_data.id,
                "email": user_data.email,
                "full_name": (
                    user_data.user_metadata.get("full_name")
                    if user_data.user_metadata
                    else None
                ),
                "phone_number": user_data.phone,
                "is_verified": bool(user_data.email_confirmed_at),
            },
            email_verification_sent=email_verification_sent,
        )

    except Exception as e:
        logger.error(f"Signup failed for {request.email}: {str(e)}")
        return UserSignupResponse(
            success=False,
            message="Signup failed. The email may already be in use or there was a server error.",
        )


@router.post("/resend-verification")
async def resend_verification_email(
    request: PasswordResetRequest,
) -> PasswordResetResponse:
    """
    Resend email verification for unverified users.
    """
    try:
        # Request verification email from Supabase
        response = await retry_supabase_operation(
            lambda: supabase_admin.auth.resend(
                {"type": "signup", "email": request.email}
            )
        )

        return PasswordResetResponse(
            success=True,
            message="Verification email sent successfully. Please check your inbox.",
        )

    except Exception as e:
        logger.error(
            f"Failed to resend verification email for {request.email}: {str(e)}"
        )
        return PasswordResetResponse(
            success=False,
            message="Failed to send verification email. Please try again later.",
        )


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest) -> PasswordResetResponse:
    """
    Send password reset email to user.
    """
    try:
        # Request password reset from Supabase
        response = await retry_supabase_operation(
            lambda: supabase_admin.auth.reset_password_email(request.email)
        )

        return PasswordResetResponse(
            success=True,
            message="Password reset email sent successfully. Please check your inbox.",
        )

    except Exception as e:
        logger.error(
            f"Failed to send password reset email for {request.email}: {str(e)}"
        )
        return PasswordResetResponse(
            success=False,
            message="Failed to send password reset email. Please try again later.",
        )


@router.post("/logout")
async def logout_user(user_id: str = Depends(get_current_user_id)) -> Dict[str, Any]:
    """
    Logout the authenticated user.
    JWT secured - user can only logout themselves.
    """
    try:
        # In a JWT-based system, logout is typically handled client-side
        # by removing the token. Server-side logout would require token blacklisting.

        logger.info(f"User {user_id} logged out")

        return {"success": True, "message": "Logout successful"}

    except Exception as e:
        logger.error(f"Logout failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


# Protected endpoints (require JWT authentication)


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> UserProfileResponse:
    """
    Get current user's profile information.
    JWT secured - returns authenticated user's own profile.
    """
    try:
        # Get additional user data from normalized database
        from .database import get_db
        from models import User
        from .sync_service import to_uuid

        with get_db() as db:
            user_uuid = to_uuid(user.user_id)
            db_user = db.query(User).filter(User.id == user_uuid).first()

            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            return UserProfileResponse(
                user_id=str(db_user.id),
                email=db_user.email,
                full_name=db_user.full_name,
                phone_number=db_user.phone_number,
                is_active=db_user.is_active,
                is_verified=db_user.is_verified,
                created_at=db_user.created_at.isoformat() if db_user.created_at else "",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile for user {user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.post("/refresh-token")
async def refresh_token(user_id: str = Depends(get_current_user_id)) -> Dict[str, Any]:
    """
    Refresh user's JWT token.
    JWT secured - user can only refresh their own token.
    """
    try:
        # In a full implementation, you would:
        # 1. Validate the refresh token
        # 2. Generate a new access token
        # 3. Optionally rotate the refresh token

        # For now, we'll return a success message
        # The frontend should handle token refresh via Supabase client

        return {
            "success": True,
            "message": "Token refresh should be handled by Supabase client",
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Token refresh failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.delete("/account")
async def delete_user_account(
    user_id: str = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Delete the authenticated user's account.
    JWT secured - user can only delete their own account.
    """
    try:
        # Delete from Supabase
        try:
            await retry_supabase_operation(
                lambda: supabase_admin.auth.admin.delete_user(user_id)
            )
            logger.info(f"Deleted user {user_id} from Supabase")
        except Exception as e:
            logger.error(f"Failed to delete user from Supabase: {str(e)}")

        # Delete from normalized database
        from .database import get_db
        from models import User
        from .sync_service import to_uuid

        with get_db() as db:
            user_uuid = to_uuid(user_id)
            db_user = db.query(User).filter(User.id == user_uuid).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                logger.info(f"Deleted user {user_id} from normalized database")

        # Here you would also:
        # 1. Clear all user memories from Redis and Pinecone
        # 2. Delete chat conversations
        # 3. Clean up any other user data

        return {"success": True, "message": "Account deleted successfully"}

    except Exception as e:
        logger.error(f"Account deletion failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed",
        )

        # Health check
        try:
            # Test if we can connect to Supabase
            test_response = await retry_supabase_operation(
                lambda: supabase_admin.auth.get_user("test-user-id")
            )
            supabase_status = "healthy"
        except Exception as e:
            supabase_status = "error"
            supabase_error = str(e)

        return {
            "status": "healthy",
            "supabase": supabase_status,
            "supabase_error": supabase_error,
            "supabase_url": SUPABASE_URL,
            "supabase_key_configured": bool(SUPABASE_SERVICE_ROLE_KEY),
            "auth_system": "unified_jwt",
            "endpoints": [
                "/auth/login",
                "/auth/signup",
                "/auth/logout",
                "/auth/profile",
            ],
        }
    except Exception as e:
        logger.error(f"Auth health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "supabase": "unknown",
            "auth_system": "unified_jwt",
        }


@router.post("/test-email-verification")
async def test_email_verification(request: PasswordResetRequest) -> Dict[str, Any]:
    """
    Test endpoint to debug email verification issues.
    This will attempt to resend verification email and provide detailed error info.
    """
    try:
        logger.info(f"Testing email verification for: {request.email}")

        # Check if user exists in Supabase
        try:
            user_response = await retry_supabase_operation(
                lambda: supabase_admin.auth.admin.get_user_by_email(request.email)
            )
            if user_response.user:
                user = user_response.user
                logger.info(
                    f"User found: {user.id}, email_confirmed_at: {user.email_confirmed_at}"
                )

                # Try to resend verification email
                try:
                    resend_response = await retry_supabase_operation(
                        lambda: supabase_admin.auth.resend(
                            {"type": "signup", "email": request.email}
                        )
                    )

                    return {
                        "success": True,
                        "message": "Verification email sent successfully",
                        "user_exists": True,
                        "user_verified": bool(user.email_confirmed_at),
                        "user_id": user.id,
                        "resend_response": str(resend_response),
                    }

                except Exception as resend_error:
                    logger.error(f"Resend failed: {str(resend_error)}")
                    return {
                        "success": False,
                        "message": f"Failed to resend verification: {str(resend_error)}",
                        "user_exists": True,
                        "user_verified": bool(user.email_confirmed_at),
                        "user_id": user.id,
                        "error": str(resend_error),
                    }
            else:
                return {
                    "success": False,
                    "message": "User not found in Supabase",
                    "user_exists": False,
                }

        except Exception as user_error:
            logger.error(f"Error getting user: {str(user_error)}")
            return {
                "success": False,
                "message": f"Error checking user: {str(user_error)}",
                "error": str(user_error),
            }

    except Exception as e:
        logger.error(f"Test email verification failed: {str(e)}")
        return {"success": False, "message": f"Test failed: {str(e)}", "error": str(e)}


# All authentication now uses the unified system - maximum security and consistency
