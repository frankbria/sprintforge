"""Tests for Monte Carlo simulation API endpoints."""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.auth import create_jwt_token
from app.main import app


class TestSimulationEndpoint:
    """Test suite for POST /api/v1/projects/{project_id}/simulate endpoint."""

    @pytest.fixture
    def valid_simulation_request(self):
        """Valid simulation request payload."""
        return {
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "distribution_type": "triangular",
                    "optimistic": 1.0,
                    "most_likely": 3.0,
                    "pessimistic": 5.0,
                    "dependencies": "",
                },
                {
                    "task_id": "TASK-2",
                    "distribution_type": "triangular",
                    "optimistic": 2.0,
                    "most_likely": 4.0,
                    "pessimistic": 6.0,
                    "dependencies": "TASK-1",
                },
            ],
            "project_start_date": "2025-01-15",
            "iterations": 10000,
            "holidays": ["2025-01-20", "2025-02-14"],
            "percentiles": [10, 50, 90, 95, 99],
        }

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user data."""
        user_id = str(uuid4())
        return {
            "sub": user_id,
            "email": "test@example.com",
            "name": "Test User",
        }

    @pytest.fixture
    def auth_token(self, mock_user):
        """Generate valid JWT token for testing."""
        return create_jwt_token(mock_user, expires_delta=60)

    @pytest.fixture
    def auth_headers(self, auth_token):
        """HTTP headers with authentication."""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.mark.asyncio
    async def test_run_simulation_success(
        self, valid_simulation_request, auth_headers, mock_user
    ):
        """Test successful simulation execution."""
        project_id = uuid4()

        # Mock the SimulationService response
        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 8.5,
            "confidence_intervals": {
                10: 6.0,
                50: 8.5,
                90: 11.0,
                95: 12.0,
                99: 14.0,
            },
            "mean_duration": 8.5,
            "median_duration": 8.5,
            "std_deviation": 2.1,
            "iterations_run": 10000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 2,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["project_id"] == str(project_id)
            assert data["project_duration_days"] == 8.5
            assert data["iterations_run"] == 10000
            assert data["task_count"] == 2
            assert "confidence_intervals" in data
            assert len(data["confidence_intervals"]) == 5

    @pytest.mark.asyncio
    async def test_run_simulation_missing_auth(self, valid_simulation_request):
        """Test simulation request without authentication."""
        project_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=valid_simulation_request,
            )

        # FastAPI returns 403 when HTTPBearer credential is missing
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_run_simulation_invalid_token(self, valid_simulation_request):
        """Test simulation request with invalid token."""
        project_id = uuid4()
        headers = {"Authorization": "Bearer invalid_token_here"}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=valid_simulation_request,
                headers=headers,
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_run_simulation_project_not_found(
        self, valid_simulation_request, auth_headers
    ):
        """Test simulation for non-existent project."""
        project_id = uuid4()

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.side_effect = ValueError("Project not found")
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_run_simulation_invalid_parameters(
        self, valid_simulation_request, auth_headers
    ):
        """Test simulation with invalid parameters (non-'not found' ValueError)."""
        project_id = uuid4()

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.side_effect = ValueError(
                "Invalid task configuration: negative duration"
            )
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_run_simulation_invalid_iterations(
        self, valid_simulation_request, auth_headers
    ):
        """Test validation for invalid iteration count."""
        project_id = uuid4()
        invalid_request = valid_simulation_request.copy()
        invalid_request["iterations"] = 50  # Below minimum of 100

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=invalid_request,
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        errors = response.json()["detail"]
        assert any("iterations" in str(error).lower() for error in errors)

    @pytest.mark.asyncio
    async def test_run_simulation_iterations_too_high(
        self, valid_simulation_request, auth_headers
    ):
        """Test validation for iterations exceeding maximum."""
        project_id = uuid4()
        invalid_request = valid_simulation_request.copy()
        invalid_request["iterations"] = 200000  # Above maximum of 100000

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=invalid_request,
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_run_simulation_missing_required_fields(self, auth_headers):
        """Test validation for missing required fields."""
        project_id = uuid4()
        incomplete_request = {
            "tasks": [],  # Missing task data
            # Missing project_start_date
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=incomplete_request,
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_run_simulation_invalid_distribution_type(
        self, valid_simulation_request, auth_headers
    ):
        """Test validation for invalid distribution type."""
        project_id = uuid4()
        invalid_request = valid_simulation_request.copy()
        invalid_request["tasks"][0]["distribution_type"] = "invalid_type"

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=invalid_request,
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_run_simulation_empty_task_list(
        self, valid_simulation_request, auth_headers
    ):
        """Test simulation with empty task list."""
        project_id = uuid4()
        invalid_request = valid_simulation_request.copy()
        invalid_request["tasks"] = []

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/simulate",
                json=invalid_request,
                headers=auth_headers,
            )

        # Pydantic validation catches empty list (min_length=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_run_simulation_service_error(
        self, valid_simulation_request, auth_headers
    ):
        """Test handling of internal service errors."""
        project_id = uuid4()

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.side_effect = RuntimeError(
                "Simulation engine failure"
            )
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_run_simulation_default_parameters(self, auth_headers):
        """Test simulation with default optional parameters."""
        project_id = uuid4()
        minimal_request = {
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "distribution_type": "triangular",
                    "optimistic": 1.0,
                    "most_likely": 3.0,
                    "pessimistic": 5.0,
                    "dependencies": "",
                }
            ],
            "project_start_date": "2025-01-15",
            # iterations defaults to 10000
            # holidays defaults to None
            # percentiles defaults to [10, 50, 90, 95, 99]
        }

        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 3.2,
            "confidence_intervals": {10: 2.0, 50: 3.0, 90: 4.5, 95: 5.0, 99: 6.0},
            "mean_duration": 3.2,
            "median_duration": 3.0,
            "std_deviation": 1.1,
            "iterations_run": 10000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 1,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=minimal_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["iterations_run"] == 10000  # Default value used

    @pytest.mark.asyncio
    async def test_run_simulation_uniform_distribution(self, auth_headers):
        """Test simulation with uniform distribution."""
        project_id = uuid4()
        uniform_request = {
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "distribution_type": "uniform",
                    "min_duration": 2.0,
                    "max_duration": 8.0,
                    "dependencies": "",
                }
            ],
            "project_start_date": "2025-01-15",
            "iterations": 5000,
        }

        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 5.0,
            "confidence_intervals": {10: 3.0, 50: 5.0, 90: 7.0, 95: 7.5, 99: 8.0},
            "mean_duration": 5.0,
            "median_duration": 5.0,
            "std_deviation": 1.5,
            "iterations_run": 5000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 1,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=uniform_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_run_simulation_normal_distribution(self, auth_headers):
        """Test simulation with normal distribution."""
        project_id = uuid4()
        normal_request = {
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "distribution_type": "normal",
                    "mean": 5.0,
                    "std_dev": 1.0,
                    "dependencies": "",
                }
            ],
            "project_start_date": "2025-01-15",
            "iterations": 8000,
        }

        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 5.1,
            "confidence_intervals": {10: 3.5, 50: 5.0, 90: 6.5, 95: 7.0, 99: 8.0},
            "mean_duration": 5.1,
            "median_duration": 5.0,
            "std_deviation": 1.0,
            "iterations_run": 8000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 1,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=normal_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_run_simulation_complex_dependencies(self, auth_headers):
        """Test simulation with complex task dependencies."""
        project_id = uuid4()
        complex_request = {
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "distribution_type": "triangular",
                    "optimistic": 1.0,
                    "most_likely": 2.0,
                    "pessimistic": 3.0,
                    "dependencies": "",
                },
                {
                    "task_id": "TASK-2",
                    "distribution_type": "triangular",
                    "optimistic": 2.0,
                    "most_likely": 3.0,
                    "pessimistic": 4.0,
                    "dependencies": "TASK-1",
                },
                {
                    "task_id": "TASK-3",
                    "distribution_type": "triangular",
                    "optimistic": 1.0,
                    "most_likely": 2.0,
                    "pessimistic": 3.0,
                    "dependencies": "TASK-1",
                },
                {
                    "task_id": "TASK-4",
                    "distribution_type": "triangular",
                    "optimistic": 3.0,
                    "most_likely": 5.0,
                    "pessimistic": 7.0,
                    "dependencies": "TASK-2,TASK-3",
                },
            ],
            "project_start_date": "2025-01-15",
            "iterations": 15000,
        }

        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 12.5,
            "confidence_intervals": {
                10: 9.0,
                50: 12.0,
                90: 16.0,
                95: 18.0,
                99: 20.0,
            },
            "mean_duration": 12.5,
            "median_duration": 12.0,
            "std_deviation": 3.2,
            "iterations_run": 15000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 4,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=complex_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["task_count"] == 4

    @pytest.mark.asyncio
    async def test_openapi_schema_includes_simulation(self):
        """Test that simulation endpoint is documented in OpenAPI schema."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        openapi_spec = response.json()

        # Check that simulation endpoint exists in paths
        simulation_path = "/api/v1/projects/{project_id}/simulate"
        assert simulation_path in openapi_spec["paths"]
        assert "post" in openapi_spec["paths"][simulation_path]

        # Check endpoint documentation
        endpoint_spec = openapi_spec["paths"][simulation_path]["post"]
        assert "summary" in endpoint_spec
        assert "description" in endpoint_spec
        assert "requestBody" in endpoint_spec
        assert "responses" in endpoint_spec

        # Check authentication is required
        assert "security" in endpoint_spec or "security" in openapi_spec

    @pytest.mark.asyncio
    async def test_response_format_validation(
        self, valid_simulation_request, auth_headers
    ):
        """Test that response matches expected schema."""
        project_id = uuid4()

        mock_result = {
            "project_id": str(project_id),
            "project_duration_days": 8.5,
            "confidence_intervals": {10: 6.0, 50: 8.5, 90: 11.0, 95: 12.0, 99: 14.0},
            "mean_duration": 8.5,
            "median_duration": 8.5,
            "std_deviation": 2.1,
            "iterations_run": 10000,
            "simulation_timestamp": datetime.utcnow().isoformat(),
            "task_count": 2,
        }

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.return_value = mock_result
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate all required fields are present
        required_fields = [
            "project_id",
            "project_duration_days",
            "confidence_intervals",
            "mean_duration",
            "median_duration",
            "std_deviation",
            "iterations_run",
            "simulation_timestamp",
            "task_count",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate data types
        assert isinstance(data["project_duration_days"], (int, float))
        assert isinstance(data["confidence_intervals"], dict)
        assert isinstance(data["mean_duration"], (int, float))
        assert isinstance(data["iterations_run"], int)
        assert isinstance(data["task_count"], int)

    @pytest.mark.asyncio
    async def test_run_simulation_permission_error(
        self, valid_simulation_request, auth_headers
    ):
        """Test simulation when user lacks project permissions."""
        project_id = uuid4()

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.side_effect = PermissionError(
                "User does not have access to this project"
            )
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            # Should return 404 to avoid information disclosure
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_run_simulation_unexpected_error(
        self, valid_simulation_request, auth_headers
    ):
        """Test handling of unexpected errors."""
        project_id = uuid4()

        with patch("app.api.endpoints.simulation.SimulationService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.run_simulation.side_effect = Exception(
                "Unexpected database connection failure"
            )
            mock_service.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/simulate",
                    json=valid_simulation_request,
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "unexpected" in response.json()["detail"].lower()
