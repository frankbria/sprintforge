"""Tests for Excel generation API endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from jose import jwt
from httpx import AsyncClient

from app.main import app
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM
from app.models.user import User
from app.models.project import Project


class TestExcelEndpoints:
    """Test Excel generation API endpoints."""

    def create_test_token(self, user_id: str, email: str) -> str:
        """Create a test JWT token."""
        payload = {
            "sub": user_id,
            "email": email,
            "exp": (datetime.now(timezone.utc).timestamp()) + 1800,
            "iat": datetime.now(timezone.utc).timestamp(),
            "provider": "google",
        }
        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    def create_test_user(self) -> User:
        """Create a test user model."""
        return User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={},
        )

    def create_test_project(self, owner_id) -> Project:
        """Create a test project model."""
        return Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            owner_id=owner_id,
            configuration={
                "template_id": "agile_basic",
                "project_id": "test_proj_123",
                "project_name": "Test Project",
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "features": {
                    "monte_carlo": False,
                    "critical_path": True,
                    "gantt_chart": True,
                },
            },
            template_version="1.0",
            is_public=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_generate_excel_success(self):
        """Test successful Excel generation."""
        user = self.create_test_user()
        project = self.create_test_project(user.id)
        token = self.create_test_token(str(user.id), user.email)

        # Mock Excel generation to return dummy bytes
        mock_excel_bytes = b"Excel file content"

        with patch("app.services.project_service.ProjectService.check_owner_permission") as mock_check, \
             patch("app.services.project_service.ProjectService.get_project") as mock_get, \
             patch("app.services.excel_service.ExcelService.generate_excel") as mock_generate:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_generate.return_value = mock_excel_bytes

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project.id}/generate",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "attachment" in response.headers["content-disposition"]
            assert ".xlsx" in response.headers["content-disposition"]
            assert response.content == mock_excel_bytes

    @pytest.mark.asyncio
    async def test_generate_excel_unauthorized(self):
        """Test Excel generation without authentication."""
        project_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{project_id}/generate",
            )

        assert response.status_code == 403  # HTTPBearer returns 403 for missing token

    @pytest.mark.asyncio
    async def test_generate_excel_project_not_found(self):
        """Test Excel generation for non-existent project."""
        user = self.create_test_user()
        project_id = uuid4()
        token = self.create_test_token(str(user.id), user.email)

        with patch("app.services.project_service.ProjectService.check_owner_permission") as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project_id}/generate",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 404
            assert response.json()["detail"] == "Project not found"

    @pytest.mark.asyncio
    async def test_generate_excel_unauthorized_user(self):
        """Test Excel generation by non-owner user."""
        user = self.create_test_user()
        other_user = self.create_test_user()
        project = self.create_test_project(other_user.id)
        token = self.create_test_token(str(user.id), user.email)

        with patch("app.services.project_service.ProjectService.check_owner_permission") as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project.id}/generate",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 404  # Security: return 404 instead of 403

    @pytest.mark.asyncio
    async def test_generate_excel_invalid_configuration(self):
        """Test Excel generation with invalid project configuration."""
        user = self.create_test_user()
        project = self.create_test_project(user.id)
        token = self.create_test_token(str(user.id), user.email)

        with patch("app.services.project_service.ProjectService.check_owner_permission") as mock_check, \
             patch("app.services.project_service.ProjectService.get_project") as mock_get, \
             patch("app.services.excel_service.ExcelService.generate_excel") as mock_generate:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_generate.side_effect = ValueError("Invalid sprint pattern")

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project.id}/generate",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 400
            assert "Invalid project configuration" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_excel_server_error(self):
        """Test Excel generation with server error."""
        user = self.create_test_user()
        project = self.create_test_project(user.id)
        token = self.create_test_token(str(user.id), user.email)

        with patch("app.services.project_service.ProjectService.check_owner_permission") as mock_check, \
             patch("app.services.project_service.ProjectService.get_project") as mock_get, \
             patch("app.services.excel_service.ExcelService.generate_excel") as mock_generate:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_generate.side_effect = Exception("Unexpected error")

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/projects/{project.id}/generate",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 500
            assert response.json()["detail"] == "Failed to generate Excel template"


class TestExcelServiceUnit:
    """Unit tests for ExcelService."""

    @pytest.mark.asyncio
    async def test_filename_generation(self):
        """Test filename generation with project name sanitization."""
        from app.services.excel_service import ExcelService

        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={},
        )

        project = Project(
            id=uuid4(),
            name="Test Project!@# With Special Characters",
            description="Test",
            owner_id=user.id,
            configuration={"template_id": "agile_basic"},
            template_version="1.0",
            is_public=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock()
        service = ExcelService(mock_db)
        filename = service.get_filename(project)

        # Check filename is sanitized
        assert filename.endswith(".xlsx")
        assert "!" not in filename
        assert "@" not in filename
        assert "#" not in filename
        assert " " not in filename  # Spaces should be replaced with underscores

    @pytest.mark.asyncio
    async def test_project_config_mapping(self):
        """Test mapping Project model to Excel ProjectConfig."""
        from app.services.excel_service import ExcelService

        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={},
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test Description",
            owner_id=user.id,
            configuration={
                "template_id": "agile_advanced",
                "project_id": "proj_123",
                "project_name": "Test Project",
                "sprint_pattern": "PI-N.Sprint-M",
                "features": {
                    "monte_carlo": True,
                    "critical_path": True,
                },
            },
            template_version="1.0",
            is_public=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock()
        service = ExcelService(mock_db)
        config = service._map_project_to_config(project)

        assert config.project_id == "proj_123"
        assert config.project_name == "Test Project"
        assert config.sprint_pattern == "PI-N.Sprint-M"
        assert config.features["monte_carlo"] is True
        assert config.features["critical_path"] is True
        assert config.metadata["template_id"] == "agile_advanced"
        assert config.metadata["description"] == "Test Description"

    @pytest.mark.asyncio
    async def test_excel_generation_integration(self):
        """Test actual Excel generation without mocking."""
        from app.services.excel_service import ExcelService

        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={},
        )

        project = Project(
            id=uuid4(),
            name="Integration Test Project",
            description="Testing actual Excel generation",
            owner_id=user.id,
            configuration={
                "template_id": "agile_basic",
                "project_id": "int_test_123",
                "project_name": "Integration Test",
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "features": {
                    "monte_carlo": False,
                    "critical_path": True,
                },
            },
            template_version="1.0",
            is_public=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Create mock database that handles commit
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        service = ExcelService(mock_db)

        # Test actual Excel generation
        excel_bytes = await service.generate_excel(project)

        # Verify Excel bytes were generated
        assert excel_bytes is not None
        assert len(excel_bytes) > 0
        assert isinstance(excel_bytes, bytes)

        # Verify it's an Excel file (starts with PK for zip/xlsx)
        assert excel_bytes[:2] == b"PK"

        # Verify database commit was called
        mock_db.commit.assert_called_once()

        # Verify last_generated_at was updated
        assert project.last_generated_at is not None
