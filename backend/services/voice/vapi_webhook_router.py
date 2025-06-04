"""
VAPI Webhook Router - Unified Webhook Handler for Mental Health Assistant

This module provides a single entry point for all VAPI webhooks, routing tool calls
to appropriate handlers based on the tool name. This consolidates all webhook
functionality into one place.

Architecture:
- Single webhook endpoint: /api/voice/webhooks
- Routes based on tool name to appropriate handler
- Supports all tool categories: crisis, general, scheduling, safety_checkup, image, memory
- Validates webhook signatures for security
- Comprehensive logging and error handling
"""

import hmac
import hashlib
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from models import VoiceCall, CallSummary, WebhookEvent
from .config import config
from .database import get_db
from .user_integration import VoiceUserIntegration
from .vapi_tools_registry import vapi_tools_registry
from .scheduling_integration import handle_vapi_tool_call

logger = logging.getLogger(__name__)


class VAPIWebhookRouter:
    """Unified webhook router for all VAPI tool calls and events."""

    def __init__(self):
        """Initialize the webhook router with handler mappings."""
        self.tool_routing_map = vapi_tools_registry.get_tool_routing_map()
        self.user_integration = VoiceUserIntegration()
        self.webhook_timeout = config.WEBHOOK_TIMEOUT

    async def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process incoming VAPI webhook.

        Args:
            payload: Webhook payload from VAPI
            headers: HTTP headers including signature

        Returns:
            Response data to send back to VAPI
        """
        try:
            # Validate webhook signature
            if not self._validate_webhook_signature(payload, headers):
                logger.warning("Invalid webhook signature")
                return {"error": "Invalid signature", "status": 401}

            # Log webhook event
            await self._log_webhook_event(payload)

            # Extract event type
            event_type = payload.get("message", {}).get("type")

            if event_type == "tool-calls":
                return await self._handle_tool_calls(payload)
            elif event_type == "function-call":
                return await self._handle_function_call(payload)
            elif event_type == "end-of-call-report":
                return await self._handle_call_end(payload)
            elif event_type == "conversation-update":
                return await self._handle_conversation_update(payload)
            elif event_type == "hang":
                return await self._handle_call_hang(payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {
                    "message": f"Event type {event_type} acknowledged",
                    "status": 200,
                }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"error": str(e), "status": 500}

    async def _handle_tool_calls(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls from VAPI assistant."""
        try:
            tool_calls = payload.get("message", {}).get("toolCalls", [])
            call_id = payload.get("message", {}).get("call", {}).get("id")

            if not tool_calls:
                return {"message": "No tool calls found", "status": 200}

            # Process all tool calls
            results = []
            for tool_call in tool_calls:
                result = await self._process_single_tool_call(
                    tool_call, payload, call_id
                )
                results.append(result)

            # Return aggregated results
            all_successful = all(result.get("success", False) for result in results)

            return {
                "message": "Tool calls processed",
                "results": results,
                "all_successful": all_successful,
                "status": 200,
            }

        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            return {"error": str(e), "status": 500}

    async def _handle_function_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle individual function call from VAPI."""
        try:
            function_call = payload.get("message", {}).get("functionCall", {})
            call_id = payload.get("message", {}).get("call", {}).get("id")

            if not function_call:
                return {"message": "No function call found", "status": 200}

            result = await self._process_single_tool_call(
                function_call, payload, call_id
            )

            return {
                "message": "Function call processed",
                "result": result,
                "status": 200,
            }

        except Exception as e:
            logger.error(f"Error handling function call: {e}")
            return {"error": str(e), "status": 500}

    async def _process_single_tool_call(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any], call_id: str
    ) -> Dict[str, Any]:
        """
        Process a single tool call by routing to appropriate handler.

        Args:
            tool_call: Individual tool call data
            payload: Full webhook payload for context
            call_id: Call ID for tracking

        Returns:
            Result from the specific handler
        """
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})

            # Parse parameters if they come as a JSON string (common with VAPI webhooks)
            if isinstance(parameters, str):
                try:
                    import json

                    parameters = json.loads(parameters)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse general tool parameters JSON: {parameters}, error: {e}"
                    )
                    parameters = {}

            user_id = self._extract_user_id(payload)

            if not function_name:
                return {"success": False, "error": "No function name provided"}

            logger.info(f"Processing tool call: {function_name} for call {call_id}")

            # Get handler type from routing map
            handler_type = self.tool_routing_map.get(function_name)

            if not handler_type:
                logger.warning(f"Unknown tool function: {function_name}")
                return {"success": False, "error": f"Unknown tool: {function_name}"}

            # Route to appropriate handler
            if handler_type == "crisis_handler":
                return await self._handle_crisis_tool(tool_call, payload)
            elif handler_type == "general_handler":
                return await self._handle_general_tool(tool_call, payload)
            elif handler_type == "scheduling_handler":
                return await self._handle_scheduling_tool(tool_call, payload)
            elif handler_type == "safety_checkup_handler":
                return await self._handle_safety_checkup_tool(tool_call, payload)
            elif handler_type == "image_handler":
                return await self._handle_image_tool(tool_call, payload)
            elif handler_type == "memory_handler":
                return await self._handle_memory_tool(tool_call, payload)
            elif handler_type == "vapi_native":
                # Native VAPI tools don't need handling - VAPI processes them
                return {
                    "success": True,
                    "message": f"{function_name} handled natively by VAPI",
                    "handled_by": "vapi_native",
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown handler type: {handler_type}",
                }

        except Exception as e:
            logger.error(f"Error processing tool call {function_name}: {e}")
            return {"success": False, "error": str(e)}

    # === CRISIS TOOLS HANDLER ===
    async def _handle_crisis_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle crisis intervention tools - consolidated implementation."""
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})

            # Parse parameters if they come as a JSON string (common with VAPI webhooks)
            if isinstance(parameters, str):
                try:
                    import json

                    parameters = json.loads(parameters)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse crisis tool parameters JSON: {parameters}, error: {e}"
                    )
                    parameters = {}

            user_id = self._extract_user_id(payload)

            if function_name == "query_safety_network_contacts":
                # Query safety network database for emergency contacts via API
                try:
                    # Use the real safety network API endpoint
                    safety_api_base = "http://localhost:8000"  # Adjust as needed
                    url = f"{safety_api_base}/safety-network/contacts"

                    # Extract crisis level for emergency contact filtering
                    crisis_level = parameters.get("crisis_level", "moderate")
                    emergency_only = crisis_level in ["high", "critical"]

                    # For crisis situations, bypass auth by calling the manager directly
                    from services.safety_network.manager import SafetyNetworkManager

                    contacts = SafetyNetworkManager.get_user_safety_contacts(
                        user_id=user_id,
                        active_only=True,
                        emergency_only=emergency_only,
                        ordered_by_priority=True,
                    )

                    # Format response for VAPI
                    return {
                        "success": True,
                        "has_contacts": len(contacts) > 0,
                        "contact_count": len(contacts),
                        "primary_contact": (contacts[0] if contacts else None),
                        "crisis_level": crisis_level,
                        "message": f"Found {len(contacts)} emergency contacts for {crisis_level} crisis",
                        "next_action": (
                            "initiate_contact" if contacts else "fallback_to_hotlines"
                        ),
                    }
                except Exception as e:
                    logger.error(f"Error querying safety network: {e}")
                    return {
                        "success": False,
                        "error": "EMERGENCY_CONTACT_SYSTEM_DOWN",
                        "message": "Emergency contact system temporarily unavailable",
                        "fallback_action": "use_crisis_hotlines",
                    }

            elif function_name == "initiate_emergency_contact_outreach":
                # Initiate contact outreach directly through manager for crisis situations
                try:
                    from services.safety_network.manager import SafetyNetworkManager

                    # Get the specific contact
                    contacts = SafetyNetworkManager.get_user_safety_contacts(
                        user_id=user_id,
                        active_only=True,
                        emergency_only=True,
                    )

                    # Find the requested contact
                    contact_id = parameters.get("contact_id")
                    target_contact = None
                    for contact in contacts:
                        if contact["id"] == contact_id:
                            target_contact = contact
                            break

                    if not target_contact:
                        return {
                            "success": False,
                            "error": "CONTACT_NOT_FOUND",
                            "message": "Emergency contact not found",
                        }

                    # Determine best contact method
                    available_methods = target_contact.get(
                        "allowed_communication_methods", []
                    )
                    preferred_method = parameters.get("preferred_method", "sms")

                    if preferred_method not in available_methods:
                        # Fall back to first available method
                        preferred_method = (
                            available_methods[0] if available_methods else "phone"
                        )

                    # Log the outreach attempt initiation
                    SafetyNetworkManager.log_contact_attempt(
                        safety_contact_id=contact_id,
                        user_id=user_id,
                        contact_method=preferred_method,
                        success=True,
                        reason=f"Crisis intervention: {parameters.get('crisis_level', 'moderate')}",
                        initiated_by="vapi_webhook",
                        message_content=parameters.get(
                            "message_context", "Emergency support needed"
                        ),
                        contact_metadata={
                            "crisis_level": parameters.get("crisis_level", "moderate")
                        },
                    )

                    return {
                        "success": True,
                        "outreach_initiated": True,
                        "contact_method": preferred_method,
                        "contact_name": target_contact.get(
                            "full_name", "Emergency Contact"
                        ),
                        "phone_number": target_contact.get(
                            "phone_number"
                        ),  # For VAPI SMS tool
                        "message": f"Outreach initiated to {target_contact.get('full_name', 'Emergency Contact')} via {preferred_method}",
                        "vapi_action": (
                            "send_sms" if preferred_method == "sms" else "make_call"
                        ),
                    }

                except Exception as e:
                    logger.error(f"Error initiating outreach: {e}")
                    return {
                        "success": False,
                        "error": "OUTREACH_SYSTEM_ERROR",
                        "message": "Contact outreach system error",
                    }

            elif function_name == "log_crisis_intervention":
                # Log crisis intervention outcome directly through manager
                try:
                    # Parse parameters if they come as a JSON string (common with VAPI webhooks)
                    if isinstance(parameters, str):
                        try:
                            import json

                            parameters = json.loads(parameters)
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse logging tool parameters JSON: {parameters}, error: {e}"
                            )
                            parameters = {}

                    from services.safety_network.manager import SafetyNetworkManager

                    # Log the contact attempt outcome
                    contact_id = parameters.get("contact_id")
                    contact_method_str = parameters.get("contact_method", "sms")
                    contact_success = parameters.get("contact_success", False)
                    crisis_summary = parameters.get(
                        "crisis_summary", "Crisis intervention via VAPI"
                    )

                    logger.info(
                        f"Attempting to log crisis intervention: contact_id={contact_id}, method={contact_method_str}, success={contact_success}"
                    )

                    log_success = SafetyNetworkManager.log_contact_attempt(
                        safety_contact_id=contact_id,
                        user_id=user_id,
                        contact_method=contact_method_str,
                        success=contact_success,
                        reason="Crisis intervention outcome",
                        initiated_by="vapi_webhook",
                        message_content=crisis_summary,
                        contact_metadata={
                            "next_steps": parameters.get("next_steps"),
                            "logged_via": "crisis_intervention_api",
                        },
                    )

                    logger.info(f"Log contact attempt result: {log_success}")

                    if log_success:
                        return {
                            "success": True,
                            "logged": True,
                            "intervention_outcome": (
                                "successful"
                                if parameters.get("contact_success", False)
                                else "failed"
                            ),
                            "message": "Crisis intervention logged successfully",
                            "follow_up_required": bool(parameters.get("next_steps")),
                        }
                    else:
                        return {
                            "success": False,
                            "error": "LOGGING_FAILED",
                            "message": "Failed to log crisis intervention",
                        }

                except Exception as e:
                    logger.error(f"Error logging crisis intervention: {e}")
                    return {
                        "success": False,
                        "error": "LOGGING_SYSTEM_ERROR",
                        "message": "Crisis logging system error",
                    }

            else:
                return {
                    "success": False,
                    "error": f"Unknown crisis tool: {function_name}",
                }

        except Exception as e:
            logger.error(f"Error in crisis tool handler: {e}")
            return {"success": False, "error": f"Crisis handler error: {str(e)}"}

    def _get_user_jwt(self, user_id: str) -> str:
        """
        Get JWT token for user to make authenticated API calls.
        In production, this would retrieve or generate a valid JWT for the user.
        For now, return a placeholder.
        """
        # TODO: Implement proper JWT retrieval/generation for user
        return "vapi-system-token"  # Placeholder - needs real implementation

    # === GENERAL TOOLS HANDLER ===
    async def _handle_general_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general voice management tools."""
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})

            # Parse parameters if they come as a JSON string (common with VAPI webhooks)
            if isinstance(parameters, str):
                try:
                    import json

                    parameters = json.loads(parameters)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse general tool parameters JSON: {parameters}, error: {e}"
                    )
                    parameters = {}

            if function_name == "pause_conversation":
                duration = parameters.get("duration_seconds", 10)
                message = parameters.get("pause_message", "Taking a moment to pause...")

                # Simulate pause (in real implementation, this would use VAPI's pause functionality)
                await asyncio.sleep(min(duration, 30))  # Cap at 30 seconds for safety

                return {
                    "success": True,
                    "message": f"Conversation paused for {duration} seconds",
                    "action": "pause_completed",
                }

            elif function_name == "check_system_status":
                operation_type = parameters.get("operation_type")

                # Check status of recent operations
                status = await self._check_operation_status(operation_type)

                return {
                    "success": True,
                    "operation_type": operation_type,
                    "status": status,
                    "message": f"System status check completed for {operation_type}",
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown general tool: {function_name}",
                }

        except Exception as e:
            logger.error(f"Error in general tool handler: {e}")
            return {"success": False, "error": f"General handler error: {str(e)}"}

    # === SCHEDULING TOOLS HANDLER ===
    async def _handle_scheduling_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle scheduling tools via existing integration."""
        try:
            # Use the existing scheduling integration
            return await handle_vapi_tool_call(payload)

        except Exception as e:
            logger.error(f"Error in scheduling tool handler: {e}")
            return {"success": False, "error": f"Scheduling handler error: {str(e)}"}

    # === SAFETY CHECKUP TOOLS HANDLER ===
    async def _handle_safety_checkup_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle safety checkup tools."""
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})
            user_id = self._extract_user_id(payload)

            # Make API call to safety network service
            safety_api_base = config.get_api_endpoint("safety_network")

            endpoint_map = {
                "schedule_safety_checkup": "/checkup/schedules",
                "get_safety_checkup_schedules": "/checkup/schedules",
                "cancel_safety_checkup": "/checkup/schedules/{checkup_id}",
            }

            endpoint = endpoint_map.get(function_name)
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unknown safety checkup tool: {function_name}",
                }

            url = f"{safety_api_base}{endpoint}"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.webhook_timeout)
            ) as session:
                if function_name == "get_safety_checkup_schedules":
                    async with session.get(url) as response:
                        result = await response.json()
                elif function_name == "cancel_safety_checkup":
                    checkup_id = parameters.get("checkup_id")
                    url = f"{safety_api_base}/checkup/schedules/{checkup_id}"
                    async with session.delete(url) as response:
                        result = await response.json()
                else:  # schedule_safety_checkup
                    async with session.post(
                        url, json={**parameters, "user_id": user_id}
                    ) as response:
                        result = await response.json()

                return {
                    "success": response.status == 200,
                    "result": result,
                    "function": function_name,
                    "handled_by": "safety_network_api",
                }

        except Exception as e:
            logger.error(f"Error in safety checkup tool handler: {e}")
            return {
                "success": False,
                "error": f"Safety checkup handler error: {str(e)}",
            }

    # === IMAGE GENERATION TOOLS HANDLER ===
    async def _handle_image_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle image generation tools via API calls."""
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})
            user_id = self._extract_user_id(payload)

            if not user_id:
                return {"success": False, "error": "User ID not found in payload"}

            # Make API call to image generation service
            image_api_base = config.get_api_endpoint("image_generation")

            # Route to appropriate image endpoint
            endpoint_map = {
                "process_drawing_reflection": "/analyze",
                "validate_visualization_input": "/validate",
                "generate_visual_prompt": "/prompt",
                "create_emotional_image": "/create",
                "get_image_generation_status": f"/status/{parameters.get('user_id', user_id)}",
            }

            endpoint = endpoint_map.get(function_name)
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unknown image tool: {function_name}",
                }

            url = f"{image_api_base}{endpoint}"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.webhook_timeout)
            ) as session:
                if function_name == "get_image_generation_status":
                    async with session.get(url) as response:
                        result = await response.json()
                else:
                    async with session.post(
                        url, json={**parameters, "user_id": user_id}
                    ) as response:
                        result = await response.json()

                return {
                    "success": response.status == 200,
                    "result": result,
                    "function": function_name,
                    "handled_by": "image_service_api",
                }

        except Exception as e:
            logger.error(f"Error in image tool handler: {e}")
            return {"success": False, "error": f"Image handler error: {str(e)}"}

    # === MEMORY TOOLS HANDLER ===
    async def _handle_memory_tool(
        self, tool_call: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle memory tools via API calls."""
        try:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})
            user_id = self._extract_user_id(payload)

            if not user_id:
                return {"success": False, "error": "User ID not found in payload"}

            # Make API call to memory service
            memory_api_base = config.get_api_endpoint("memory")

            # Route to appropriate memory endpoint
            endpoint_map = {
                "search_user_memories": "/search",
                "store_conversation_memory": "/push",
                "get_memory_insights": f"/insights?user_id={user_id}",
            }

            endpoint = endpoint_map.get(function_name)
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unknown memory tool: {function_name}",
                }

            url = f"{memory_api_base}{endpoint}"

            # Map parameters to match memory service API
            if function_name == "store_conversation_memory":
                # Map registry parameters to memory service parameters
                api_params = {
                    "content": parameters.get("memory_content")
                    or parameters.get("content"),
                    "type": parameters.get("memory_type", "voice_interaction"),
                    "metadata": {
                        "importance": parameters.get("importance_level"),
                        "tags": parameters.get("tags", []),
                        **(parameters.get("metadata", {})),
                    },
                }
            elif function_name == "search_user_memories":
                # Map search parameters
                api_params = {
                    "query": parameters.get("query"),
                    "top_k": parameters.get("top_k", 5),
                }
            else:
                api_params = parameters

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.webhook_timeout)
            ) as session:
                if function_name == "get_memory_insights":
                    async with session.get(url) as response:
                        result = await response.json()
                else:
                    async with session.post(
                        url, json={**api_params, "user_id": user_id}
                    ) as response:
                        result = await response.json()

                return {
                    "success": response.status == 200,
                    "result": result,
                    "function": function_name,
                    "handled_by": "memory_service_api",
                }

        except Exception as e:
            logger.error(f"Error in memory tool handler: {e}")
            return {"success": False, "error": f"Memory handler error: {str(e)}"}

    # === CALL EVENT HANDLERS ===
    async def _handle_call_end(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle end-of-call report."""
        try:
            call_data = payload.get("call", {})
            call_id = call_data.get("id")

            if call_id:
                await self._store_call_summary(call_data)

            return {"message": "Call end processed", "status": 200}

        except Exception as e:
            logger.error(f"Error handling call end: {e}")
            return {"error": str(e), "status": 500}

    async def _handle_conversation_update(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle conversation updates."""
        try:
            message_data = payload.get("message", {})
            call_id = message_data.get("call", {}).get("id")

            if call_id:
                await self._update_call_metadata(call_id, message_data)

            return {"message": "Conversation update processed", "status": 200}

        except Exception as e:
            logger.error(f"Error handling conversation update: {e}")
            return {"error": str(e), "status": 500}

    async def _handle_call_hang(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call hang up."""
        try:
            call_id = payload.get("call", {}).get("id")

            if call_id:
                await self._mark_call_ended(call_id, "hang_up")

            return {"message": "Call hang processed", "status": 200}

        except Exception as e:
            logger.error(f"Error handling call hang: {e}")
            return {"error": str(e), "status": 500}

    # === UTILITY METHODS ===
    def _validate_webhook_signature(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        """Validate webhook signature."""
        if not config.WEBHOOK_SECRET:
            logger.warning("No webhook secret configured - skipping validation")
            return True

        try:
            signature = headers.get("x-vapi-signature", "")
            if not signature:
                return False

            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = hmac.new(
                config.WEBHOOK_SECRET.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False

    def _extract_user_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from webhook payload."""
        return (
            payload.get("message", {}).get("call", {}).get("metadata", {}).get("userId")
        )

    async def _check_operation_status(self, operation_type: str) -> Dict[str, Any]:
        """Check status of recent operations."""
        try:
            with get_db() as db:
                from datetime import timedelta

                recent_time = datetime.utcnow() - timedelta(minutes=5)

                # Check recent webhook events for failures
                recent_events = (
                    db.query(WebhookEvent)
                    .filter(WebhookEvent.created_at >= recent_time)
                    .all()
                )

                failed_events = [
                    e
                    for e in recent_events
                    if e.event_type.endswith("_failed") or "error" in e.event_type
                ]

                return {
                    "status": "healthy" if not failed_events else "degraded",
                    "recent_failures": len(failed_events),
                    "total_recent_events": len(recent_events),
                }

        except Exception as e:
            logger.error(f"Error checking operation status: {e}")
            return {"status": "unknown", "error": str(e)}

    async def _log_webhook_event(self, payload: Dict[str, Any]) -> None:
        """Log webhook event to database."""
        try:
            with get_db() as db:
                event = WebhookEvent(
                    event_type=payload.get("message", {}).get("type", "unknown"),
                    payload_data=payload,
                )
                db.add(event)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to log webhook event: {e}")

    async def _store_call_summary(self, call_data: Dict[str, Any]) -> None:
        """Store call summary without transcript."""
        try:
            with get_db() as db:
                call_id = call_data.get("id")
                analysis = call_data.get("analysis", {})

                # Find call record
                call_record = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if call_record:
                    # Create summary without transcript
                    summary = CallSummary(
                        call_id=call_record.id,
                        user_id=call_record.user_id,
                        summary_json={
                            "sentiment": analysis.get("sentiment"),
                            "summary": analysis.get("summary"),
                            "key_topics": analysis.get("keyTopics", []),
                            "action_items": analysis.get("actionItems", []),
                            "emotional_state": analysis.get("emotionalState"),
                        },
                        sentiment=analysis.get("sentiment"),
                        key_topics=analysis.get("keyTopics", []),
                        action_items=analysis.get("actionItems", []),
                        emotional_state=analysis.get("emotionalState"),
                    )
                    db.add(summary)
                    db.commit()

        except Exception as e:
            logger.error(f"Error storing call summary: {e}")

    async def _update_call_metadata(
        self, call_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Update call metadata."""
        try:
            with get_db() as db:
                call_record = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if call_record:
                    # Update any relevant metadata
                    call_record.updated_at = datetime.utcnow()
                    db.commit()

        except Exception as e:
            logger.error(f"Error updating call metadata: {e}")

    async def _mark_call_ended(self, call_id: str, end_reason: str) -> None:
        """Mark call as ended."""
        try:
            with get_db() as db:
                call_record = (
                    db.query(VoiceCall)
                    .filter(VoiceCall.vapi_call_id == call_id)
                    .first()
                )

                if call_record:
                    call_record.status = "completed"
                    call_record.ended_at = datetime.utcnow()
                    db.commit()

        except Exception as e:
            logger.error(f"Error marking call ended: {e}")


# Global router instance
vapi_webhook_router = VAPIWebhookRouter()
