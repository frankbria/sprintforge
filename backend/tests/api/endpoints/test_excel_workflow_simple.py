"""
Simplified tests for Excel workflow API endpoints.

Tests the basic happy path and critical error cases.
"""

import io
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from openpyxl import Workbook

from app.core.auth import create_jwt_token
from app.main import app


class TestExcelWorkflowEndpoints:
    """Test suite for Excel workflow endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {"sub": str(uuid4()), "email": "test@example.com"}

    @pytest.fixture
    def auth_token(self, mock_user):
        """Generate JWT token."""
        return create_jwt_token(mock_user, expires_delta=60)

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Authentication headers."""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.fixture
    def valid_excel_bytes(self):
        """Create valid Excel file bytes."""
        wb = Workbook()
        ws = wb.active
        ws.append(
            [
                "Task ID",
                "Task Name",
                "Optimistic",
                "Most Likely",
                "Pessimistic",
                "Dependencies",
            ]
        )
        ws.append(["TASK-1", "Test task", 1.0, 2.0, 3.0, ""])

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()

    @pytest.mark.asyncio
    async def test_upload_excel_and_simulate_success(
        self, auth_headers, mock_user, valid_excel_bytes
    ):
        """Test successful Excel upload and simulation."""
        project_id = uuid4()

        with patch(
            "app.services.excel_parser_service.ExcelParserService.parse_excel_file"
        ) as mock_parse, patch(
            "app.services.simulation_service.SimulationService.run_simulation"
        ) as mock_simulate, patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.save_simulation_result"
        ) as mock_save:
            # Mock parser
            from app.services.excel_parser_service import ParsedExcelData, ParsedTask

            mock_parse.return_value = ParsedExcelData(
                tasks=[
                    ParsedTask(
                        task_id="TASK-1",
                        task_name="Test task",
                        optimistic=1.0,
                        most_likely=2.0,
                        pessimistic=3.0,
                        dependencies="",
                    )
                ]
            )

            # Mock simulation
            from datetime import datetime

            from app.services.simulation_service import (
                SimulationResult as ServiceSimulationResult,
            )

            mock_simulate.return_value = ServiceSimulationResult(
                project_duration_days=5.0,
                confidence_intervals={10: 4.0, 50: 5.0, 90: 6.0},
                mean_duration=5.0,
                median_duration=5.0,
                std_deviation=0.5,
                iterations_run=10000,
                simulation_date=datetime.now(),
                task_count=1,
            )

            # Mock persistence
            mock_save.return_value = 123

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/excel/projects/{project_id}/simulate",
                    files={
                        "file": (
                            "test.xlsx",
                            valid_excel_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                    params={"iterations": 10000, "project_start_date": "2025-01-15"},
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["simulation_id"] == 123
            assert data["project_id"] == str(project_id)
            assert "download_url" in data

    @pytest.mark.asyncio
    async def test_upload_excel_file_too_large(self, auth_headers):
        """Test rejection of files larger than 10MB."""
        project_id = uuid4()
        large_file = b"0" * (11 * 1024 * 1024)  # 11MB

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/excel/projects/{project_id}/simulate",
                files={
                    "file": (
                        "large.xlsx",
                        large_file,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                params={"iterations": 10000, "project_start_date": "2025-01-15"},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, auth_headers):
        """Test rejection of non-Excel files."""
        project_id = uuid4()
        text_file = b"This is not an Excel file"

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/excel/projects/{project_id}/simulate",
                files={"file": ("test.txt", text_file, "text/plain")},
                params={"iterations": 10000, "project_start_date": "2025-01-15"},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    @pytest.mark.asyncio
    async def test_upload_excel_unauthorized(self, valid_excel_bytes):
        """Test upload without authentication."""
        project_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/excel/projects/{project_id}/simulate",
                files={
                    "file": (
                        "test.xlsx",
                        valid_excel_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                params={"iterations": 10000, "project_start_date": "2025-01-15"},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_download_template(self, auth_headers):
        """Test downloading blank template."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/excel/template",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    @pytest.mark.asyncio
    async def test_download_template_with_sample_data(self, auth_headers):
        """Test downloading template with sample data."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/excel/template",
                params={"include_sample_data": True},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_download_simulation_excel(self, auth_headers):
        """Test downloading Excel with simulation results."""
        simulation_id = 123

        with patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.get_simulation_result"
        ) as mock_get:
            # Mock database result
            from datetime import datetime

            mock_result = MagicMock()
            mock_result.id = simulation_id
            mock_result.project_id = uuid4()
            mock_result.mean_duration = 35.5
            mock_result.median_duration = 35.5
            mock_result.std_deviation = 8.2
            mock_result.confidence_intervals = {10: 28.0, 50: 35.5, 90: 45.0}
            mock_result.iterations = 10000
            mock_result.task_count = 7
            mock_result.created_at = datetime.now()
            mock_get.return_value = mock_result

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/excel/simulations/{simulation_id}/excel",
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            assert (
                response.headers["content-type"]
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    @pytest.mark.asyncio
    async def test_download_simulation_excel_not_found(self, auth_headers):
        """Test download with non-existent simulation ID."""
        simulation_id = 999

        with patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.get_simulation_result"
        ) as mock_get:
            mock_get.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/excel/simulations/{simulation_id}/excel",
                    headers=auth_headers,
                )

            assert response.status_code == status.HTTP_404_NOT_FOUND
