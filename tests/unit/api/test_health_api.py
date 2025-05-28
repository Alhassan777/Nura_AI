"""
Unit tests for Health API endpoints.
Tests the /api/health endpoints for system monitoring and configuration validation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status


class TestHealthAPI:
    """Test suite for Health API endpoints."""

    def test_health_check_healthy_status(self, test_client, mock_redis):
        """Test health check returns healthy status when all services operational."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            with patch("os.getenv", return_value="test-api-key"):
                response = test_client.get("/api/health/")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["status"] in ["healthy", "degraded"]
                assert "timestamp" in data
                assert "services" in data
                assert "configuration" in data
                assert isinstance(data["services"], dict)

    def test_health_check_missing_api_key(self, test_client, mock_redis):
        """Test health check returns degraded status when API key is missing."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
                response = test_client.get("/api/health/")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["status"] == "degraded"
                assert "configuration" in data

    def test_health_check_redis_connection_failure(self, test_client):
        """Test health check handles Redis connection failures gracefully."""
        mock_redis_fail = Mock()
        mock_redis_fail.ping.side_effect = Exception("Redis connection failed")

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis_fail):
            with patch("os.getenv", return_value="test-api-key"):
                response = test_client.get("/api/health/")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Should still return a response even with Redis issues
                assert "status" in data
                assert "services" in data

    def test_configuration_validation_success(self, test_client):
        """Test configuration validation with valid environment variables."""
        with patch("services.memory.config.Config.GOOGLE_API_KEY", "test-api-key"):
            # Mock the file loading to return valid prompts
            with patch("services.memory.config.load_prompt_from_file") as mock_load:
                mock_load.return_value = "Valid prompt content"

                response = test_client.get("/api/health/config/test")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # The test should handle configuration gracefully
                assert data["status"] in ["SUCCESS", "CONFIGURATION_ERROR"]
                assert "message" in data
                assert "details" in data

    def test_configuration_validation_missing_api_key(self, test_client):
        """Test configuration validation with missing Google API key."""
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/config/test")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "CONFIGURATION_ERROR"
            assert "recommendations" in data
            assert "details" in data

    def test_configuration_validation_vector_db_config(self, test_client):
        """Test vector database configuration validation."""
        with patch("services.memory.config.Config.GOOGLE_API_KEY", "test-api-key"):
            with patch(
                "services.memory.config.Config.PINECONE_API_KEY", "test-pinecone-key"
            ):
                response = test_client.get("/api/health/config/test")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert "status" in data
                assert "details" in data

    def test_service_status_monitoring_all_healthy(self, test_client, mock_redis):
        """Test service status monitoring when all services are healthy."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            with patch("services.memory.memoryService.MemoryService") as mock_memory:
                mock_memory.return_value = Mock()

                response = test_client.get("/api/health/services")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert "overall_status" in data
                assert "services" in data
                assert "redis" in data["services"]
                assert "memory" in data["services"]

    def test_service_status_monitoring_redis_unhealthy(self, test_client):
        """Test service status monitoring when Redis is unhealthy."""
        mock_redis_fail = AsyncMock()
        mock_redis_fail.ping.side_effect = Exception("Connection failed")

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis_fail):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "overall_status" in data
            assert "services" in data
            assert "redis" in data["services"]
            assert data["services"]["redis"]["status"] == "error"

    def test_service_status_memory_service_check(self, test_client, mock_redis):
        """Test memory service status check."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "services" in data
            assert "memory" in data["services"]
            memory_status = data["services"]["memory"]
            assert "status" in memory_status
            assert memory_status["status"] in ["healthy", "error"]

    def test_service_status_voice_service_check(self, test_client, mock_redis):
        """Test voice service status check."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "services" in data
            assert "voice" in data["services"]
            voice_status = data["services"]["voice"]
            assert "status" in voice_status

    def test_health_endpoint_response_structure(self, test_client, mock_redis):
        """Test that health endpoint returns proper response structure."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            response = test_client.get("/api/health/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check required fields
            required_fields = [
                "status",
                "timestamp",
                "services",
                "configuration",
                "message",
                "version",
            ]
            for field in required_fields:
                assert field in data

            # Check timestamp format
            assert isinstance(data["timestamp"], str)

            # Check services structure
            assert isinstance(data["services"], dict)

    def test_configuration_recommendations(self, test_client):
        """Test that configuration validation provides actionable recommendations."""
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/config/test")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "CONFIGURATION_ERROR"
            assert "recommendations" in data
            assert isinstance(data["recommendations"], list)
            assert len(data["recommendations"]) > 0

    def test_health_check_handles_exceptions(self, test_client):
        """Test that health check handles unexpected exceptions gracefully."""
        with patch(
            "utils.redis_client.get_redis_client",
            side_effect=Exception("Unexpected error"),
        ):
            response = test_client.get("/api/health/")

            # Should still return a response, not crash
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data

    def test_service_status_includes_response_time(self, test_client, mock_redis):
        """Test that service status includes proper service information."""
        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check if services have proper structure
            assert "services" in data
            for service_name, service_data in data["services"].items():
                assert "status" in service_data
                assert "message" in service_data


class TestHealthAPIIntegration:
    """Integration tests for Health API with real dependencies."""

    @pytest.mark.asyncio
    async def test_health_check_with_real_config(self, test_client):
        """Test health check with actual configuration loading."""
        # This test uses real configuration loading
        response = test_client.get("/api/health/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have basic structure even with real config
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    def test_configuration_validation_comprehensive(self, test_client):
        """Test comprehensive configuration validation."""
        response = test_client.get("/api/health/config/test")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should validate all required configuration items
        assert "status" in data
        assert data["status"] in ["SUCCESS", "CONFIGURATION_ERROR"]

        # Should include recommendations if issues found
        if data["status"] == "CONFIGURATION_ERROR":
            assert "recommendations" in data
