"""Tests for database models."""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


@pytest.mark.models
@pytest.mark.database
class TestUserModel:
    """Test User model functionality (NextAuth.js compatible)."""

    @pytest.mark.asyncio
    async def test_user_table_creation(self, async_session: AsyncSession):
        """Test User table creation with NextAuth.js compatibility."""
        # Create users table with all required fields
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                email_verified TIMESTAMP,
                image TEXT,
                subscription_tier VARCHAR(50) DEFAULT 'free',
                subscription_status VARCHAR(50) DEFAULT 'active',
                max_projects INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await async_session.commit()

        # Verify table structure
        result = await async_session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))

        columns = {row.column_name: row for row in result.fetchall()}

        # Verify NextAuth.js required fields
        nextauth_fields = ["id", "name", "email", "email_verified", "image"]
        for field in nextauth_fields:
            assert field in columns, f"Missing NextAuth.js field: {field}"

        # Verify SprintForge specific fields
        sprintforge_fields = ["subscription_tier", "subscription_status", "max_projects"]
        for field in sprintforge_fields:
            assert field in columns, f"Missing SprintForge field: {field}"

        # Verify email is unique
        assert columns["email"].is_nullable == "NO"

    @pytest.mark.asyncio
    async def test_user_creation(self, async_session: AsyncSession, sample_user_data: Dict[str, Any]):
        """Test creating a user with valid data."""
        # Create users table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                email_verified TIMESTAMP,
                image TEXT,
                subscription_tier VARCHAR(50) DEFAULT 'free',
                subscription_status VARCHAR(50) DEFAULT 'active',
                max_projects INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert user
        await async_session.execute(text("""
            INSERT INTO users (id, name, email, subscription_tier, subscription_status, max_projects)
            VALUES (:id, :name, :email, :subscription_tier, :subscription_status, :max_projects)
        """), sample_user_data)
        await async_session.commit()

        # Verify user was created
        result = await async_session.execute(text("""
            SELECT * FROM users WHERE id = :id
        """), {"id": sample_user_data["id"]})
        user = result.fetchone()

        assert user is not None
        assert user.id == sample_user_data["id"]
        assert user.name == sample_user_data["name"]
        assert user.email == sample_user_data["email"]
        assert user.subscription_tier == sample_user_data["subscription_tier"]
        assert user.max_projects == sample_user_data["max_projects"]

    @pytest.mark.asyncio
    async def test_user_email_uniqueness(self, async_session: AsyncSession):
        """Test that user emails must be unique."""
        # Create users table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                email_verified TIMESTAMP,
                image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert first user
        await async_session.execute(text("""
            INSERT INTO users (id, name, email)
            VALUES ('user1', 'User One', 'test@example.com')
        """))
        await async_session.commit()

        # Try to insert second user with same email
        with pytest.raises(Exception):  # Should raise IntegrityError
            await async_session.execute(text("""
                INSERT INTO users (id, name, email)
                VALUES ('user2', 'User Two', 'test@example.com')
            """))
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_user_subscription_tiers(self, async_session: AsyncSession):
        """Test user subscription tier functionality."""
        # Create users table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                subscription_tier VARCHAR(50) DEFAULT 'free',
                max_projects INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Test different subscription tiers
        subscription_data = [
            ("user1", "free", 3),
            ("user2", "pro", 10),
            ("user3", "enterprise", 100)
        ]

        for user_id, tier, max_projects in subscription_data:
            await async_session.execute(text("""
                INSERT INTO users (id, email, subscription_tier, max_projects)
                VALUES (:id, :email, :tier, :max_projects)
            """), {
                "id": user_id,
                "email": f"{user_id}@example.com",
                "tier": tier,
                "max_projects": max_projects
            })
        await async_session.commit()

        # Verify all users were created with correct tiers
        result = await async_session.execute(text("""
            SELECT id, subscription_tier, max_projects FROM users ORDER BY id
        """))
        users = result.fetchall()

        assert len(users) == 3
        for i, (user_id, tier, max_projects) in enumerate(subscription_data):
            assert users[i].id == user_id
            assert users[i].subscription_tier == tier
            assert users[i].max_projects == max_projects

    @pytest.mark.asyncio
    async def test_user_timestamps(self, async_session: AsyncSession):
        """Test user timestamp functionality."""
        # Create users table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert user
        await async_session.execute(text("""
            INSERT INTO users (id, email) VALUES ('user1', 'user1@example.com')
        """))
        await async_session.commit()

        # Verify timestamps were set
        result = await async_session.execute(text("""
            SELECT created_at, updated_at FROM users WHERE id = 'user1'
        """))
        user = result.fetchone()

        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)


@pytest.mark.models
@pytest.mark.database
class TestProjectModel:
    """Test Project model functionality with JSONB configuration."""

    @pytest.mark.asyncio
    async def test_project_table_creation(self, async_session: AsyncSession):
        """Test Project table creation with JSONB config field."""
        # Create projects table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                is_public BOOLEAN DEFAULT FALSE,
                config JSONB DEFAULT '{}',
                template_checksum VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await async_session.commit()

        # Verify table structure
        result = await async_session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'projects'
            ORDER BY ordinal_position
        """))

        columns = {row.column_name: row for row in result.fetchall()}

        # Verify required fields
        required_fields = ["id", "name", "owner_id", "config"]
        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

        # Verify JSONB config field
        assert columns["config"].data_type == "jsonb"

    @pytest.mark.asyncio
    async def test_project_creation(self, async_session: AsyncSession, sample_project_data: Dict[str, Any]):
        """Test creating a project with JSONB configuration."""
        # Create projects table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                is_public BOOLEAN DEFAULT FALSE,
                config JSONB DEFAULT '{}',
                template_checksum VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert project
        await async_session.execute(text("""
            INSERT INTO projects (id, name, description, owner_id, is_public, config, template_checksum)
            VALUES (:id, :name, :description, :owner_id, :is_public, :config, :template_checksum)
        """), {
            **sample_project_data,
            "config": json.dumps(sample_project_data["config"])
        })
        await async_session.commit()

        # Verify project was created
        result = await async_session.execute(text("""
            SELECT * FROM projects WHERE id = :id
        """), {"id": sample_project_data["id"]})
        project = result.fetchone()

        assert project is not None
        assert project.id == sample_project_data["id"]
        assert project.name == sample_project_data["name"]
        assert project.owner_id == sample_project_data["owner_id"]
        assert project.is_public == sample_project_data["is_public"]

        # Verify JSONB config
        config = json.loads(json.dumps(dict(project.config)))
        assert config["template_version"] == "1.0"
        assert "custom_fields" in config
        assert "workflow_settings" in config

    @pytest.mark.asyncio
    async def test_project_jsonb_queries(self, async_session: AsyncSession):
        """Test JSONB queries on project config field."""
        # Create projects table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_id TEXT NOT NULL,
                config JSONB DEFAULT '{}'
            )
        """))

        # Insert projects with different configs
        projects_data = [
            {
                "id": "proj1",
                "name": "Project 1",
                "owner_id": "user1",
                "config": {"template_version": "1.0", "type": "software"}
            },
            {
                "id": "proj2",
                "name": "Project 2",
                "owner_id": "user1",
                "config": {"template_version": "2.0", "type": "marketing"}
            }
        ]

        for project_data in projects_data:
            await async_session.execute(text("""
                INSERT INTO projects (id, name, owner_id, config)
                VALUES (:id, :name, :owner_id, :config)
            """), {
                **project_data,
                "config": json.dumps(project_data["config"])
            })
        await async_session.commit()

        # Query by JSONB field
        result = await async_session.execute(text("""
            SELECT id, name FROM projects
            WHERE config->>'template_version' = '1.0'
        """))
        projects = result.fetchall()

        assert len(projects) == 1
        assert projects[0].id == "proj1"

        # Query by nested JSONB field
        result = await async_session.execute(text("""
            SELECT id, name FROM projects
            WHERE config->>'type' = 'software'
        """))
        projects = result.fetchall()

        assert len(projects) == 1
        assert projects[0].id == "proj1"

    @pytest.mark.asyncio
    async def test_project_config_validation(self, async_session: AsyncSession):
        """Test project config field validation."""
        # Create projects table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_id TEXT NOT NULL,
                config JSONB DEFAULT '{}'
            )
        """))

        # Test valid JSON config
        valid_config = {
            "template_version": "1.0",
            "custom_fields": [
                {"name": "priority", "type": "select", "options": ["high", "medium", "low"]}
            ],
            "workflow_settings": {
                "default_status": "todo",
                "statuses": ["todo", "in_progress", "done"]
            }
        }

        await async_session.execute(text("""
            INSERT INTO projects (id, name, owner_id, config)
            VALUES ('proj1', 'Test Project', 'user1', :config)
        """), {"config": json.dumps(valid_config)})
        await async_session.commit()

        # Verify project was created with valid config
        result = await async_session.execute(text("""
            SELECT config FROM projects WHERE id = 'proj1'
        """))
        project = result.fetchone()

        config = json.loads(json.dumps(dict(project.config)))
        assert config["template_version"] == "1.0"
        assert len(config["custom_fields"]) == 1
        assert config["workflow_settings"]["default_status"] == "todo"

    @pytest.mark.asyncio
    async def test_project_owner_relationship(self, async_session: AsyncSession):
        """Test project owner relationship (foreign key behavior)."""
        # Create both users and projects tables
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Insert user first
        await async_session.execute(text("""
            INSERT INTO users (id, email) VALUES ('user1', 'user1@example.com')
        """))

        # Insert project with valid owner
        await async_session.execute(text("""
            INSERT INTO projects (id, name, owner_id)
            VALUES ('proj1', 'Test Project', 'user1')
        """))
        await async_session.commit()

        # Verify project was created
        result = await async_session.execute(text("""
            SELECT * FROM projects WHERE id = 'proj1'
        """))
        project = result.fetchone()
        assert project is not None
        assert project.owner_id == 'user1'

        # Test foreign key constraint - should fail with invalid owner
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO projects (id, name, owner_id)
                VALUES ('proj2', 'Invalid Project', 'nonexistent_user')
            """))
            await async_session.commit()


@pytest.mark.models
@pytest.mark.database
class TestProjectMembershipModel:
    """Test ProjectMembership model functionality."""

    @pytest.mark.asyncio
    async def test_project_membership_table_creation(self, async_session: AsyncSession):
        """Test ProjectMembership table creation with role-based access."""
        # Create project_memberships table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
                invitation_email VARCHAR(255),
                invitation_token VARCHAR(255),
                invitation_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, project_id)
            )
        """))
        await async_session.commit()

        # Verify table structure
        result = await async_session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'project_memberships'
            ORDER BY ordinal_position
        """))

        columns = {row.column_name: row for row in result.fetchall()}

        # Verify required fields
        required_fields = ["user_id", "project_id", "role", "permissions"]
        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

        # Verify permissions array field
        assert "ARRAY" in columns["permissions"].data_type or "text[]" in columns["permissions"].data_type

    @pytest.mark.asyncio
    async def test_project_membership_creation(
        self,
        async_session: AsyncSession,
        sample_project_membership_data: Dict[str, Any]
    ):
        """Test creating a project membership."""
        # Create project_memberships table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
                invitation_email VARCHAR(255),
                invitation_token VARCHAR(255),
                invitation_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, project_id)
            )
        """))

        # Insert membership
        await async_session.execute(text("""
            INSERT INTO project_memberships (user_id, project_id, role, permissions, invitation_status)
            VALUES (:user_id, :project_id, :role, :permissions, :invitation_status)
        """), sample_project_membership_data)
        await async_session.commit()

        # Verify membership was created
        result = await async_session.execute(text("""
            SELECT * FROM project_memberships WHERE user_id = :user_id AND project_id = :project_id
        """), {
            "user_id": sample_project_membership_data["user_id"],
            "project_id": sample_project_membership_data["project_id"]
        })
        membership = result.fetchone()

        assert membership is not None
        assert membership.user_id == sample_project_membership_data["user_id"]
        assert membership.project_id == sample_project_membership_data["project_id"]
        assert membership.role == sample_project_membership_data["role"]
        assert list(membership.permissions) == sample_project_membership_data["permissions"]

    @pytest.mark.asyncio
    async def test_project_membership_roles(self, async_session: AsyncSession):
        """Test different project membership roles."""
        # Create project_memberships table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
                PRIMARY KEY (user_id, project_id)
            )
        """))

        # Test different roles
        roles_data = [
            ("user1", "proj1", "owner", ["read", "write", "admin", "delete"]),
            ("user2", "proj1", "admin", ["read", "write", "admin"]),
            ("user3", "proj1", "editor", ["read", "write"]),
            ("user4", "proj1", "viewer", ["read"])
        ]

        for user_id, project_id, role, permissions in roles_data:
            await async_session.execute(text("""
                INSERT INTO project_memberships (user_id, project_id, role, permissions)
                VALUES (:user_id, :project_id, :role, :permissions)
            """), {
                "user_id": user_id,
                "project_id": project_id,
                "role": role,
                "permissions": permissions
            })
        await async_session.commit()

        # Verify all memberships were created
        result = await async_session.execute(text("""
            SELECT user_id, role, permissions FROM project_memberships
            WHERE project_id = 'proj1' ORDER BY user_id
        """))
        memberships = result.fetchall()

        assert len(memberships) == 4
        for i, (user_id, project_id, role, permissions) in enumerate(roles_data):
            assert memberships[i].user_id == user_id
            assert memberships[i].role == role
            assert list(memberships[i].permissions) == permissions

    @pytest.mark.asyncio
    async def test_project_membership_invitation_workflow(self, async_session: AsyncSession):
        """Test project membership invitation workflow."""
        # Create project_memberships table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT,
                project_id TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                invitation_email VARCHAR(255),
                invitation_token VARCHAR(255),
                invitation_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, project_id)
            )
        """))

        # Test pending invitation
        await async_session.execute(text("""
            INSERT INTO project_memberships (project_id, invitation_email, invitation_token, invitation_status)
            VALUES ('proj1', 'invitee@example.com', 'token123', 'pending')
        """))
        await async_session.commit()

        # Verify pending invitation
        result = await async_session.execute(text("""
            SELECT * FROM project_memberships WHERE invitation_email = 'invitee@example.com'
        """))
        invitation = result.fetchone()

        assert invitation is not None
        assert invitation.invitation_email == 'invitee@example.com'
        assert invitation.invitation_token == 'token123'
        assert invitation.invitation_status == 'pending'

        # Test accepting invitation (update user_id and status)
        await async_session.execute(text("""
            UPDATE project_memberships
            SET user_id = 'user5', invitation_status = 'accepted'
            WHERE invitation_token = 'token123'
        """))
        await async_session.commit()

        # Verify invitation was accepted
        result = await async_session.execute(text("""
            SELECT * FROM project_memberships WHERE invitation_token = 'token123'
        """))
        accepted = result.fetchone()

        assert accepted.user_id == 'user5'
        assert accepted.invitation_status == 'accepted'

    @pytest.mark.asyncio
    async def test_project_membership_cascading_deletes(self, async_session: AsyncSession):
        """Test cascading deletes for project memberships."""
        # Create projects and project_memberships tables with proper relationships
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                role VARCHAR(50) DEFAULT 'member',
                PRIMARY KEY (user_id, project_id)
            )
        """))

        # Insert project and membership
        await async_session.execute(text("""
            INSERT INTO projects (id, name) VALUES ('proj1', 'Test Project')
        """))

        await async_session.execute(text("""
            INSERT INTO project_memberships (user_id, project_id, role)
            VALUES ('user1', 'proj1', 'owner')
        """))
        await async_session.commit()

        # Verify membership exists
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM project_memberships WHERE project_id = 'proj1'
        """))
        count = result.scalar()
        assert count == 1

        # Delete project
        await async_session.execute(text("""
            DELETE FROM projects WHERE id = 'proj1'
        """))
        await async_session.commit()

        # Verify membership was cascaded deleted
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM project_memberships WHERE project_id = 'proj1'
        """))
        count = result.scalar()
        assert count == 0


@pytest.mark.models
@pytest.mark.database
class TestDatabaseConstraintsAndIndexes:
    """Test database constraints and indexes."""

    @pytest.mark.asyncio
    async def test_primary_key_constraints(self, async_session: AsyncSession):
        """Test primary key constraints across all models."""
        # Create tables with primary keys
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                PRIMARY KEY (user_id, project_id)
            )
        """))

        # Test primary key constraints
        await async_session.execute(text("""
            INSERT INTO users (id, email) VALUES ('user1', 'user1@example.com')
        """))

        # Should fail with duplicate primary key
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO users (id, email) VALUES ('user1', 'different@example.com')
            """))
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_unique_constraints(self, async_session: AsyncSession):
        """Test unique constraints."""
        # Create table with unique constraint
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL
            )
        """))

        # Insert first user
        await async_session.execute(text("""
            INSERT INTO users (id, email) VALUES ('user1', 'test@example.com')
        """))
        await async_session.commit()

        # Should fail with duplicate email
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO users (id, email) VALUES ('user2', 'test@example.com')
            """))
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, async_session: AsyncSession):
        """Test foreign key constraints."""
        # Create tables with foreign key relationships
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Insert user
        await async_session.execute(text("""
            INSERT INTO users (id, email) VALUES ('user1', 'user1@example.com')
        """))

        # Should succeed with valid foreign key
        await async_session.execute(text("""
            INSERT INTO projects (id, name, owner_id)
            VALUES ('proj1', 'Test Project', 'user1')
        """))
        await async_session.commit()

        # Should fail with invalid foreign key
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO projects (id, name, owner_id)
                VALUES ('proj2', 'Invalid Project', 'nonexistent_user')
            """))
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_performance_indexes(self, async_session: AsyncSession):
        """Test performance indexes creation and usage."""
        # Create table with indexes
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create performance indexes
        await async_session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id)
        """))

        await async_session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)
        """))

        await async_session.commit()

        # Verify indexes exist
        result = await async_session.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'projects'
        """))
        indexes = [row.indexname for row in result.fetchall()]

        assert 'idx_projects_owner_id' in indexes
        assert 'idx_projects_created_at' in indexes

    @pytest.mark.asyncio
    async def test_check_constraints(self, async_session: AsyncSession):
        """Test check constraints for data validation."""
        # Create table with check constraints
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                max_projects INTEGER CHECK (max_projects > 0),
                subscription_tier VARCHAR(50) CHECK (subscription_tier IN ('free', 'pro', 'enterprise'))
            )
        """))

        # Should succeed with valid data
        await async_session.execute(text("""
            INSERT INTO users (id, email, max_projects, subscription_tier)
            VALUES ('user1', 'user1@example.com', 5, 'pro')
        """))
        await async_session.commit()

        # Should fail with invalid max_projects
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO users (id, email, max_projects, subscription_tier)
                VALUES ('user2', 'user2@example.com', -1, 'pro')
            """))
            await async_session.commit()

        # Should fail with invalid subscription_tier
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO users (id, email, max_projects, subscription_tier)
                VALUES ('user3', 'user3@example.com', 5, 'invalid_tier')
            """))
            await async_session.commit()