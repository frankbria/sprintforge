"""Tests for analytics API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta, date
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from jose import jwt
from httpx import AsyncClient

from app.main import app
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM
from app.models.user import User
from app.models.project import Project


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

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
    async def test_get_analytics_overview_success(self):
        """Test successful analytics overview retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.calculate_project_health_score') as mock_health, \
             patch('app.services.analytics_service.AnalyticsService.get_critical_path_metrics') as mock_critical, \
             patch('app.services.analytics_service.AnalyticsService.get_resource_utilization') as mock_resources, \
             patch('app.services.analytics_service.AnalyticsService.get_simulation_summary') as mock_simulation, \
             patch('app.services.analytics_service.AnalyticsService.get_progress_metrics') as mock_progress:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_health.return_value = 78.5
            mock_critical.return_value = {
                "critical_tasks": [uuid4(), uuid4()],
                "total_duration": 45,
                "float_time": {},
                "risk_tasks": [uuid4()],
                "path_stability_score": 78.5,
            }
            mock_resources.return_value = {
                "total_resources": 15,
                "allocated_resources": 12,
                "utilization_pct": 82.5,
                "over_allocated": [],
                "under_utilized": [],
                "resource_timeline": {},
            }
            mock_simulation.return_value = {
                "percentiles": {"p10": 38.2, "p50": 45.0, "p75": 52.5, "p90": 58.3, "p95": 62.7},
                "mean_duration": 45.8,
                "std_deviation": 8.2,
                "risk_level": "medium",
                "confidence_80pct_range": [40.5, 55.0],
                "histogram_data": [],
            }
            mock_progress.return_value = {
                "completion_pct": 67.5,
                "tasks_completed": 54,
                "tasks_total": 80,
                "on_time_pct": 88.9,
                "delayed_tasks": 6,
                "burn_rate": 2.3,
                "estimated_completion_date": date.today(),
                "variance_from_plan": -3,
            }

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/overview",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["health_score"] == 78.5
            assert "critical_path_summary" in data
            assert "resource_summary" in data
            assert "simulation_summary" in data
            assert "progress_summary" in data
            assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_get_analytics_overview_unauthorized(self):
        """Test analytics overview without authentication."""
        project_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/projects/{project_id}/analytics/overview"
            )

        assert response.status_code == 403  # No Bearer token

    @pytest.mark.asyncio
    async def test_get_analytics_overview_not_found(self):
        """Test analytics overview for non-existent project."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project_id = uuid4()

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project_id}/analytics/overview",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_critical_path_analytics_success(self):
        """Test successful critical path analytics retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.get_critical_path_metrics') as mock_metrics:

            mock_check.return_value = True
            mock_get.return_value = project
            task_id_1 = uuid4()
            task_id_2 = uuid4()
            mock_metrics.return_value = {
                "critical_tasks": [task_id_1, task_id_2],
                "total_duration": 45,
                "float_time": {str(uuid4()): 3.5},
                "risk_tasks": [task_id_1],
                "path_stability_score": 78.5,
            }

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/critical-path",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["critical_tasks"]) == 2
            assert data["total_duration"] == 45
            assert data["path_stability_score"] == 78.5

    @pytest.mark.asyncio
    async def test_get_resource_analytics_success(self):
        """Test successful resource analytics retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.get_resource_utilization') as mock_resources:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_resources.return_value = {
                "total_resources": 15,
                "allocated_resources": 12,
                "utilization_pct": 82.5,
                "over_allocated": [
                    {
                        "resource_id": "res_001",
                        "name": "John Doe",
                        "allocation_pct": 120.0,
                        "tasks_count": 5,
                    }
                ],
                "under_utilized": [],
                "resource_timeline": {"2025-02-03": 78.5},
            }

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/resources",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total_resources"] == 15
            assert data["allocated_resources"] == 12
            assert data["utilization_pct"] == 82.5
            assert len(data["over_allocated"]) == 1
            assert data["over_allocated"][0]["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_simulation_analytics_success(self):
        """Test successful simulation analytics retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.get_simulation_summary') as mock_simulation:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_simulation.return_value = {
                "percentiles": {
                    "p10": 38.2,
                    "p50": 45.0,
                    "p75": 52.5,
                    "p90": 58.3,
                    "p95": 62.7,
                },
                "mean_duration": 45.8,
                "std_deviation": 8.2,
                "risk_level": "medium",
                "confidence_80pct_range": [40.5, 55.0],
                "histogram_data": [
                    {"bucket": "40-45", "count": 380},
                    {"bucket": "45-50", "count": 420},
                ],
            }

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/simulation",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["risk_level"] == "medium"
            assert data["mean_duration"] == 45.8
            assert data["percentiles"]["p50"] == 45.0
            assert len(data["histogram_data"]) == 2

    @pytest.mark.asyncio
    async def test_get_progress_analytics_success(self):
        """Test successful progress analytics retrieval."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.get_progress_metrics') as mock_progress:

            mock_check.return_value = True
            mock_get.return_value = project
            estimated_date = date.today() + timedelta(days=30)
            mock_progress.return_value = {
                "completion_pct": 67.5,
                "tasks_completed": 54,
                "tasks_total": 80,
                "on_time_pct": 88.9,
                "delayed_tasks": 6,
                "burn_rate": 2.3,
                "estimated_completion_date": estimated_date,
                "variance_from_plan": -3,
            }

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/progress",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["completion_pct"] == 67.5
            assert data["tasks_completed"] == 54
            assert data["tasks_total"] == 80
            assert data["burn_rate"] == 2.3
            assert data["variance_from_plan"] == -3

    @pytest.mark.asyncio
    async def test_get_critical_path_analytics_unauthorized(self):
        """Test critical path analytics by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/critical-path",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_resource_analytics_unauthorized(self):
        """Test resource analytics by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/resources",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_simulation_analytics_unauthorized(self):
        """Test simulation analytics by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/simulation",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_progress_analytics_unauthorized(self):
        """Test progress analytics by non-owner."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        other_user_id = uuid4()
        project = self.create_test_project(other_user_id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check:
            mock_check.return_value = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/progress",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_analytics_service_error_handling(self):
        """Test error handling when analytics service fails."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)
        project = self.create_test_project(user.id)

        with patch('app.services.project_service.ProjectService.check_owner_permission') as mock_check, \
             patch('app.services.project_service.ProjectService.get_project') as mock_get, \
             patch('app.services.analytics_service.AnalyticsService.calculate_project_health_score') as mock_health:

            mock_check.return_value = True
            mock_get.return_value = project
            mock_health.side_effect = Exception("Service error")

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/projects/{project.id}/analytics/overview",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 500
            assert "Failed to retrieve analytics overview" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.api.endpoints.analytics"])
