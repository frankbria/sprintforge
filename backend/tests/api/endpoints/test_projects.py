"""Tests for project API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from jose import jwt
from httpx import AsyncClient

from app.main import app
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM
from app.models.user import User
from app.models.project import Project


class TestProjectEndpoints:
    """Test project API endpoints."""

    def create_test_token(self, user_id: str, email: str, expired: bool = False) -> str:
        """Create a test JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": exp.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "provider": "google"
        }

        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    def create_test_user(self) -> User:
        """Create a test user model."""
        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={}
        )
        return user

    def create_test_project(self, user_id: UUID) -> Project:
        """Create a test project model."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            owner_id=user_id,
            configuration={
                "project_name": "Test Project",
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "holidays": ["2025-01-01"],
                "features": {
                    "monte_carlo": True,
                    "critical_path": True,
                    "gantt_chart": True,
                },
            },
            template_version="1.0",
            is_public=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return project

    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test successful project creation."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        project_data = {
            "name": "My Agile Project",
            "description": "Sprint planning for Q1 2025",
            "template_id": "agile_advanced",
            "configuration": {
                "project_name": "My Agile Project",
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "holidays": ["2025-01-01", "2025-12-25"],
                "features": {
                    "monte_carlo": True,
                    "critical_path": True,
                    "gantt_chart": True,
                },
            },
        }

        with patch('app.services.project_service.ProjectService.create_project') as mock_create:
            created_project = self.create_test_project(user.id)
            created_project.name = project_data["name"]
            created_project.description = project_data["description"]
            mock_create.return_value = created_project

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/projects",
                    json=project_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == project_data["name"]
            assert data["description"] == project_data["description"]
            assert "id" in data
            assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(self):
        """Test project creation without authentication."""
        project_data = {
            "name": "Test Project",
            "configuration": {
                "project_name": "Test Project",
                "sprint_pattern": "YY.Q.#",
            },
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 403  # No Bearer token

    @pytest.mark.asyncio
    async def test_create_project_invalid_configuration(self):
        """Test project creation with invalid configuration."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        project_data = {
            "name": "Test Project",
            "configuration": {
                "working_days": [8, 9, 10],  # Invalid weekdays
            },
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/projects",
                json=project_data,
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_projects_success(self):
        """Test successful project listing."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        projects = [self.create_test_project(user.id) for _ in range(3)]

        with patch('app.services.project_service.ProjectService.list_projects') as mock_list:
            mock_list.return_value = (projects, 3)

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/projects",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert data["limit"] == 20
            assert data["offset"] == 0
            assert len(data["projects"]) == 3

    @pytest.mark.asyncio
    async def test_list_projects_with_pagination(self):
        """Test project listing with pagination parameters."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        projects = [self.create_test_project(user.id) for _ in range(5)]

        with patch('app.services.project_service.ProjectService.list_projects') as mock_list:
            mock_list.return_value = (projects[:2], 5)

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/projects?limit=2&offset=0",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 5
            assert data["limit"] == 2
            assert len(data["projects"]) == 2

    @pytest.mark.asyncio
    async def test_list_projects_with_search(self):
        """Test project listing with search parameter."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        projects = [self.create_test_project(user.id)]

        with patch('app.services.project_service.ProjectService.list_projects') as mock_list:
            mock_list.return_value = (projects, 1)

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/projects?search=agile",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_projects_with_sorting(self):
        """Test project listing with sorting."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        projects = [self.create_test_project(user.id)]

        with patch('app.services.project_service.ProjectService.list_projects') as mock_list:
            mock_list.return_value = (projects, 1)

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/projects?sort=-created_at",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            # Verify sort parameter was passed correctly
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            assert call_kwargs["sort_desc"] is True
            assert call_kwargs["sort_by"] == "created_at"

    @pytest.mark.asyncio
    async def test_get_project_success(self):
        """Test successful project retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get:
            mock_check.return_value = True
            mock_get.return_value = project

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(project.id)
            assert data["name"] == project.name

    @pytest.mark.asyncio
    async def test_get_project_not_found(self):
        """Test project retrieval for non-existent project."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project_id = uuid4()

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_project_unauthorized_user(self):
        """Test project retrieval by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404  # Return 404 to avoid information leakage

    @pytest.mark.asyncio
    async def test_update_project_success(self):
        """Test successful project update."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
        }

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.update_project') as mock_update:
            mock_check.return_value = True
            updated_project = self.create_test_project(user.id)
            updated_project.name = update_data["name"]
            updated_project.description = update_data["description"]
            mock_update.return_value = updated_project

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    f"/api/v1/projects/{project.id}",
                    json=update_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == update_data["name"]
            assert data["description"] == update_data["description"]

    @pytest.mark.asyncio
    async def test_update_project_partial(self):
        """Test partial project update (configuration only)."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        update_data = {
            "configuration": {
                "sprint_duration_weeks": 3
            }
        }

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.update_project') as mock_update:
            mock_check.return_value = True
            updated_project = self.create_test_project(user.id)
            mock_update.return_value = updated_project

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    f"/api/v1/projects/{project.id}",
                    json=update_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_project_unauthorized(self):
        """Test project update by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        update_data = {"name": "Unauthorized Update"}

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    f"/api/v1/projects/{project.id}",
                    json=update_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_success(self):
        """Test successful project deletion."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.delete_project') as mock_delete:
            mock_check.return_value = True
            mock_delete.return_value = True

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/v1/projects/{project.id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self):
        """Test deletion of non-existent project."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project_id = uuid4()

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.delete_project') as mock_delete:
            mock_check.return_value = True
            mock_delete.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/v1/projects/{project_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_unauthorized(self):
        """Test project deletion by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/v1/projects/{project.id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404


class TestProjectServiceUnit:
    """Unit tests for ProjectService."""

    @pytest.mark.asyncio
    async def test_create_project_generates_project_id(self):
        """Test that project creation generates project_id in configuration."""
        from app.services.project_service import ProjectService
        from app.schemas.project import ProjectCreate, ProjectConfigSchema

        mock_db = AsyncMock()
        service = ProjectService(mock_db)

        user_id = uuid4()
        project_data = ProjectCreate(
            name="Test Project",
            description="Test Description",
            configuration=ProjectConfigSchema(
                project_name="Test Project",
                sprint_pattern="YY.Q.#",
            )
        )

        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        project = await service.create_project(user_id, project_data)

        assert "project_id" in project.configuration
        assert project.configuration["project_id"] is not None
        assert project.configuration["project_name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_list_projects_search_filter(self):
        """Test project listing with search filter."""
        from app.services.project_service import ProjectService

        mock_db = AsyncMock()
        service = ProjectService(mock_db)

        user_id = uuid4()

        # Mock execute to return empty results for simplicity
        mock_result = Mock()
        mock_result.scalar_one.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        projects, total = await service.list_projects(
            user_id=user_id,
            search="agile"
        )

        assert total == 0
        assert projects == []
        # Verify execute was called
        assert mock_db.execute.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.api.endpoints.projects", "--cov=app.services.project_service"])
