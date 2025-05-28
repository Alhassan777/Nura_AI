"""
Validation tests for Health API to ensure tests catch real issues.
These tests verify that our test suite actually detects real problems in the application logic.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status


class TestHealthAPIValidation:
    """Validation tests to ensure our tests catch real issues."""

    def test_configuration_missing_api_key_actually_fails(self, test_client):
        """Verify that missing API key actually causes configuration failure."""
        # This test ensures our mocking actually works and catches real config issues
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/config/test")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # This should actually fail when API key is missing
            assert data["status"] == "CONFIGURATION_ERROR"
            assert "missing_required" in data["details"]
            assert "GOOGLE_API_KEY" in data["details"]["missing_required"]

    def test_redis_connection_failure_detection(self, test_client):
        """Verify that Redis connection failures are actually detected."""
        # Create a mock that actually fails
        mock_redis_fail = AsyncMock()
        mock_redis_fail.ping.side_effect = ConnectionError("Redis connection failed")

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis_fail):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should detect the Redis failure
            assert "services" in data
            assert "redis" in data["services"]
            assert data["services"]["redis"]["status"] == "error"
            assert "Redis connection failed" in data["services"]["redis"]["message"]

    def test_memory_service_initialization_failure(self, test_client):
        """Verify that memory service initialization failures are detected."""
        # Mock MemoryService to fail during initialization
        with patch(
            "services.memory.memoryService.MemoryService",
            side_effect=Exception("Memory service init failed"),
        ):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should detect the memory service failure
            assert "services" in data
            assert "memory" in data["services"]
            assert data["services"]["memory"]["status"] == "error"
            assert "Memory service init failed" in data["services"]["memory"]["message"]

    def test_health_status_degraded_with_config_issues(self, test_client):
        """Verify that health status is degraded when there are configuration issues."""
        # Mock configuration to have issues
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should be degraded due to missing API key
            assert data["status"] == "degraded"
            assert data["configuration"]["has_configuration_issues"] is True

    def test_voice_service_missing_api_key(self, test_client):
        """Verify that voice service reports degraded status when API key is missing."""
        # Mock voice config to have missing API key
        with patch("services.voice.config.config.VAPI_API_KEY", None):
            response = test_client.get("/api/health/services")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should detect voice service degradation
            assert "services" in data
            assert "voice" in data["services"]
            # Voice service should be degraded without API key
            assert data["services"]["voice"]["status"] in ["degraded", "error"]

    def test_overall_status_calculation(self, test_client):
        """Verify that overall status is calculated correctly based on individual services."""
        # Mock multiple service failures
        mock_redis_fail = AsyncMock()
        mock_redis_fail.ping.side_effect = Exception("Redis down")

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis_fail):
            with patch(
                "services.memory.memoryService.MemoryService",
                side_effect=Exception("Memory down"),
            ):
                response = test_client.get("/api/health/services")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Overall status should reflect service failures
                assert "overall_status" in data
                # Should be error or degraded when multiple services fail
                assert data["overall_status"] in ["error", "degraded"]

    def test_configuration_recommendations_are_actionable(self, test_client):
        """Verify that configuration recommendations are actually helpful."""
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/config/test")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "CONFIGURATION_ERROR"
            assert "recommendations" in data
            recommendations = data["recommendations"]

            # Should have actionable recommendations
            assert len(recommendations) > 0
            assert any(
                "env" in rec.lower() for rec in recommendations
            )  # Should mention environment setup

    def test_timestamp_format_validation(self, test_client):
        """Verify that timestamps are in correct format."""
        response = test_client.get("/api/health/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "timestamp" in data
        timestamp = data["timestamp"]

        # Should be a valid timestamp string
        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be a reasonable timestamp length

    def test_service_response_structure_consistency(self, test_client):
        """Verify that all services return consistent response structure."""
        response = test_client.get("/api/health/services")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "services" in data
        services = data["services"]

        # All services should have consistent structure
        for service_name, service_data in services.items():
            assert "status" in service_data, f"Service {service_name} missing status"
            assert "message" in service_data, f"Service {service_name} missing message"
            assert service_data["status"] in [
                "healthy",
                "degraded",
                "error",
            ], f"Service {service_name} has invalid status: {service_data['status']}"

    def test_error_handling_doesnt_crash_application(self, test_client):
        """Verify that errors in health checks don't crash the application."""
        # Mock everything to fail
        with patch(
            "utils.redis_client.get_redis_client",
            side_effect=Exception("Everything is broken"),
        ):
            with patch(
                "services.memory.memoryService.MemoryService",
                side_effect=Exception("Memory exploded"),
            ):
                with patch(
                    "services.voice.config.config",
                    side_effect=Exception("Voice vanished"),
                ):
                    response = test_client.get("/api/health/")

                    # Should still return a response, not crash
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()

                    # Should have basic structure even when everything fails
                    assert "status" in data
                    assert "timestamp" in data
                    assert "services" in data


class TestHealthAPILogicValidation:
    """Tests to validate the actual business logic of health checks."""

    def test_configuration_validation_logic(self, test_client):
        """Test that configuration validation logic is working correctly."""
        # Test with valid config
        with patch("services.memory.config.Config.GOOGLE_API_KEY", "valid-key"):
            response = test_client.get("/api/health/config/test")
            data = response.json()
            assert data["status"] == "SUCCESS"

        # Test with invalid config
        with patch("services.memory.config.Config.GOOGLE_API_KEY", None):
            response = test_client.get("/api/health/config/test")
            data = response.json()
            assert data["status"] == "CONFIGURATION_ERROR"

    def test_service_health_aggregation_logic(self, test_client):
        """Test that service health aggregation works correctly."""
        # All services healthy
        with patch("utils.redis_client.get_redis_client") as mock_redis:
            mock_redis.return_value.ping = AsyncMock(return_value=True)
            with patch("services.memory.memoryService.MemoryService"):
                response = test_client.get("/api/health/services")
                data = response.json()

                # Should have healthy overall status when all services are healthy
                healthy_services = sum(
                    1
                    for service in data["services"].values()
                    if service["status"] == "healthy"
                )
                total_services = len(data["services"])

                # Logic validation: if most services are healthy, overall should be healthy
                if healthy_services >= total_services * 0.5:
                    assert data["overall_status"] in ["healthy", "degraded"]

    def test_real_vs_mocked_behavior_consistency(self, test_client):
        """Ensure mocked behavior matches real behavior patterns."""
        # This test helps ensure our mocks are realistic

        # Test real configuration loading
        response = test_client.get("/api/health/config/test")
        real_data = response.json()

        # The real response should match our expected patterns
        assert "status" in real_data
        assert real_data["status"] in ["SUCCESS", "CONFIGURATION_ERROR"]

        if real_data["status"] == "SUCCESS":
            assert "details" in real_data
            assert real_data["details"]["has_configuration_issues"] is False
        else:
            assert "recommendations" in real_data
            assert len(real_data["recommendations"]) > 0
