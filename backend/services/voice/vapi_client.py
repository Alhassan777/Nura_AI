"""
Vapi API client for outbound calls and assistant management.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
import json

from .config import config

logger = logging.getLogger(__name__)


class VapiClient:
    """Client for interacting with Vapi REST API."""

    def __init__(self):
        self.base_url = config.VAPI_BASE_URL
        self.api_key = config.VAPI_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_outbound_call(
        self,
        assistant_id: str,
        phone_number: str,
        user_id: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
        phone_number_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an outbound phone call.

        Args:
            assistant_id: Vapi assistant ID
            phone_number: Phone number to call (E.164 format)
            user_id: Our internal user ID
            custom_metadata: Additional metadata for the call
            phone_number_id: Vapi phone number ID to call from (required for outbound calls)

        Returns:
            Vapi call response
        """

        # Validate required configuration
        if not self.api_key:
            raise ValueError(
                "VAPI_API_KEY is not configured. Please set the VAPI_API_KEY environment variable."
            )

        if not assistant_id or assistant_id == "default-assistant":
            raise ValueError(
                "Valid VAPI_ASSISTANT_ID is required. Please set a real Vapi assistant ID."
            )

        # Note: phoneNumberId may be optional for some Vapi accounts with default numbers
        # but typically required for outbound calls

        metadata = {"userId": user_id, "channel": "phone", **(custom_metadata or {})}

        # Format the payload according to Vapi documentation
        payload = {
            "assistantId": assistant_id,
            "customer": {"number": phone_number},
            "metadata": metadata,
        }

        # Add phoneNumberId if provided
        if phone_number_id:
            payload["phoneNumberId"] = phone_number_id

        logger.info(f"Vapi API payload: {payload}")
        logger.info(f"Using API key: {'SET' if self.api_key else 'NOT SET'}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/call",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )

                # Log response details for debugging
                logger.info(f"Vapi API response status: {response.status_code}")

                if response.status_code != 200:
                    response_text = response.text
                    logger.error(f"Vapi API error response: {response_text}")

                    try:
                        error_data = response.json()
                        logger.error(f"Vapi API error details: {error_data}")

                        # Provide helpful error messages
                        if response.status_code == 401:
                            raise ValueError(
                                "Authentication failed. Check your VAPI_API_KEY."
                            )
                        elif response.status_code == 400:
                            error_msg = error_data.get("message", "Bad request")
                            raise ValueError(
                                f"Vapi API validation error: {error_msg}. Check your assistant ID and phone number configuration."
                            )

                    except ValueError:
                        raise  # Re-raise our custom ValueError
                    except:
                        pass

                response.raise_for_status()

                call_data = response.json()
                logger.info(
                    f"Created outbound call {call_data.get('id')} for user {user_id}"
                )

                return call_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Vapi API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            raise ValueError(
                f"Vapi API error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to create outbound call: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating outbound call: {e}")
            raise

    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Get call details from Vapi.

        Args:
            call_id: Vapi call ID

        Returns:
            Call details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/call/{call_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting call {call_id}: {e}")
            raise

    async def list_assistants(self) -> List[Dict[str, Any]]:
        """
        List available assistants from Vapi.

        Returns:
            List of assistant configurations
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/assistant", headers=self.headers, timeout=30.0
                )
                response.raise_for_status()

                data = response.json()
                return data.get("assistants", [])

        except httpx.HTTPError as e:
            logger.error(f"Failed to list assistants: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing assistants: {e}")
            raise

    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Get specific assistant details.

        Args:
            assistant_id: Vapi assistant ID

        Returns:
            Assistant configuration
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get assistant {assistant_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting assistant {assistant_id}: {e}")
            raise

    async def transfer_call(
        self, call_id: str, transfer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transfer an active call to another phone number.

        Args:
            call_id: Vapi call ID
            transfer_data: Transfer configuration with destination details

        Returns:
            Transfer response from Vapi
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/call/{call_id}/transfer",
                    headers=self.headers,
                    json=transfer_data,
                    timeout=30.0,
                )
                response.raise_for_status()

                transfer_result = response.json()
                logger.info(f"Call transfer initiated for call {call_id}")

                return {
                    "success": True,
                    "transfer_id": transfer_result.get("transferId"),
                    "destination": transfer_data.get("destination", {}).get("number"),
                    "message": "Call transfer initiated successfully",
                }

        except httpx.HTTPError as e:
            logger.error(f"Failed to transfer call {call_id}: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text if hasattr(e, 'response') else str(e)}",
            }
        except Exception as e:
            logger.error(f"Unexpected error transferring call {call_id}: {e}")
            return {"success": False, "error": str(e)}

    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """
        End an active call.

        Args:
            call_id: Vapi call ID

        Returns:
            End call response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/call/{call_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "message": f"Call {call_id} ended successfully",
                }

        except httpx.HTTPError as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Unexpected error ending call {call_id}: {e}")
            return {"success": False, "error": str(e)}

    async def create_call(
        self,
        assistant_id: str,
        phone_number: str = None,
        phone_number_id: str = None,
        user_id: str = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a call (outbound phone call or other types).

        Args:
            assistant_id: Vapi assistant ID
            phone_number: Phone number to call (E.164 format) for outbound calls
            phone_number_id: Vapi phone number ID to call from
            user_id: Our internal user ID
            custom_metadata: Additional metadata for the call

        Returns:
            Vapi call response
        """
        if phone_number:
            # Import here to avoid circular imports
            from .config import config

            # Use provided phone_number_id or fall back to config
            calling_number_id = phone_number_id or config.VAPI_PHONE_NUMBER_ID

            # This is an outbound phone call
            return await self.create_outbound_call(
                assistant_id, phone_number, user_id, custom_metadata, calling_number_id
            )
        else:
            # This might be for other call types - for now just return the outbound call
            raise ValueError("Phone number is required for outbound calls")


# Global client instance
vapi_client = VapiClient()
