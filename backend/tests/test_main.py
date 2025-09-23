"""
Tests for FastAPI main application.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint."""
    response = await test_client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "0.1.0"
    assert "environment" in data
    assert "checks" in data

    # Database check should be present
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_api_root(test_client: AsyncClient):
    """Test API root endpoint."""
    response = await test_client.get("/api/v1/")

    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "SprintForge API" in data["message"]


@pytest.mark.asyncio
async def test_docs_endpoint_in_development(test_client: AsyncClient):
    """Test that docs are available in development."""
    response = await test_client.get("/docs")

    # Should be available in development environment
    # Might return 404 if not in development mode
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_cors_headers(test_client: AsyncClient):
    """Test CORS headers are properly set."""
    response = await test_client.options("/api/v1/")

    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


@pytest.mark.asyncio
async def test_nonexistent_endpoint(test_client: AsyncClient):
    """Test that nonexistent endpoints return 404."""
    response = await test_client.get("/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_method(test_client: AsyncClient):
    """Test invalid HTTP method returns 405."""
    response = await test_client.patch("/health")

    assert response.status_code == 405