"""
Tests for voice utilities module.
Tests call mapping, event processing, and context management functionality.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Import the voice utilities
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../backend"))

from utils.voice import (
    store_call_mapping,
    get_customer_id,
    get_call_mapping,
    delete_call_mapping,
    extract_call_id_from_vapi_event,
    is_conversation_update_event,
    extract_user_message_from_event,
    store_conversation_context,
    get_conversation_context,
)


class TestCallMapping:
    """Test call mapping functionality."""

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_call_mapping_success(self, mock_get_redis):
        """Test successful call mapping storage."""
        # Mock Redis client with async methods
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(return_value=True)

        call_id = "call_123"
        customer_id = "customer_456"

        result = await store_call_mapping(call_id, customer_id)

        assert result is True
        mock_redis.setex.assert_called_once()

        # Verify the call arguments
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"vapi:call:{call_id}"  # key
        assert call_args[0][1] == 1800  # TTL (30 minutes * 60 seconds)

        # Verify the stored data structure
        stored_data = json.loads(call_args[0][2])
        assert stored_data["customerId"] == customer_id
        assert stored_data["mode"] == "web"
        assert "timestamp" in stored_data

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_call_mapping_with_custom_ttl(self, mock_get_redis):
        """Test call mapping storage with custom TTL."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(return_value=True)

        call_id = "call_123"
        customer_id = "customer_456"
        custom_ttl = 60  # 60 minutes

        result = await store_call_mapping(call_id, customer_id, ttl_minutes=custom_ttl)

        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # 60 minutes * 60 seconds

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_call_mapping_redis_failure(self, mock_get_redis):
        """Test call mapping storage when Redis fails."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection failed"))

        result = await store_call_mapping("call_123", "customer_456")

        assert result is False

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_customer_id_success(self, mock_get_redis):
        """Test successful customer ID retrieval."""
        call_id = "call_123"
        customer_id = "customer_456"
        stored_data = {
            "customerId": customer_id,
            "mode": "web",
            "timestamp": "2024-01-01T10:00:00Z",
        }

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))

        result = await get_customer_id(call_id)

        assert result == customer_id
        mock_redis.get.assert_called_once_with(f"vapi:call:{call_id}")

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_customer_id_not_found(self, mock_get_redis):
        """Test customer ID retrieval when mapping doesn't exist."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=None)

        result = await get_customer_id("nonexistent_call")

        assert result is None

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_customer_id_invalid_json(self, mock_get_redis):
        """Test customer ID retrieval with corrupted data."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value="invalid json")

        result = await get_customer_id("call_123")

        assert result is None

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_call_mapping_success(self, mock_get_redis):
        """Test successful full call mapping retrieval."""
        call_id = "call_123"
        stored_data = {
            "customerId": "customer_456",
            "mode": "web",
            "timestamp": "2024-01-01T10:00:00Z",
        }

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))

        result = await get_call_mapping(call_id)

        expected_data = stored_data.copy()
        expected_data["callId"] = call_id
        assert result == expected_data
        mock_redis.get.assert_called_once_with(f"vapi:call:{call_id}")

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_delete_call_mapping_success(self, mock_get_redis):
        """Test successful call mapping deletion."""
        call_id = "call_123"
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.delete = AsyncMock(return_value=1)  # 1 key deleted

        result = await delete_call_mapping(call_id)

        assert result is True
        mock_redis.delete.assert_called_once_with(f"vapi:call:{call_id}")

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_delete_call_mapping_not_found(self, mock_get_redis):
        """Test call mapping deletion when key doesn't exist."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.delete = AsyncMock(return_value=0)  # 0 keys deleted

        result = await delete_call_mapping("nonexistent_call")

        assert result is False


class TestEventProcessing:
    """Test Vapi event processing functionality."""

    def test_extract_call_id_from_call_start_event(self):
        """Test call ID extraction from call-start event."""
        event = {
            "type": "call-start",
            "call": {"id": "call_123456", "status": "in-progress"},
        }

        result = extract_call_id_from_vapi_event(event)
        assert result == "call_123456"

    def test_extract_call_id_from_call_end_event(self):
        """Test call ID extraction from call-end event."""
        event = {
            "type": "call-end",
            "call": {
                "id": "call_789012",
                "status": "ended",
                "endedReason": "user-hangup",
            },
        }

        result = extract_call_id_from_vapi_event(event)
        assert result == "call_789012"

    def test_extract_call_id_from_conversation_update(self):
        """Test call ID extraction from conversation-update event."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_345678"},
            "message": {"role": "user", "content": "Hello, I need help"},
        }

        result = extract_call_id_from_vapi_event(event)
        assert result == "call_345678"

    def test_extract_call_id_missing_call_object(self):
        """Test call ID extraction when call object is missing."""
        event = {"type": "some-event", "data": "some data"}

        result = extract_call_id_from_vapi_event(event)
        assert result is None

    def test_extract_call_id_missing_id_field(self):
        """Test call ID extraction when ID field is missing."""
        event = {"type": "call-start", "call": {"status": "in-progress"}}

        result = extract_call_id_from_vapi_event(event)
        assert result is None

    def test_is_conversation_update_event_true(self):
        """Test conversation update event detection - positive case."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_123"},
            "message": {"role": "user", "content": "Hello"},
        }

        result = is_conversation_update_event(event)
        assert result is True

    def test_is_conversation_update_event_false(self):
        """Test conversation update event detection - negative case."""
        event = {"type": "call-start", "call": {"id": "call_123"}}

        result = is_conversation_update_event(event)
        assert result is False

    def test_is_conversation_update_event_missing_type(self):
        """Test conversation update event detection with missing type."""
        event = {
            "call": {"id": "call_123"},
            "message": {"role": "user", "content": "Hello"},
        }

        result = is_conversation_update_event(event)
        assert result is False

    def test_extract_user_message_from_event_success(self):
        """Test successful user message extraction."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_123"},
            "message": {
                "role": "user",
                "content": "I'm feeling anxious today",
                "timestamp": "2024-01-01T10:00:00Z",
            },
        }

        result = extract_user_message_from_event(event)

        assert result == "I'm feeling anxious today"

    def test_extract_user_message_assistant_role(self):
        """Test user message extraction from assistant message (should return None)."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_123"},
            "message": {
                "role": "assistant",
                "content": "I understand you're feeling anxious",
                "timestamp": "2024-01-01T10:00:00Z",
            },
        }

        result = extract_user_message_from_event(event)
        assert result is None

    def test_extract_user_message_missing_message(self):
        """Test user message extraction when message object is missing."""
        event = {"type": "conversation-update", "call": {"id": "call_123"}}

        result = extract_user_message_from_event(event)
        assert result is None

    def test_extract_user_message_missing_content(self):
        """Test user message extraction when content is missing."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_123"},
            "message": {"role": "user", "timestamp": "2024-01-01T10:00:00Z"},
        }

        result = extract_user_message_from_event(event)
        assert result is None

    def test_extract_user_message_empty_content(self):
        """Test user message extraction with empty content."""
        event = {
            "type": "conversation-update",
            "call": {"id": "call_123"},
            "message": {
                "role": "user",
                "content": "",
                "timestamp": "2024-01-01T10:00:00Z",
            },
        }

        result = extract_user_message_from_event(event)
        assert result is None


class TestConversationContext:
    """Test conversation context management."""

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_conversation_context_success(self, mock_get_redis):
        """Test successful conversation context storage."""
        call_id = "call_123"
        context = {
            "user_id": "user_456",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "session_start": "2024-01-01T10:00:00Z",
        }

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(return_value=True)

        result = await store_conversation_context(call_id, context)

        assert result is True
        mock_redis.setex.assert_called_once()

        # Verify the call arguments
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"vapi:context:{call_id}"
        assert call_args[0][1] == 3600  # Default TTL (60 minutes * 60 seconds)

        stored_data = json.loads(call_args[0][2])
        # Check that original context data is preserved
        assert stored_data["user_id"] == context["user_id"]
        assert stored_data["conversation_history"] == context["conversation_history"]
        assert stored_data["session_start"] == context["session_start"]
        # Check that timestamp was added automatically
        assert "timestamp" in stored_data

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_conversation_context_with_custom_ttl(self, mock_get_redis):
        """Test conversation context storage with custom TTL."""
        call_id = "call_123"
        context = {"user_id": "user_456"}
        custom_ttl = 30  # 30 minutes

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(return_value=True)

        result = await store_conversation_context(
            call_id, context, ttl_minutes=custom_ttl
        )

        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 1800  # 30 minutes * 60 seconds

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_store_conversation_context_redis_failure(self, mock_get_redis):
        """Test conversation context storage when Redis fails."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection failed"))

        result = await store_conversation_context("call_123", {"user_id": "user_456"})

        assert result is False

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_conversation_context_success(self, mock_get_redis):
        """Test successful conversation context retrieval."""
        call_id = "call_123"
        context = {
            "user_id": "user_456",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=json.dumps(context))

        result = await get_conversation_context(call_id)

        assert result == context
        mock_redis.get.assert_called_once_with(f"vapi:context:{call_id}")

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_conversation_context_not_found(self, mock_get_redis):
        """Test conversation context retrieval when context doesn't exist."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=None)

        result = await get_conversation_context("nonexistent_call")

        assert result is None

    @pytest.mark.asyncio
    @patch("utils.voice.get_redis_client")
    async def test_get_conversation_context_invalid_json(self, mock_get_redis):
        """Test conversation context retrieval with corrupted data."""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value="invalid json")

        result = await get_conversation_context("call_123")

        assert result is None


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_extract_call_id_with_none_event(self):
        """Test call ID extraction with None event."""
        result = extract_call_id_from_vapi_event(None)
        assert result is None

    def test_extract_call_id_with_empty_event(self):
        """Test call ID extraction with empty event."""
        result = extract_call_id_from_vapi_event({})
        assert result is None

    def test_is_conversation_update_with_none_event(self):
        """Test conversation update detection with None event."""
        result = is_conversation_update_event(None)
        assert result is False

    def test_extract_user_message_with_none_event(self):
        """Test user message extraction with None event."""
        result = extract_user_message_from_event(None)
        assert result is None

    def test_complex_vapi_event_structure(self):
        """Test with complex, realistic Vapi event structure."""
        complex_event = {
            "type": "conversation-update",
            "timestamp": "2024-01-01T10:00:00.000Z",
            "call": {
                "id": "call_abc123def456",
                "status": "in-progress",
                "startedAt": "2024-01-01T09:58:30.000Z",
                "customer": {"number": "+1234567890"},
                "assistant": {"id": "assistant_789", "name": "Mental Health Assistant"},
            },
            "message": {
                "role": "user",
                "content": "I've been having trouble sleeping lately and feeling overwhelmed",
                "timestamp": "2024-01-01T10:00:00.000Z",
                "duration": 3.2,
                "endTime": "2024-01-01T10:00:03.200Z",
            },
            "artifact": {
                "messages": [
                    {
                        "role": "user",
                        "content": "I've been having trouble sleeping lately and feeling overwhelmed",
                    }
                ]
            },
        }

        # Test all extraction functions with complex event
        call_id = extract_call_id_from_vapi_event(complex_event)
        assert call_id == "call_abc123def456"

        is_conversation = is_conversation_update_event(complex_event)
        assert is_conversation is True

        user_message = extract_user_message_from_event(complex_event)
        assert (
            user_message
            == "I've been having trouble sleeping lately and feeling overwhelmed"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
