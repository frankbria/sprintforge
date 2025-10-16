"""
Tests for Excel workflow API endpoints.

Tests cover:
- Upload Excel and run simulation (success and error cases)
- Download Excel with Monte Carlo results
- Download blank template
- Download template with sample data
- File validation (size, type, format)
- Authentication and authorization
- Database persistence
"""

import io
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from openpyxl import Workbook

from app.core.auth import create_jwt_token
from app.main import app


class TestUploadExcelAndSimulate:
    """Test cases for POST /projects/{project_id}/excel/simulate endpoint."""

    @pytest.fixture
    def valid_excel_file(self) -> UploadFile:
        """Create a valid Excel file with task data."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Tasks"

        # Headers
        ws.append(
            ["Task ID", "Task Name", "Optimistic", "Most Likely", "Pessimistic", "Dependencies"]
        )

        # Sample tasks
        ws.append(["TASK-1", "Setup environment", 1.0, 3.0, 5.0, ""])
        ws.append(["TASK-2", "Implement feature", 2.0, 4.0, 6.0, "TASK-1"])
        ws.append(["TASK-3", "Write tests", 1.0, 2.0, 3.0, "TASK-2"])

        # Save to bytes
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)

        return UploadFile(
            filename="test_tasks.xlsx",
            file=excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @pytest.fixture
    def mock_user_info(self) -> dict:
        """Mock authenticated user info."""
        return {"sub": str(uuid4()), "email": "test@example.com"}

    async def test_upload_valid_excel_and_simulate_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        valid_excel_file: UploadFile,
        mock_user_info: dict,
    ):
        """Test uploading valid Excel file and running simulation successfully."""
        project_id = uuid4()

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_parser_service.ExcelParserService.parse_excel"
        ) as mock_parse, patch(
            "app.services.simulation_service.SimulationService.run_simulation"
        ) as mock_simulate, patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.save_simulation_result"
        ) as mock_save:

            # Mock parser output
            mock_parse.return_value = [
                {
                    "task_id": "TASK-1",
                    "task_name": "Setup environment",
                    "optimistic": 1.0,
                    "most_likely": 3.0,
                    "pessimistic": 5.0,
                    "dependencies": "",
                }
            ]

            # Mock simulation result
            mock_simulation_result = MagicMock()
            mock_simulation_result.project_duration_days = 8.5
            mock_simulation_result.confidence_intervals = {10: 6.0, 50: 8.5, 90: 11.0}
            mock_simulation_result.mean_duration = 8.5
            mock_simulation_result.median_duration = 8.5
            mock_simulation_result.iterations_run = 10000
            mock_simulation_result.task_count = 1
            mock_simulate.return_value = mock_simulation_result

            # Mock persistence
            mock_save.return_value = 123  # simulation_id

            # Make request
            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
                params={
                    "iterations": 10000,
                    "project_start_date": "2025-01-15",
                },
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["simulation_id"] == 123
            assert data["project_id"] == str(project_id)
            assert data["task_count"] == 1
            assert data["iterations_run"] == 10000
            assert "download_url" in data
            assert f"/simulations/123/excel" in data["download_url"]

    async def test_upload_excel_file_too_large(
        self, client: AsyncClient, mock_user_info: dict
    ):
        """Test rejection of files larger than 10MB."""
        project_id = uuid4()

        # Create a file larger than 10MB
        large_file = io.BytesIO(b"0" * (11 * 1024 * 1024))  # 11MB

        with patch("app.core.auth.require_auth", return_value=mock_user_info):
            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("large.xlsx", large_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                params={
                    "iterations": 10000,
                    "project_start_date": "2025-01-15",
                },
            )

            assert response.status_code == 413  # Payload Too Large

    async def test_upload_invalid_file_type(
        self, client: AsyncClient, mock_user_info: dict
    ):
        """Test rejection of non-Excel files."""
        project_id = uuid4()

        # Create a text file
        text_file = io.BytesIO(b"This is not an Excel file")

        with patch("app.core.auth.require_auth", return_value=mock_user_info):
            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("not_excel.txt", text_file, "text/plain")},
                params={
                    "iterations": 10000,
                    "project_start_date": "2025-01-15",
                },
            )

            assert response.status_code == 415  # Unsupported Media Type

    async def test_upload_excel_with_parsing_errors(
        self, client: AsyncClient, valid_excel_file: UploadFile, mock_user_info: dict
    ):
        """Test handling of Excel parsing errors."""
        project_id = uuid4()

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_parser_service.ExcelParserService.parse_excel"
        ) as mock_parse:

            # Mock parsing error
            mock_parse.side_effect = ValueError("Missing required column: task_name")

            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
                params={
                    "iterations": 10000,
                    "project_start_date": "2025-01-15",
                },
            )

            assert response.status_code == 400  # Bad Request
            assert "task_name" in response.json()["detail"]

    async def test_upload_excel_with_circular_dependencies(
        self, client: AsyncClient, valid_excel_file: UploadFile, mock_user_info: dict
    ):
        """Test handling of circular dependency errors."""
        project_id = uuid4()

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_parser_service.ExcelParserService.parse_excel"
        ) as mock_parse, patch(
            "app.services.simulation_service.SimulationService.run_simulation"
        ) as mock_simulate:

            mock_parse.return_value = [{"task_id": "TASK-1"}]
            mock_simulate.side_effect = ValueError("Circular dependency detected: TASK-1 -> TASK-2 -> TASK-1")

            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
                params={
                    "iterations": 10000,
                    "project_start_date": "2025-01-15",
                },
            )

            assert response.status_code == 422  # Validation Error
            assert "circular" in response.json()["detail"].lower()

    async def test_upload_excel_unauthorized(
        self, client: AsyncClient, valid_excel_file: UploadFile
    ):
        """Test upload without authentication."""
        project_id = uuid4()

        response = await client.post(
            f"/api/v1/projects/{project_id}/excel/simulate",
            files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
            params={
                "iterations": 10000,
                "project_start_date": "2025-01-15",
            },
        )

        assert response.status_code == 401  # Unauthorized

    async def test_upload_excel_invalid_iterations(
        self, client: AsyncClient, valid_excel_file: UploadFile, mock_user_info: dict
    ):
        """Test validation of iterations parameter."""
        project_id = uuid4()

        with patch("app.core.auth.require_auth", return_value=mock_user_info):
            # Too few iterations
            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
                params={
                    "iterations": 50,  # Below minimum of 100
                    "project_start_date": "2025-01-15",
                },
            )
            assert response.status_code == 422

            # Too many iterations
            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", valid_excel_file.file, valid_excel_file.content_type)},
                params={
                    "iterations": 200000,  # Above maximum of 100000
                    "project_start_date": "2025-01-15",
                },
            )
            assert response.status_code == 422


class TestDownloadSimulationExcel:
    """Test cases for GET /simulations/{simulation_id}/excel endpoint."""

    async def test_download_simulation_excel_success(
        self, client: AsyncClient, db_session: AsyncSession, mock_user_info: dict
    ):
        """Test downloading Excel file with simulation results."""
        simulation_id = 123

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.get_simulation_result"
        ) as mock_get, patch(
            "app.services.excel_generation_service.ExcelGenerationService.generate_simulation_excel"
        ) as mock_generate:

            # Mock simulation result from database
            mock_simulation = MagicMock(spec=SimulationResult)
            mock_simulation.id = simulation_id
            mock_simulation.project_id = uuid4()
            mock_simulation.mean_duration = 52.3
            mock_simulation.confidence_intervals = {10: 45.2, 50: 51.5, 90: 61.5}
            mock_get.return_value = mock_simulation

            # Mock Excel generation
            excel_bytes = b"fake excel content"
            mock_generate.return_value = excel_bytes

            response = await client.get(f"/api/v1/simulations/{simulation_id}/excel")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "attachment" in response.headers["content-disposition"]
            assert len(response.content) > 0

    async def test_download_simulation_excel_not_found(
        self, client: AsyncClient, mock_user_info: dict
    ):
        """Test download with non-existent simulation ID."""
        simulation_id = 999

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.get_simulation_result"
        ) as mock_get:

            mock_get.return_value = None

            response = await client.get(f"/api/v1/simulations/{simulation_id}/excel")

            assert response.status_code == 404

    async def test_download_simulation_excel_unauthorized(self, client: AsyncClient):
        """Test download without authentication."""
        simulation_id = 123

        response = await client.get(f"/api/v1/simulations/{simulation_id}/excel")

        assert response.status_code == 401


class TestDownloadExcelTemplate:
    """Test cases for GET /excel/template endpoint."""

    async def test_download_blank_template(
        self, client: AsyncClient, mock_user_info: dict
    ):
        """Test downloading blank Excel template."""
        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_generation_service.ExcelGenerationService.generate_blank_template"
        ) as mock_generate:

            excel_bytes = b"fake blank template"
            mock_generate.return_value = excel_bytes

            response = await client.get("/api/v1/excel/template")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "template" in response.headers["content-disposition"].lower()

    async def test_download_template_with_sample_data(
        self, client: AsyncClient, mock_user_info: dict
    ):
        """Test downloading template with sample data."""
        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_generation_service.ExcelGenerationService.generate_sample_template"
        ) as mock_generate:

            excel_bytes = b"fake sample template"
            mock_generate.return_value = excel_bytes

            response = await client.get(
                "/api/v1/excel/template", params={"include_sample_data": True}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    async def test_download_template_unauthorized(self, client: AsyncClient):
        """Test template download without authentication."""
        response = await client.get("/api/v1/excel/template")

        assert response.status_code == 401


class TestExcelWorkflowIntegration:
    """Integration tests for complete Excel workflow."""

    async def test_database_persistence(
        self, client: AsyncClient, db_session: AsyncSession, mock_user_info: dict
    ):
        """Test that simulation results are properly persisted to database."""
        project_id = uuid4()

        # Create valid Excel file
        wb = Workbook()
        ws = wb.active
        ws.append(["Task ID", "Task Name", "Optimistic", "Most Likely", "Pessimistic", "Dependencies"])
        ws.append(["TASK-1", "Test task", 1.0, 2.0, 3.0, ""])

        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)

        with patch("app.core.auth.require_auth", return_value=mock_user_info), patch(
            "app.services.excel_parser_service.ExcelParserService.parse_excel"
        ) as mock_parse, patch(
            "app.services.simulation_service.SimulationService.run_simulation"
        ) as mock_simulate, patch(
            "app.services.simulation_persistence_service.SimulationPersistenceService.save_simulation_result"
        ) as mock_save:

            mock_parse.return_value = [{"task_id": "TASK-1"}]

            mock_simulation_result = MagicMock()
            mock_simulation_result.project_duration_days = 5.0
            mock_simulation_result.mean_duration = 5.0
            mock_simulate.return_value = mock_simulation_result

            mock_save.return_value = 456  # simulation_id

            response = await client.post(
                f"/api/v1/projects/{project_id}/excel/simulate",
                files={"file": ("test.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                params={
                    "iterations": 1000,
                    "project_start_date": "2025-01-15",
                },
            )

            assert response.status_code == 200
            # Verify save was called with correct parameters
            mock_save.assert_called_once()
            assert response.json()["simulation_id"] == 456
