"""
Webhook handler for Vapi events.
Processes call events and stores summaries (NO transcripts).
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import VoiceCall, CallSummary, WebhookEvent, VoiceUser
from .config import config
from .database import get_db_session

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles incoming Vapi webhooks."""

    def __init__(self):
        self.webhook_secret = config.WEBHOOK_SECRET

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Vapi.

        Args:
            payload: Raw request body
            signature: Signature from Vapi headers

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning(
                "No webhook secret configured - skipping signature verification"
            )
            return True

        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(), payload, hashlib.sha256
            ).hexdigest()

            # Remove 'sha256=' prefix if present
            if signature.startswith("sha256="):
                signature = signature[7:]

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def handle_webhook(
        self, payload: Dict[str, Any], signature: Optional[str] = None
    ) -> bool:
        """
        Process incoming webhook event.

        Args:
            payload: Webhook payload from Vapi
            signature: HMAC signature for verification

        Returns:
            True if processed successfully
        """
        try:
            # Log the webhook event first
            await self._log_webhook_event(payload)

            event_type = payload.get("type") or payload.get("eventType")
            if not event_type:
                logger.warning("No event type in webhook payload")
                return False

            # Extract call ID
            call_id = self._extract_call_id(payload)
            if not call_id:
                logger.warning("No call ID found in webhook payload")
                return False

            logger.info(f"Processing webhook event: {event_type} for call {call_id}")

            # Route to appropriate handler
            if event_type == "call-start":
                return await self._handle_call_start(payload, call_id)
            elif event_type == "call-end":
                return await self._handle_call_end(payload, call_id)
            elif event_type == "analysis-complete":
                return await self._handle_analysis_complete(payload, call_id)
            else:
                logger.info(f"Ignoring event type: {event_type}")
                return True

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False

    def _extract_call_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract call ID from webhook payload."""
        return (
            payload.get("call", {}).get("id")
            or payload.get("callId")
            or payload.get("id")
        )

    def _extract_user_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from call metadata."""
        call_data = payload.get("call", {})
        metadata = call_data.get("metadata", {})
        return metadata.get("userId")

    async def _handle_call_start(self, payload: Dict[str, Any], call_id: str) -> bool:
        """Handle call-start event."""
        try:
            with get_db_session() as db:
                call_data = payload.get("call", {})
                user_id = self._extract_user_id(payload)

                if not user_id:
                    logger.error(f"No user ID in call-start for call {call_id}")
                    return False

                # Check if user exists
                user = db.query(VoiceUser).filter(VoiceUser.id == user_id).first()
                if not user:
                    logger.error(f"User {user_id} not found for call {call_id}")
                    return False

                # Create or update call record
                existing_call = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if existing_call:
                    # Update existing call
                    existing_call.status = "in-progress"
                    existing_call.started_at = datetime.utcnow()
                else:
                    # Create new call record
                    metadata = call_data.get("metadata", {})
                    channel = metadata.get("channel", "browser")

                    new_call = VoiceCall(
                        vapi_call_id=call_id,
                        user_id=user_id,
                        assistant_id=call_data.get(
                            "assistantId", config.DEFAULT_ASSISTANT_ID
                        ),
                        channel=channel,
                        status="in-progress",
                        phone_number=call_data.get("phoneNumber"),
                        started_at=datetime.utcnow(),
                    )
                    db.add(new_call)

                logger.info(f"Recorded call start for {call_id}")
                return True

        except Exception as e:
            logger.error(f"Error handling call-start: {e}")
            return False

    async def _handle_call_end(self, payload: Dict[str, Any], call_id: str) -> bool:
        """Handle call-end event."""
        try:
            with get_db_session() as db:
                call_data = payload.get("call", {})

                # Update call record
                call_record = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if not call_record:
                    logger.warning(f"Call record not found for {call_id}")
                    return False

                call_record.status = "completed"
                call_record.ended_at = datetime.utcnow()

                # Store cost information if available
                cost_data = call_data.get("cost")
                if cost_data:
                    call_record.cost_total = str(cost_data.get("total", 0))
                    call_record.cost_breakdown = cost_data

                logger.info(f"Recorded call end for {call_id}")
                return True

        except Exception as e:
            logger.error(f"Error handling call-end: {e}")
            return False

    async def _handle_analysis_complete(
        self, payload: Dict[str, Any], call_id: str
    ) -> bool:
        """
        Handle analysis-complete event.
        This is where we store the summary WITHOUT the transcript.
        """
        try:
            with get_db_session() as db:
                # Get call record
                call_record = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if not call_record:
                    logger.warning(f"Call record not found for analysis {call_id}")
                    return False

                analysis_data = payload.get("analysis", {})

                # Extract summary data (NO transcript)
                summary_data = {
                    "sentiment": analysis_data.get("sentiment"),
                    "summary": analysis_data.get("summary"),
                    "keyTopics": analysis_data.get("keyTopics", []),
                    "actionItems": analysis_data.get("actionItems", []),
                    "structuredData": analysis_data.get("structuredData", {}),
                    # Add any mental health specific analysis
                    "emotionalState": analysis_data.get("emotionalState"),
                    "crisisIndicators": analysis_data.get("crisisIndicators", []),
                    "metadata": {
                        "analyzedAt": datetime.utcnow().isoformat(),
                        "vapiCallId": call_id,
                    },
                }

                # Check if summary already exists
                existing_summary = (
                    db.query(CallSummary)
                    .filter(CallSummary.call_id == call_record.id)
                    .first()
                )

                if existing_summary:
                    # Update existing summary
                    existing_summary.summary_json = summary_data
                    existing_summary.sentiment = analysis_data.get("sentiment")
                    existing_summary.key_topics = analysis_data.get("keyTopics", [])
                    existing_summary.action_items = analysis_data.get("actionItems", [])
                    existing_summary.emotional_state = analysis_data.get(
                        "emotionalState"
                    )
                    existing_summary.crisis_indicators = analysis_data.get(
                        "crisisIndicators", []
                    )
                else:
                    # Create new summary
                    new_summary = CallSummary(
                        call_id=call_record.id,
                        user_id=call_record.user_id,
                        summary_json=summary_data,
                        sentiment=analysis_data.get("sentiment"),
                        key_topics=analysis_data.get("keyTopics", []),
                        action_items=analysis_data.get("actionItems", []),
                        emotional_state=analysis_data.get("emotionalState"),
                        crisis_indicators=analysis_data.get("crisisIndicators", []),
                    )
                    db.add(new_summary)

                logger.info(f"Stored call summary for {call_id} (NO transcript stored)")
                return True

        except Exception as e:
            logger.error(f"Error handling analysis-complete: {e}")
            return False

    async def _log_webhook_event(self, payload: Dict[str, Any]) -> None:
        """Log webhook event for debugging."""
        try:
            with get_db_session() as db:
                event = WebhookEvent(
                    vapi_call_id=self._extract_call_id(payload),
                    event_type=payload.get("type") or payload.get("eventType"),
                    payload=payload,
                    processing_status="pending",
                )
                db.add(event)

        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")


# Global handler instance
webhook_handler = WebhookHandler()
