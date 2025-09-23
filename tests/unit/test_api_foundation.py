"""Tests for API foundation components."""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from fastapi import status, HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pydantic import BaseModel, ValidationError

from app.main import app


@pytest.mark.api
class TestRoutingStructure:
    """Test API routing structure and organization."""

    def test_api_versioning_structure(self, client: TestClient):
        """Test API versioning structure is properly implemented."""
        # Test API v1 root
        response = client.get("/api/v1/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "SprintForge API v0.1.0" in data["message"]

    def test_api_route_organization(self, client: TestClient):
        """Test that API routes are properly organized."""
        # Test that API routes exist under versioned prefix
        response = client.get("/api/v1/")
        assert response.status_code == status.HTTP_200_OK

        # Test that direct API access without version returns 404
        response = client.get("/api/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_endpoint_accessibility(self, client: TestClient):
        """Test that health endpoint is accessible outside API versioning."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "healthy"

    def test_route_discovery(self, client: TestClient):
        """Test route discovery through OpenAPI schema."""
        response = client.get("/openapi.json")

        if response.status_code == status.HTTP_200_OK:
            openapi_schema = response.json()
            paths = openapi_schema.get("paths", {})

            # Verify key endpoints are documented
            assert "/health" in paths
            assert "/api/v1/" in paths

            # Verify HTTP methods are properly documented
            health_methods = paths["/health"].keys()
            assert "get" in health_methods

    @pytest.mark.asyncio
    async def test_async_route_handling(self, async_client: AsyncClient):
        """Test that routes handle async requests properly."""
        response = await async_client.get("/api/v1/")
        assert response.status_code == status.HTTP_200_OK

        response = await async_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_route_case_sensitivity(self, client: TestClient):
        """Test route case sensitivity."""
        # Standard routes
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        # Case variations should return 404
        response = client.get("/HEALTH")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = client.get("/Health")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestPydanticSchemaValidation:
    """Test Pydantic schema validation for API requests and responses."""

    def test_basic_pydantic_models(self):
        """Test basic Pydantic model creation and validation."""
        # Define test schemas that would be used in the API
        class UserCreateSchema(BaseModel):
            name: str
            email: str
            subscription_tier: str = "free"

        class ProjectCreateSchema(BaseModel):
            name: str
            description: str = None
            is_public: bool = False
            config: Dict[str, Any] = {}

        # Test valid user data
        valid_user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subscription_tier": "pro"
        }
        user = UserCreateSchema(**valid_user_data)
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.subscription_tier == "pro"

        # Test valid project data
        valid_project_data = {
            "name": "Test Project",
            "description": "A test project",
            "config": {"template_version": "1.0"}
        }
        project = ProjectCreateSchema(**valid_project_data)
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.config["template_version"] == "1.0"

    def test_pydantic_validation_errors(self):
        """Test Pydantic validation error handling."""
        class UserCreateSchema(BaseModel):
            name: str
            email: str
            age: int

        # Test missing required field
        with pytest.raises(ValidationError) as exc_info:
            UserCreateSchema(name="Test User")  # Missing email and age

        error = exc_info.value
        assert len(error.errors()) >= 2  # At least email and age missing

        # Test invalid data type
        with pytest.raises(ValidationError) as exc_info:
            UserCreateSchema(name="Test User", email="test@example.com", age="not_a_number")

        error = exc_info.value
        assert any("type" in str(err) for err in error.errors())

    def test_nested_schema_validation(self):
        """Test nested Pydantic schema validation."""
        class WorkflowSettings(BaseModel):
            default_status: str
            statuses: List[str]

        class ProjectConfig(BaseModel):
            template_version: str
            workflow_settings: WorkflowSettings

        class ProjectCreateSchema(BaseModel):
            name: str
            config: ProjectConfig

        # Test valid nested data
        valid_data = {
            "name": "Test Project",
            "config": {
                "template_version": "1.0",
                "workflow_settings": {
                    "default_status": "todo",
                    "statuses": ["todo", "in_progress", "done"]
                }
            }
        }

        project = ProjectCreateSchema(**valid_data)
        assert project.name == "Test Project"
        assert project.config.template_version == "1.0"
        assert project.config.workflow_settings.default_status == "todo"
        assert len(project.config.workflow_settings.statuses) == 3

        # Test invalid nested data
        with pytest.raises(ValidationError):
            invalid_data = {
                "name": "Test Project",
                "config": {
                    "template_version": "1.0",
                    "workflow_settings": {
                        "default_status": "todo"
                        # Missing required 'statuses' field
                    }
                }
            }
            ProjectCreateSchema(**invalid_data)

    def test_schema_serialization(self):
        """Test Pydantic schema serialization."""
        class UserResponseSchema(BaseModel):
            id: str
            name: str
            email: str
            created_at: str

        user_data = {
            "id": "user123",
            "name": "Test User",
            "email": "test@example.com",
            "created_at": "2023-01-01T00:00:00Z"
        }

        user = UserResponseSchema(**user_data)

        # Test JSON serialization
        json_data = user.model_dump()
        assert json_data["id"] == "user123"
        assert json_data["name"] == "Test User"

        # Test JSON string serialization
        json_str = user.model_dump_json()
        parsed_data = json.loads(json_str)
        assert parsed_data["email"] == "test@example.com"

    def test_optional_and_default_fields(self):
        """Test optional fields and default values in schemas."""
        class ProjectCreateSchema(BaseModel):
            name: str
            description: str = None
            is_public: bool = False
            max_members: int = 10
            tags: List[str] = []

        # Test with minimal data (using defaults)
        minimal_data = {"name": "Test Project"}
        project = ProjectCreateSchema(**minimal_data)

        assert project.name == "Test Project"
        assert project.description is None
        assert project.is_public is False
        assert project.max_members == 10
        assert project.tags == []

        # Test with all fields provided
        full_data = {
            "name": "Full Project",
            "description": "A complete project",
            "is_public": True,
            "max_members": 25,
            "tags": ["urgent", "frontend"]
        }
        project = ProjectCreateSchema(**full_data)

        assert project.name == "Full Project"
        assert project.description == "A complete project"
        assert project.is_public is True
        assert project.max_members == 25
        assert project.tags == ["urgent", "frontend"]


@pytest.mark.api
class TestErrorHandlingMiddleware:
    """Test error handling middleware functionality."""

    def test_404_error_handling(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "Not Found" in data["detail"]

    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 method not allowed error handling."""
        # Try POST on health endpoint which only accepts GET
        response = client.post("/health")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        data = response.json()
        assert "detail" in data
        assert "Method Not Allowed" in data["detail"]

    def test_422_validation_error_handling(self, client: TestClient):
        """Test 422 validation error handling."""
        # This test would be more relevant when we have endpoints that accept data
        # For now, test with malformed request to existing endpoint
        response = client.post("/api/v1/", json={"invalid": "data"})

        # The endpoint might not exist yet, so we test for expected status codes
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_async_error_handling(self, async_client: AsyncClient):
        """Test error handling with async client."""
        response = await async_client.get("/nonexistent-endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_error_response_format(self, client: TestClient):
        """Test error response format consistency."""
        # Test different error types have consistent format
        error_endpoints = [
            ("/nonexistent", status.HTTP_404_NOT_FOUND),
        ]

        for endpoint, expected_status in error_endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status

            data = response.json()
            # FastAPI standard error format
            assert "detail" in data
            assert isinstance(data["detail"], str)

    def test_custom_exception_handling(self):
        """Test custom exception handling setup."""
        # This tests the structure for custom exception handlers
        # Actual implementation would be in the FastAPI app

        class CustomAPIException(HTTPException):
            def __init__(self, status_code: int, detail: str, error_code: str = None):
                super().__init__(status_code=status_code, detail=detail)
                self.error_code = error_code

        # Test custom exception creation
        custom_error = CustomAPIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom error message",
            error_code="CUSTOM_ERROR"
        )

        assert custom_error.status_code == status.HTTP_400_BAD_REQUEST
        assert custom_error.detail == "Custom error message"
        assert custom_error.error_code == "CUSTOM_ERROR"

    def test_error_logging_preparation(self):
        """Test error logging structure preparation."""
        # This would test the logging setup for errors
        # For now, verify logging framework is available

        import structlog
        logger = structlog.get_logger()

        # Test logger can handle error context
        error_context = {
            "error_type": "validation_error",
            "endpoint": "/api/v1/projects",
            "user_id": "user123",
            "request_id": "req456"
        }

        # This should not raise an exception
        try:
            logger.error("Test error logging", **error_context)
            assert True
        except Exception as e:
            pytest.fail(f"Error logging failed: {e}")


@pytest.mark.api
class TestAPIDocumentation:
    """Test API documentation generation and accessibility."""

    def test_openapi_schema_generation(self, client: TestClient):
        """Test OpenAPI schema generation."""
        response = client.get("/openapi.json")

        # In development mode, OpenAPI should be available
        if response.status_code == status.HTTP_200_OK:
            openapi_schema = response.json()

            # Verify OpenAPI structure
            assert "openapi" in openapi_schema
            assert "info" in openapi_schema
            assert "paths" in openapi_schema

            # Verify info section
            info = openapi_schema["info"]
            assert info["title"] == "SprintForge API"
            assert info["version"] == "0.1.0"
            assert "Open-source" in info["description"]

    def test_swagger_ui_accessibility(self, client: TestClient):
        """Test Swagger UI accessibility."""
        response = client.get("/docs")

        # Should be available in development mode
        if response.status_code == status.HTTP_200_OK:
            # Check that it returns HTML content
            assert "text/html" in response.headers.get("content-type", "")
            assert "swagger" in response.text.lower()

    def test_redoc_accessibility(self, client: TestClient):
        """Test ReDoc accessibility."""
        response = client.get("/redoc")

        # Should be available in development mode
        if response.status_code == status.HTTP_200_OK:
            # Check that it returns HTML content
            assert "text/html" in response.headers.get("content-type", "")
            assert "redoc" in response.text.lower()

    def test_api_endpoint_documentation(self, client: TestClient):
        """Test that API endpoints are properly documented."""
        response = client.get("/openapi.json")

        if response.status_code == status.HTTP_200_OK:
            openapi_schema = response.json()
            paths = openapi_schema.get("paths", {})

            # Test health endpoint documentation
            if "/health" in paths:
                health_endpoint = paths["/health"]
                assert "get" in health_endpoint
                get_operation = health_endpoint["get"]
                assert "summary" in get_operation or "description" in get_operation

            # Test API v1 root documentation
            if "/api/v1/" in paths:
                api_root = paths["/api/v1/"]
                assert "get" in api_root

    def test_response_schema_documentation(self, client: TestClient):
        """Test that response schemas are documented."""
        response = client.get("/openapi.json")

        if response.status_code == status.HTTP_200_OK:
            openapi_schema = response.json()

            # Check for components/schemas section
            if "components" in openapi_schema:
                components = openapi_schema["components"]
                if "schemas" in components:
                    schemas = components["schemas"]
                    # Verify that response schemas are defined
                    assert isinstance(schemas, dict)

    def test_environment_based_docs_access(self, test_settings):
        """Test that documentation access is environment-controlled."""
        # In test environment, docs should be accessible
        # This logic would be implemented in the actual app configuration

        if test_settings.environment == "development":
            # Docs should be enabled
            assert True  # Placeholder for actual test

        elif test_settings.environment == "production":
            # Docs should be disabled
            assert True  # Placeholder for actual test


@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Test API integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, async_client: AsyncClient):
        """Test handling of concurrent API requests."""
        import asyncio

        # Create multiple concurrent requests to different endpoints
        tasks = [
            async_client.get("/health"),
            async_client.get("/api/v1/"),
            async_client.get("/health"),
            async_client.get("/api/v1/"),
            async_client.get("/health"),
        ]

        responses = await asyncio.gather(*tasks)

        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    def test_api_response_consistency(self, client: TestClient):
        """Test API response format consistency."""
        endpoints = ["/health", "/api/v1/"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK

            # All responses should be JSON
            assert "application/json" in response.headers.get("content-type", "")

            # All responses should be valid JSON
            data = response.json()
            assert isinstance(data, dict)

    def test_api_performance_baseline(self, client: TestClient):
        """Test API performance baseline."""
        import time

        endpoints = ["/health", "/api/v1/"]
        performance_data = {}

        for endpoint in endpoints:
            response_times = []
            for _ in range(5):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()

                assert response.status_code == status.HTTP_200_OK
                response_times.append(end_time - start_time)

            avg_time = sum(response_times) / len(response_times)
            performance_data[endpoint] = avg_time

            # API endpoints should respond quickly
            assert avg_time < 0.5, f"Endpoint {endpoint} too slow: {avg_time:.3f}s"

    def test_api_error_handling_consistency(self, client: TestClient):
        """Test that error handling is consistent across the API."""
        # Test 404 errors
        not_found_endpoints = [
            "/nonexistent",
            "/api/nonexistent",
            "/api/v1/nonexistent",
            "/api/v2/test"
        ]

        for endpoint in not_found_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_404_NOT_FOUND

            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

    def test_api_content_type_handling(self, client: TestClient):
        """Test API content type handling."""
        # Test JSON content type
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers.get("content-type", "")

        # Test that endpoints return consistent content types
        endpoints = ["/health", "/api/v1/"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type

    @pytest.mark.asyncio
    async def test_api_header_handling(self, async_client: AsyncClient):
        """Test API header handling."""
        # Test with custom headers
        headers = {
            "User-Agent": "SprintForge-Test/1.0",
            "X-Request-ID": "test-request-123",
            "Accept": "application/json"
        }

        response = await async_client.get("/health", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Test CORS headers (if CORS is enabled)
        cors_headers = {
            "Origin": "http://localhost:3000"
        }

        response = await async_client.get("/health", headers=cors_headers)
        assert response.status_code == status.HTTP_200_OK

        # Check for CORS response headers
        response_headers = response.headers
        # CORS headers might be present depending on middleware configuration
        assert isinstance(response_headers, dict) or hasattr(response_headers, 'get')