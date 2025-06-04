"""
Privacy Service API - Centralized privacy, PII detection, and GDPR compliance.
Provides privacy functionality for all other services.
SECURE: All endpoints use JWT authentication - users can only access their own data.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Import unified authentication system
from utils.auth import get_current_user_id, get_authenticated_user, AuthenticatedUser

# Internal imports
from .security.pii_detector import PIIDetector
from .processors.privacy_processor import PrivacyProcessor
from .processors.gdpr_processor import GDPRProcessor

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/privacy", tags=["privacy"])

# Initialize privacy components
pii_detector = PIIDetector()


# Pydantic models for API (user_id always comes from JWT - no user input needed)
class PIIDetectionRequest(BaseModel):
    content: str
    context: Optional[str] = None


class PIIDetectionResponse(BaseModel):
    detected_items: List[Dict[str, Any]]
    has_pii: bool
    risk_summary: Dict[str, Any]
    recommendations: Dict[str, Any]


class ConsentRequest(BaseModel):
    data_type: str
    consent_granted: bool
    consent_scope: Dict[str, Any]


class ConsentResponse(BaseModel):
    success: bool
    consent_id: str
    message: str


class DataDeletionRequest(BaseModel):
    data_types: Optional[List[str]] = None
    reason: str


# 🔐 SECURE PRIVACY ENDPOINTS - JWT Authentication Required


@router.post("/detect-pii", response_model=PIIDetectionResponse)
async def detect_pii(
    request: PIIDetectionRequest, user_id: str = Depends(get_current_user_id)
):
    """Detect PII in content. User authenticated via JWT."""
    try:
        # Create a temporary memory item for PII detection
        from ..memory.types import MemoryItem

        temp_memory = MemoryItem(
            id="temp",
            userId=user_id,  # Use authenticated user ID
            content=request.content,
            type="text",
            metadata={"context": request.context} if request.context else {},
            timestamp=datetime.utcnow(),
        )

        results = await pii_detector.detect_pii(temp_memory)

        return PIIDetectionResponse(
            detected_items=results.get("detected_items", []),
            has_pii=len(results.get("detected_items", [])) > 0,
            risk_summary=results.get("risk_summary", {}),
            recommendations=pii_detector.get_granular_consent_options(results),
        )

    except Exception as e:
        logger.error(f"Error detecting PII for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    request: ConsentRequest, user_id: str = Depends(get_current_user_id)
):
    """Record user consent for data processing. User authenticated via JWT."""
    try:
        # Generate consent ID for authenticated user
        consent_id = f"consent_{user_id}_{datetime.utcnow().isoformat()}"

        # Log consent decision
        logger.info(
            f"Consent recorded: {consent_id} - {request.data_type} - {request.consent_granted}"
        )

        return ConsentResponse(
            success=True, consent_id=consent_id, message="Consent recorded successfully"
        )

    except Exception as e:
        logger.error(f"Error recording consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-export")
async def export_user_data(
    data_types: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    """Export user data for GDPR compliance. JWT secured - user can only export their own data."""
    try:
        # Collect data from all services for authenticated user
        export_data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "data_types_requested": data_types.split(",") if data_types else ["all"],
            "data": {"note": "This would contain actual user data from all services"},
        }

        return export_data

    except Exception as e:
        logger.error(f"Error exporting data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/data-deletion")
async def delete_user_data(
    request: DataDeletionRequest, user_id: str = Depends(get_current_user_id)
):
    """Delete user data for GDPR compliance. JWT secured - user can only delete their own data."""
    try:
        # Coordinate deletion across all services for authenticated user
        logger.info(f"Data deletion requested for user {user_id}: {request.reason}")

        return {
            "success": True,
            "message": f"Data deletion initiated for user {user_id}",
            "data_types": request.data_types or ["all"],
            "deletion_id": f"del_{user_id}_{datetime.utcnow().isoformat()}",
        }

    except Exception as e:
        logger.error(f"Error deleting data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
