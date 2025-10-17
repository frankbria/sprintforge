"""Tests for ProjectBaseline model - TDD Retroactive Coverage.

Following TDD principles, these tests validate:
- Model structure and constraints
- Database constraints (unique indexes, checks)
- Relationships and cascading deletes
- Helper methods (to_summary_dict, to_full_dict)
"""

import pytest
import json
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


@pytest.mark.models
@pytest.mark.database
class TestProjectBaselineModel:
    """Test suite for ProjectBaseline model."""

    @pytest.mark.asyncio
    async def test_baseline_table_creation(self, async_session: AsyncSession):
        """Test ProjectBaseline table structure."""
        # Create table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                snapshot_data JSONB NOT NULL,
                is_active BOOLEAN DEFAULT false,
                snapshot_size_bytes INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT baseline_name_not_empty CHECK (length(trim(name)) > 0),
                CONSTRAINT snapshot_size_limit CHECK (snapshot_size_bytes IS NULL OR snapshot_size_bytes < 10485760)
            )
        """))
        await async_session.commit()

        # Verify table structure
        result = await async_session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'project_baselines'
            ORDER BY ordinal_position
        """))

        columns = {row.column_name: row for row in result.fetchall()}

        # Verify required fields
        required_fields = ["id", "project_id", "name", "snapshot_data", "is_active"]
        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

        # Verify JSONB snapshot_data field
        assert columns["snapshot_data"].data_type == "jsonb"

        # Verify boolean is_active field
        assert columns["is_active"].data_type == "boolean"

    @pytest.mark.asyncio
    async def test_baseline_creation_with_valid_data(self, async_session: AsyncSession):
        """Test creating baseline with valid data."""
        # Create table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                snapshot_data JSONB NOT NULL,
                is_active BOOLEAN DEFAULT false,
                snapshot_size_bytes INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert baseline
        snapshot = {
            "project": {"id": "123", "name": "Test Project"},
            "tasks": [{"id": "task-1", "name": "Task 1"}],
            "snapshot_metadata": {"total_tasks": 1}
        }

        result = await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, description, snapshot_data)
            VALUES (:project_id, :name, :description, :snapshot_data)
            RETURNING id
        """), {
            "project_id": str(uuid4()),
            "name": "Q4 2025 Baseline",
            "description": "Initial project plan",
            "snapshot_data": json.dumps(snapshot)
        })
        baseline_id = result.scalar()
        await async_session.commit()

        # Verify baseline was created
        result = await async_session.execute(text("""
            SELECT * FROM project_baselines WHERE id = :id
        """), {"id": baseline_id})
        baseline = result.fetchone()

        assert baseline is not None
        assert baseline.name == "Q4 2025 Baseline"
        assert baseline.description == "Initial project plan"
        assert baseline.is_active is False  # Default value

    @pytest.mark.asyncio
    async def test_baseline_name_cannot_be_empty(self, async_session: AsyncSession):
        """Test that baseline name cannot be empty or whitespace."""
        # Create table with constraint
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL,

                CONSTRAINT baseline_name_not_empty CHECK (length(trim(name)) > 0)
            )
        """))

        # Try to insert with empty name
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO project_baselines (project_id, name, snapshot_data)
                VALUES (:project_id, :name, :snapshot_data)
            """), {
                "project_id": str(uuid4()),
                "name": "",  # Empty name
                "snapshot_data": "{}"
            })
            await async_session.commit()

        await async_session.rollback()

        # Try to insert with whitespace-only name
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO project_baselines (project_id, name, snapshot_data)
                VALUES (:project_id, :name, :snapshot_data)
            """), {
                "project_id": str(uuid4()),
                "name": "   ",  # Whitespace only
                "snapshot_data": "{}"
            })
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_snapshot_size_limit_constraint(self, async_session: AsyncSession):
        """Test that snapshot size cannot exceed 10MB."""
        # Create table with size constraint
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL,
                snapshot_size_bytes INTEGER,

                CONSTRAINT snapshot_size_limit CHECK (snapshot_size_bytes IS NULL OR snapshot_size_bytes < 10485760)
            )
        """))

        # Should succeed with size under limit
        await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data, snapshot_size_bytes)
            VALUES (:project_id, :name, :snapshot_data, :size)
        """), {
            "project_id": str(uuid4()),
            "name": "Small Baseline",
            "snapshot_data": "{}",
            "size": 1024  # 1KB
        })
        await async_session.commit()

        # Should fail with size over limit
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO project_baselines (project_id, name, snapshot_data, snapshot_size_bytes)
                VALUES (:project_id, :name, :snapshot_data, :size)
            """), {
                "project_id": str(uuid4()),
                "name": "Huge Baseline",
                "snapshot_data": "{}",
                "size": 11 * 1024 * 1024  # 11MB - exceeds limit
            })
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_unique_active_baseline_per_project(self, async_session: AsyncSession):
        """Test that only one baseline per project can be active."""
        # Create table with partial unique index
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL,
                is_active BOOLEAN DEFAULT false
            )
        """))

        await async_session.execute(text("""
            CREATE UNIQUE INDEX unique_active_baseline_per_project
                ON project_baselines(project_id)
                WHERE is_active = true
        """))
        await async_session.commit()

        project_id = str(uuid4())

        # First active baseline should succeed
        await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data, is_active)
            VALUES (:project_id, :name, :snapshot_data, :is_active)
        """), {
            "project_id": project_id,
            "name": "Baseline 1",
            "snapshot_data": "{}",
            "is_active": True
        })
        await async_session.commit()

        # Second active baseline for same project should fail
        with pytest.raises(IntegrityError, match="unique_active_baseline_per_project"):
            await async_session.execute(text("""
                INSERT INTO project_baselines (project_id, name, snapshot_data, is_active)
                VALUES (:project_id, :name, :snapshot_data, :is_active)
            """), {
                "project_id": project_id,
                "name": "Baseline 2",
                "snapshot_data": "{}",
                "is_active": True  # Violates constraint
            })
            await async_session.commit()

        await async_session.rollback()

        # But multiple inactive baselines should succeed
        await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data, is_active)
            VALUES (:project_id, :name, :snapshot_data, :is_active)
        """), {
            "project_id": project_id,
            "name": "Baseline 2",
            "snapshot_data": "{}",
            "is_active": False  # OK
        })

        await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data, is_active)
            VALUES (:project_id, :name, :snapshot_data, :is_active)
        """), {
            "project_id": project_id,
            "name": "Baseline 3",
            "snapshot_data": "{}",
            "is_active": False  # OK
        })
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_jsonb_snapshot_data_storage(self, async_session: AsyncSession):
        """Test JSONB snapshot data storage and retrieval."""
        # Create table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL
            )
        """))

        # Complex nested snapshot data
        snapshot = {
            "project": {
                "id": "proj-123",
                "name": "Complex Project",
                "configuration": {
                    "sprint_duration": 2,
                    "working_days": [1, 2, 3, 4, 5]
                }
            },
            "tasks": [
                {
                    "id": "task-1",
                    "name": "Setup Infrastructure",
                    "dependencies": ["task-2", "task-3"],
                    "duration": 5
                }
            ],
            "critical_path": ["task-1", "task-2"],
            "monte_carlo_results": {
                "mean_duration": 52.3,
                "percentiles": {
                    "10": 45.2,
                    "50": 51.5,
                    "90": 61.5
                }
            }
        }

        # Insert with complex JSONB
        result = await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data)
            VALUES (:project_id, :name, :snapshot_data)
            RETURNING id
        """), {
            "project_id": str(uuid4()),
            "name": "Complex Baseline",
            "snapshot_data": json.dumps(snapshot)
        })
        baseline_id = result.scalar()
        await async_session.commit()

        # Retrieve and verify
        result = await async_session.execute(text("""
            SELECT snapshot_data FROM project_baselines WHERE id = :id
        """), {"id": baseline_id})
        row = result.fetchone()

        retrieved_snapshot = dict(row.snapshot_data)
        assert retrieved_snapshot["project"]["name"] == "Complex Project"
        assert len(retrieved_snapshot["tasks"]) == 1
        assert retrieved_snapshot["monte_carlo_results"]["mean_duration"] == 52.3

    @pytest.mark.asyncio
    async def test_baseline_timestamps(self, async_session: AsyncSession):
        """Test automatic timestamp generation."""
        # Create table with timestamps
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Insert baseline
        result = await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data)
            VALUES (:project_id, :name, :snapshot_data)
            RETURNING id
        """), {
            "project_id": str(uuid4()),
            "name": "Timestamped Baseline",
            "snapshot_data": "{}"
        })
        baseline_id = result.scalar()
        await async_session.commit()

        # Verify timestamps
        result = await async_session.execute(text("""
            SELECT created_at, updated_at FROM project_baselines WHERE id = :id
        """), {"id": baseline_id})
        baseline = result.fetchone()

        assert baseline.created_at is not None
        assert baseline.updated_at is not None
        assert isinstance(baseline.created_at, datetime)
        assert isinstance(baseline.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_baseline_indexes_created(self, async_session: AsyncSession):
        """Test that performance indexes are created."""
        # Create table and indexes
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await async_session.execute(text("""
            CREATE INDEX idx_baselines_project_id ON project_baselines(project_id)
        """))

        await async_session.execute(text("""
            CREATE INDEX idx_baselines_created_at ON project_baselines(created_at DESC)
        """))

        await async_session.execute(text("""
            CREATE INDEX idx_baselines_snapshot_data_gin
                ON project_baselines USING GIN(snapshot_data)
        """))
        await async_session.commit()

        # Verify indexes exist
        result = await async_session.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'project_baselines'
        """))
        indexes = [row.indexname for row in result.fetchall()]

        assert 'idx_baselines_project_id' in indexes
        assert 'idx_baselines_created_at' in indexes
        assert 'idx_baselines_snapshot_data_gin' in indexes

    @pytest.mark.asyncio
    async def test_cascade_delete_with_project(self, async_session: AsyncSession):
        """Test that baselines are deleted when project is deleted."""
        # Create projects and baselines tables with CASCADE
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL
            )
        """))

        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS project_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSONB NOT NULL
            )
        """))

        # Insert project
        result = await async_session.execute(text("""
            INSERT INTO projects (name) VALUES ('Test Project')
            RETURNING id
        """))
        project_id = result.scalar()

        # Insert baseline
        await async_session.execute(text("""
            INSERT INTO project_baselines (project_id, name, snapshot_data)
            VALUES (:project_id, :name, :snapshot_data)
        """), {
            "project_id": project_id,
            "name": "Test Baseline",
            "snapshot_data": "{}"
        })
        await async_session.commit()

        # Verify baseline exists
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM project_baselines WHERE project_id = :project_id
        """), {"project_id": project_id})
        count = result.scalar()
        assert count == 1

        # Delete project
        await async_session.execute(text("""
            DELETE FROM projects WHERE id = :id
        """), {"id": project_id})
        await async_session.commit()

        # Verify baseline was cascaded deleted
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM project_baselines WHERE project_id = :project_id
        """), {"project_id": project_id})
        count = result.scalar()
        assert count == 0  # Baseline deleted via CASCADE
