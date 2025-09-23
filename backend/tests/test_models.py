"""
Tests for SQLAlchemy models.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from backend.app.models import User, Project, ProjectMembership, SyncOperation


@pytest.mark.asyncio
async def test_user_model_creation(test_db_session):
    """Test User model creation and basic functionality."""
    user = User(
        email="test@example.com",
        name="Test User",
        subscription_tier="pro",
        subscription_status="active",
        preferences={"theme": "dark", "notifications": True},
        is_active=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    # Test basic attributes
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.subscription_tier == "pro"
    assert user.subscription_status == "active"
    assert user.preferences == {"theme": "dark", "notifications": True}
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None

    # Test string representation
    assert str(user) == f"<User(id={user.id}, email='test@example.com')>"


@pytest.mark.asyncio
async def test_project_model_creation(test_db_session, test_user):
    """Test Project model creation and relationships."""
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=test_user.id,
        configuration={
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 2,
            "working_days": [1, 2, 3, 4, 5],
            "features": {"monte_carlo": True, "critical_path": True}
        },
        template_version="1.0",
        is_public=False,
    )

    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)

    # Test basic attributes
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.owner_id == test_user.id
    assert project.configuration["sprint_pattern"] == "YY.Q.#"
    assert project.template_version == "1.0"
    assert project.is_public is False
    assert project.created_at is not None
    assert project.updated_at is not None

    # Test string representation
    assert str(project) == f"<Project(id={project.id}, name='Test Project', owner_id={test_user.id})>"


@pytest.mark.asyncio
async def test_project_membership_model(test_db_session, test_user, test_project, test_user_pro):
    """Test ProjectMembership model creation and relationships."""
    membership = ProjectMembership(
        project_id=test_project.id,
        user_id=test_user_pro.id,
        role="editor",
        status="active",
        invited_by=test_user.id,
        invited_at=datetime.utcnow(),
        joined_at=datetime.utcnow(),
        permissions={"can_edit": True, "can_delete": False}
    )

    test_db_session.add(membership)
    await test_db_session.commit()
    await test_db_session.refresh(membership)

    # Test basic attributes
    assert membership.id is not None
    assert membership.project_id == test_project.id
    assert membership.user_id == test_user_pro.id
    assert membership.role == "editor"
    assert membership.status == "active"
    assert membership.invited_by == test_user.id
    assert membership.permissions["can_edit"] is True

    # Test string representation
    assert str(membership) == f"<ProjectMembership(id={membership.id}, project_id={test_project.id}, user_id={test_user_pro.id}, role='editor')>"


@pytest.mark.asyncio
async def test_sync_operation_model(test_db_session, test_user, test_project):
    """Test SyncOperation model creation."""
    sync_op = SyncOperation(
        project_id=test_project.id,
        user_id=test_user.id,
        operation_type="download",
        status="completed",
        file_name="project_template.xlsx",
        file_size=1024000,
        file_checksum="abc123def456",
        sync_data={"rows_processed": 100, "formulas_generated": 25},
        completed_at=datetime.utcnow()
    )

    test_db_session.add(sync_op)
    await test_db_session.commit()
    await test_db_session.refresh(sync_op)

    # Test basic attributes
    assert sync_op.id is not None
    assert sync_op.project_id == test_project.id
    assert sync_op.user_id == test_user.id
    assert sync_op.operation_type == "download"
    assert sync_op.status == "completed"
    assert sync_op.file_name == "project_template.xlsx"
    assert sync_op.file_size == 1024000
    assert sync_op.sync_data["rows_processed"] == 100

    # Test string representation
    assert str(sync_op) == f"<SyncOperation(id={sync_op.id}, type='download', status='completed')>"


@pytest.mark.asyncio
async def test_user_relationships(test_db_session, test_user, test_project):
    """Test User model relationships."""
    # Refresh to load relationships
    await test_db_session.refresh(test_user)

    # Test project relationship
    user_projects = test_user.projects
    assert len(user_projects) == 1
    assert user_projects[0].id == test_project.id


@pytest.mark.asyncio
async def test_project_configuration_jsonb(test_db_session, test_user):
    """Test JSONB configuration field functionality."""
    complex_config = {
        "sprint_pattern": "PI-N.Sprint-M",
        "sprint_duration_weeks": 3,
        "working_days": [1, 2, 3, 4, 5],
        "holidays": ["2024-12-25", "2024-01-01"],
        "features": {
            "monte_carlo": True,
            "critical_path": True,
            "resource_leveling": False,
            "progress_tracking": True
        },
        "custom_fields": [
            {"name": "priority", "type": "select", "options": ["high", "medium", "low"]},
            {"name": "estimation", "type": "number", "unit": "hours"}
        ],
        "notification_settings": {
            "email_notifications": True,
            "slack_webhook": "https://hooks.slack.com/test"
        }
    }

    project = Project(
        name="Complex Project",
        description="Project with complex configuration",
        owner_id=test_user.id,
        configuration=complex_config,
        template_version="2.0",
    )

    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)

    # Test JSONB functionality
    assert project.configuration["sprint_pattern"] == "PI-N.Sprint-M"
    assert project.configuration["features"]["monte_carlo"] is True
    assert len(project.configuration["custom_fields"]) == 2
    assert project.configuration["notification_settings"]["email_notifications"] is True


@pytest.mark.asyncio
async def test_model_timestamps(test_db_session, test_user):
    """Test that timestamps are automatically managed."""
    original_created = test_user.created_at
    original_updated = test_user.updated_at

    # Update the user
    test_user.name = "Updated Name"
    await test_db_session.commit()
    await test_db_session.refresh(test_user)

    # Created timestamp should remain the same
    assert test_user.created_at == original_created

    # Updated timestamp should be different
    assert test_user.updated_at > original_updated


@pytest.mark.asyncio
async def test_unique_constraints(test_db_session, test_user):
    """Test unique constraints are enforced."""
    # Try to create user with same email
    duplicate_user = User(
        email=test_user.email,  # Same email
        name="Different User",
        subscription_tier="free",
    )

    test_db_session.add(duplicate_user)

    # Should raise integrity error
    with pytest.raises(Exception):  # Database integrity error
        await test_db_session.commit()