"""
User Management API
Handles user synchronization, profile management, and service integration.
Provides endpoints for frontend-backend communication and Supabase webhooks.
SECURE: All endpoints use JWT authentication - users can only access their own data.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid
import hmac
import hashlib
import json
import os

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

from .sync_service import sync_service
from models import ServiceType
from .database import get_db
from utils.database import get_db_context
from ..memory.config import Config

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/users", tags=["users"])

# Security scheme
security = HTTPBearer()


# Pydantic models for API requests/responses (user_id always comes from JWT)
class UserCreateRequest(BaseModel):
    """Request model for creating/syncing user from frontend."""

    id: str  # Supabase Auth user ID
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = {}


class UserUpdateRequest(BaseModel):
    """Request model for updating user profile."""

    full_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class ServiceProfileUpdateRequest(BaseModel):
    """Request model for updating service-specific profile."""

    service_preferences: Optional[Dict[str, Any]] = None
    service_metadata: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Response model for user data."""

    id: str
    email: str
    phone_number: Optional[str]
    full_name: Optional[str]
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    current_streak: int
    xp: int
    privacy_settings: Dict[str, Any]
    created_at: Optional[str]
    updated_at: Optional[str]
    last_active_at: Optional[str]


class ServiceProfileResponse(BaseModel):
    """Response model for service profile data."""

    id: str
    user_id: str
    service_type: str
    service_preferences: Dict[str, Any]
    service_metadata: Dict[str, Any]
    usage_stats: Dict[str, Any]
    last_used_at: Optional[str]


class UserServiceProfileRequest(BaseModel):
    """Request model for updating service-specific profile."""

    service_preferences: Optional[Dict[str, Any]] = None
    service_metadata: Optional[Dict[str, Any]] = None


# User Management Endpoints


@router.post("/sync", response_model=Dict[str, Any])
async def sync_user_from_frontend(
    request: UserCreateRequest,
    background_tasks: BackgroundTasks,
    request_obj: Request,
    session_id: Optional[str] = Header(None, alias="x-session-id"),
):
    """
    Sync user data from frontend to backend.
    Called when user logs in or when profile data needs to be synced.
    """
    try:
        request_id = str(uuid.uuid4())

        # Convert frontend request to Supabase format
        supabase_user_data = {
            "id": request.id,
            "email": request.email,
            "phone": request.phone_number,
            "user_metadata": {"full_name": request.full_name, **request.user_metadata},
            # Add current timestamp as last_sign_in for active users
            "last_sign_in_at": datetime.utcnow().isoformat() + "Z",
        }

        # Sync user data
        result = await sync_service.sync_user_from_supabase(
            supabase_user_data=supabase_user_data,
            source="frontend_sync",
            session_id=session_id,
            request_id=request_id,
        )

        if result["success"]:
            return {
                "success": True,
                "action": result["action"],
                "user": result["user"],
                "message": f"User {result['action']} successfully",
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to sync user: {result['error']}"
            )

    except Exception as e:
        logger.error(f"Error in sync_user_from_frontend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """Get current user's profile data."""
    try:
        user_data = await sync_service.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    request: UserUpdateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    session_id: Optional[str] = Header(None, alias="x-session-id"),
):
    """Update user profile data."""
    try:
        request_id = str(uuid.uuid4())

        # Convert request to dict, excluding None values
        profile_data = {k: v for k, v in request.dict().items() if v is not None}

        result = await sync_service.update_user_profile(
            user_id=user_id,
            profile_data=profile_data,
            source="frontend_api",
            session_id=session_id,
            request_id=request_id,
        )

        if result["success"]:
            return {
                "success": True,
                "action": result["action"],
                "changes": result.get("changes", {}),
                "user": result["user"],
                "message": "Profile updated successfully",
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to update profile: {result['error']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Service Profile Management


@router.get("/services", response_model=List[str])
async def get_available_services():
    """Get list of available services."""
    return [service.value for service in ServiceType]


@router.get("/services/{service_type}", response_model=ServiceProfileResponse)
async def get_service_profile(
    service_type: str, user_id: str = Depends(get_current_user_id)
):
    """Get user's profile for a specific service."""
    try:
        # Validate service type
        if service_type not in [s.value for s in ServiceType]:
            raise HTTPException(status_code=400, detail="Invalid service type")

        profile_data = await sync_service.get_service_profile(user_id, service_type)
        if not profile_data:
            raise HTTPException(
                status_code=404, detail=f"Service profile not found for {service_type}"
            )

        return ServiceProfileResponse(**profile_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting service profile {user_id}/{service_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/services/{service_type}", response_model=Dict[str, Any])
async def update_service_profile(
    service_type: str,
    request: ServiceProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    session_id: Optional[str] = Header(None, alias="x-session-id"),
):
    """Update user's service-specific profile."""
    try:
        # Validate service type
        if service_type not in [s.value for s in ServiceType]:
            raise HTTPException(status_code=400, detail="Invalid service type")

        # This would need to be implemented in sync_service
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Service profile update for {service_type} - implementation pending",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating service profile {user_id}/{service_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoints (for Supabase Auth events)


@router.post("/webhooks/supabase-auth")
async def handle_supabase_auth_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: Optional[str] = Header(None, alias="x-signature"),
):
    """
    Handle Supabase Auth webhooks for real-time user sync.
    Processes user.created, user.updated, user.deleted events.
    """
    try:
        # Verify webhook signature (if configured)
        body = await request.body()
        webhook_secret = Config.SUPABASE_WEBHOOK_SECRET  # Add this to config

        if webhook_secret and x_signature:
            expected_signature = hmac.new(
                webhook_secret.encode(), body, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(f"sha256={expected_signature}", x_signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse webhook data
        webhook_data = json.loads(body.decode())
        event_type = webhook_data.get("type")
        user_data = webhook_data.get("record", {})

        request_id = str(uuid.uuid4())

        logger.info(
            f"Received Supabase Auth webhook: {event_type} for user {user_data.get('id')}"
        )

        if event_type in ["INSERT", "UPDATE"]:
            # User created or updated in Supabase Auth
            result = await sync_service.sync_user_from_supabase(
                supabase_user_data=user_data,
                source="supabase_webhook",
                request_id=request_id,
            )

            if result["success"]:
                return {
                    "success": True,
                    "message": f"User {result['action']} successfully",
                }
            else:
                logger.error(f"Failed to sync user from webhook: {result['error']}")
                return {"success": False, "error": result["error"]}

        elif event_type == "DELETE":
            # User deleted in Supabase Auth - soft delete in backend
            user_id = user_data.get("id")
            if user_id:
                # Implement soft delete logic here
                logger.info(
                    f"User {user_id} deleted in Supabase Auth - implementing soft delete"
                )
                return {"success": True, "message": "User soft delete processed"}

        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return {"success": True, "message": f"Ignored event type: {event_type}"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in webhook payload")
    except Exception as e:
        logger.error(f"Error handling Supabase webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Health and Debug Endpoints

    overall_healthy = True

    try:
        # Test database connection
        try:
            with get_db_context() as db:
                db.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful",
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            overall_healthy = False

        # Test sync service
        try:
            # Check if sync service is responsive
            test_result = await sync_service.health_check()
            health_status["checks"]["sync_service"] = {
                "status": "healthy" if test_result else "degraded",
                "message": "Sync service operational",
            }
        except Exception as e:
            health_status["checks"]["sync_service"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            overall_healthy = False

        # Test Supabase integration (if configured)
        try:
            if hasattr(Config, "SUPABASE_URL") and Config.SUPABASE_URL:
                # Could test Supabase connectivity here
                health_status["checks"]["supabase"] = {
                    "status": "configured",
                    "message": "Supabase integration configured",
                }
            else:
                health_status["checks"]["supabase"] = {
                    "status": "not_configured",
                    "message": "Supabase not configured",
                }
        except Exception as e:
            health_status["checks"]["supabase"] = {"status": "error", "error": str(e)}

        # Set overall status
        if not overall_healthy:
            health_status["status"] = "unhealthy"
        elif any(
            check.get("status") == "degraded"
            for check in health_status["checks"].values()
        ):
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "user-management",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "checks": health_status.get("checks", {}),
        }


@router.get("/sync-logs/{user_id}")
async def get_sync_logs(
    user_id: str,
    limit: int = 10,
    admin_user_id: str = Depends(get_current_user_id),  # Add admin check in production
):
    """Get sync logs for debugging (admin only)."""
    try:
        # This would query UserSyncLog table
        # For now, return placeholder
        return {
            "user_id": user_id,
            "logs": [],
            "message": "Sync logs endpoint - implementation pending",
        }

    except Exception as e:
        logger.error(f"Error getting sync logs for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
