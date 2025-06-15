"""
Audit logger for tracking memory processing operations.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from services.memory.types import MemoryItem


class AuditLogger:
    def __init__(self):
        # Initialize local file-based logging instead of Google Cloud
        self.use_google_cloud = (
            os.getenv("USE_GOOGLE_CLOUD_LOGGING", "false").lower() == "true"
        )

        # Initialize constants here (not in _log_to_file method)
        # Log levels
        self.INFO = "INFO"
        self.WARNING = "WARNING"
        self.ERROR = "ERROR"

        # Event types
        self.MEMORY_CREATED = "memory_created"
        self.MEMORY_ACCESSED = "memory_accessed"
        self.MEMORY_DELETED = "memory_deleted"
        self.MEMORY_CLEARED = "memory_cleared"
        self.CONSENT_GRANTED = "consent_granted"
        self.CONSENT_REVOKED = "consent_revoked"
        self.PII_DETECTED = "pii_detected"
        self.AUTH_FAILED = "auth_failed"

        if self.use_google_cloud:
            try:
                from google.cloud import logging as gcp_logging

                self.client = gcp_logging.Client()
                self.logger = self.client.logger("memory-service-audit")
                self.log_method = self._log_to_gcp
            except Exception as e:
                print(f"Warning: Google Cloud Logging not available: {e}")
                self._setup_local_logging()
        else:
            self._setup_local_logging()

    def _setup_local_logging(self):
        """Setup local file-based audit logging."""
        # Create audit logs directory
        audit_dir = os.getenv("AUDIT_LOG_DIR", "./logs/audit")
        os.makedirs(audit_dir, exist_ok=True)

        # Setup local logger
        self.local_logger = logging.getLogger("memory-service-audit")
        self.local_logger.setLevel(logging.INFO)

        # Create file handler
        log_file = os.path.join(audit_dir, "memory_audit.log")
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        if not self.local_logger.handlers:
            self.local_logger.addHandler(handler)

        self.log_method = self._log_to_file
        # Audit logging initialization message is now handled by centralized config_manager

    def _log_to_gcp(self, log_entry: Dict[str, Any]):
        """Log to Google Cloud Logging."""
        self.logger.log_struct(log_entry)

    def _log_to_file(self, log_entry: Dict[str, Any]):
        """Log to local file."""
        self.local_logger.info(json.dumps(log_entry, default=str))

    async def log_event(
        self,
        event_type: str,
        user_id: str,
        level: str = "INFO",
        details: Optional[Dict[str, Any]] = None,
        memory: Optional[MemoryItem] = None,
    ) -> None:
        """Log an audit event."""
        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "level": level,
            "details": details or {},
        }

        # Add memory info if provided
        if memory:
            log_entry["memory"] = {
                "id": memory.id,
                "type": memory.type,
                "has_pii": memory.metadata.get("has_pii", False),
                "sensitive_types": memory.metadata.get("sensitive_types", []),
            }

        # Write to configured logging system
        self.log_method(log_entry)

    async def log_memory_created(
        self,
        user_id: str,
        memory: MemoryItem,
        score: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log memory creation event."""
        details = {
            "score": score,
            "stored_in": (
                "long_term" if score.get("stability", 0) > 0.7 else "short_term"
            ),
        }

        # Add any additional metadata
        if metadata:
            details.update(metadata)

        await self.log_event(
            event_type=self.MEMORY_CREATED,
            user_id=user_id,
            memory=memory,
            details=details,
        )

    async def log_memory_accessed(
        self, user_id: str, memory: MemoryItem, query: str
    ) -> None:
        """Log memory access event."""
        await self.log_event(
            event_type=self.MEMORY_ACCESSED,
            user_id=user_id,
            memory=memory,
            details={"query": query},
        )

    async def log_memory_deleted(self, user_id: str, memory: MemoryItem) -> None:
        """Log memory deletion event."""
        await self.log_event(
            event_type=self.MEMORY_DELETED, user_id=user_id, memory=memory
        )

    async def log_memory_cleared(self, user_id: str, count: int) -> None:
        """Log memory clear event."""
        await self.log_event(
            event_type=self.MEMORY_CLEARED, user_id=user_id, details={"count": count}
        )

    async def log_consent_granted(
        self, user_id: str, memory: MemoryItem, sensitive_types: List[str]
    ) -> None:
        """Log consent granted event."""
        await self.log_event(
            event_type=self.CONSENT_GRANTED,
            user_id=user_id,
            memory=memory,
            details={"sensitive_types": sensitive_types},
        )

    async def log_consent_revoked(self, user_id: str, memory: MemoryItem) -> None:
        """Log consent revoked event."""
        await self.log_event(
            event_type=self.CONSENT_REVOKED, user_id=user_id, memory=memory
        )

    async def log_pii_detected(
        self,
        user_id: str,
        memory: MemoryItem,
        pii_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log PII detection event."""
        details = {"pii_types": pii_types}

        # Add any additional metadata
        if metadata:
            details.update(metadata)

        await self.log_event(
            event_type=self.PII_DETECTED,
            user_id=user_id,
            level=self.WARNING,
            memory=memory,
            details=details,
        )

    async def log_auth_failed(self, user_id: Optional[str], reason: str) -> None:
        """Log authentication failure event."""
        await self.log_event(
            event_type=self.AUTH_FAILED,
            user_id=user_id or "unknown",
            level=self.ERROR,
            details={"reason": reason},
        )
