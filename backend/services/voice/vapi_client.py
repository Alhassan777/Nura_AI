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
    ) -> Dict[str, Any]:
        """
        Create an outbound phone call.

        Args:
            assistant_id: Vapi assistant ID
            phone_number: Phone number to call (E.164 format)
            user_id: Our internal user ID
            custom_metadata: Additional metadata for the call

        Returns:
            Vapi call response
        """
        metadata = {"userId": user_id, "channel": "phone", **(custom_metadata or {})}

        payload = {
            "assistantId": assistant_id,
            "phoneNumber": phone_number,
            "metadata": metadata,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/call",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()

                call_data = response.json()
                logger.info(
                    f"Created outbound call {call_data.get('id')} for user {user_id}"
                )

                return call_data

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


# Global client instance
vapi_client = VapiClient()
