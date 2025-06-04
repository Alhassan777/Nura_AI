"""
Audit Service API - Centralized audit logging and compliance.
Provides audit functionality for all other services.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Internal imports
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/audit", tags=["audit"])

# Initialize audit logger
audit_logger = AuditLogger()


# Pydantic models for API
class AuditLogRequest(BaseModel):
    user_id: Optional[str] = None
    action: str
    resource: str
    details: Optional[Dict[str, Any]] = None
    severity: str = "info"


class AuditLogResponse(BaseModel):
    success: bool
    audit_id: str
    message: str


class AuditQueryRequest(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100


@router.post("/log", response_model=AuditLogResponse)
async def log_audit_event(request: AuditLogRequest):
    """Log an audit event."""
    try:
        audit_id = await audit_logger.log_event(
            user_id=request.user_id,
            action=request.action,
            resource=request.resource,
            details=request.details or {},
            severity=request.severity,
        )

        return AuditLogResponse(
            success=True, audit_id=audit_id, message="Audit event logged successfully"
        )

    except Exception as e:
        logger.error(f"Error logging audit event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def query_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Query audit logs with filters."""
    try:
        # This would query the audit log storage
        logs = await audit_logger.query_logs(
            user_id=user_id, action=action, resource=resource, limit=limit
        )

        return {
            "logs": logs,
            "total_count": len(logs),
            "filters_applied": {
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "limit": limit,
            },
        }

    except Exception as e:
        logger.error(f"Error querying audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
