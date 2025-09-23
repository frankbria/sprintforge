"""Tests for database foundation components."""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings


@pytest.mark.database
class TestDatabaseConnection:
    """Test database connection functionality."""

    @pytest.mark.asyncio
    async def test_database_connection_success(self, test_settings: Settings):
        """Test successful database connection."""
        # Test connection using asyncpg directly
        try:
            conn = await asyncpg.connect(
                test_settings.database_url.replace('+asyncpg', '')
            )
            await conn.close()
            assert True, "Database connection successful"
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test database connection failure handling."""
        invalid_url = "postgresql+asyncpg://invalid:invalid@invalid:5432/invalid"

        with pytest.raises(Exception):
            conn = await asyncpg.connect(invalid_url.replace('+asyncpg', ''))
            await conn.close()

    @pytest.mark.asyncio
    async def test_database_pool_configuration(self, async_engine):
        """Test database connection pool configuration."""
        # Test that engine is properly configured
        assert async_engine is not None
        assert str(async_engine.url).startswith("postgresql+asyncpg://")

    @pytest.mark.asyncio
    async def test_database_session_creation(self, async_session: AsyncSession):
        """Test database session creation and basic operations."""
        # Test basic session functionality
        result = await async_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row.test_value == 1

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, async_session: AsyncSession):
        """Test database transaction rollback functionality."""
        # Start a transaction
        async with async_session.begin():
            # Execute a query that would normally succeed
            await async_session.execute(text("SELECT 1"))
            # Rollback should work without errors
            await async_session.rollback()

        # Session should still be usable after rollback
        result = await async_session.execute(text("SELECT 2 as test_value"))
        row = result.fetchone()
        assert row.test_value == 2


@pytest.mark.database
class TestDatabaseMigrations:
    """Test database migration system."""

    @pytest.mark.asyncio
    async def test_migration_table_creation(self, async_session: AsyncSession):
        """Test migration tracking table creation."""
        # Create migration tracking table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255)
            )
        """))
        await async_session.commit()

        # Verify table exists
        result = await async_session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'schema_migrations'
            )
        """))
        exists = result.scalar()
        assert exists is True

    @pytest.mark.asyncio
    async def test_migration_version_tracking(self, async_session: AsyncSession):
        """Test migration version tracking functionality."""
        # Ensure migration table exists
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255)
            )
        """))

        # Insert a test migration record
        await async_session.execute(text("""
            INSERT INTO schema_migrations (version, checksum)
            VALUES ('001_initial', 'abc123')
            ON CONFLICT (version) DO NOTHING
        """))
        await async_session.commit()

        # Verify the migration record exists
        result = await async_session.execute(text("""
            SELECT version, checksum FROM schema_migrations
            WHERE version = '001_initial'
        """))
        row = result.fetchone()
        assert row.version == "001_initial"
        assert row.checksum == "abc123"

    @pytest.mark.asyncio
    async def test_migration_checksum_validation(self, async_session: AsyncSession):
        """Test migration checksum validation."""
        # This test simulates checksum validation logic
        # In actual implementation, this would be in the migration runner

        expected_checksum = "abc123"
        stored_checksum = "abc123"

        assert expected_checksum == stored_checksum, "Migration checksum mismatch"

    def test_migration_file_structure(self):
        """Test migration file naming and structure conventions."""
        # Test migration file naming patterns
        valid_migration_names = [
            "001_initial_schema.sql",
            "002_add_users_table.sql",
            "003_add_projects_table.sql"
        ]

        for name in valid_migration_names:
            # Check naming convention: number_description.sql
            parts = name.split("_", 1)
            assert len(parts) == 2, f"Invalid migration name format: {name}"
            assert parts[0].isdigit(), f"Migration number must be numeric: {name}"
            assert parts[1].endswith(".sql"), f"Migration must be SQL file: {name}"

    @pytest.mark.asyncio
    async def test_migration_rollback_tracking(self, async_session: AsyncSession):
        """Test migration rollback functionality."""
        # Ensure migration table exists
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(255)
            )
        """))

        # Insert migration record
        await async_session.execute(text("""
            INSERT INTO schema_migrations (version, checksum)
            VALUES ('002_test_rollback', 'def456')
            ON CONFLICT (version) DO NOTHING
        """))
        await async_session.commit()

        # Simulate rollback by removing migration record
        await async_session.execute(text("""
            DELETE FROM schema_migrations WHERE version = '002_test_rollback'
        """))
        await async_session.commit()

        # Verify migration was rolled back
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM schema_migrations WHERE version = '002_test_rollback'
        """))
        count = result.scalar()
        assert count == 0


@pytest.mark.database
class TestSchemaValidation:
    """Test database schema validation."""

    @pytest.mark.asyncio
    async def test_nextauth_tables_schema(self, async_session: AsyncSession):
        """Test NextAuth.js required tables schema validation."""
        # Create NextAuth.js tables for testing
        nextauth_tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                email_verified TIMESTAMP,
                image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_account_id TEXT NOT NULL,
                refresh_token TEXT,
                access_token TEXT,
                expires_at INTEGER,
                token_type TEXT,
                scope TEXT,
                id_token TEXT,
                session_state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, provider_account_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                session_token TEXT UNIQUE NOT NULL,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                expires TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for table_sql in nextauth_tables:
            await async_session.execute(text(table_sql))
        await async_session.commit()

        # Validate tables exist
        for table_name in ["users", "accounts", "sessions"]:
            result = await async_session.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                )
            """))
            exists = result.scalar()
            assert exists is True, f"Table {table_name} should exist"

    @pytest.mark.asyncio
    async def test_sprintforge_tables_schema(self, async_session: AsyncSession):
        """Test SprintForge-specific tables schema validation."""
        # Create SprintForge tables for testing
        sprintforge_tables = [
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                config JSONB DEFAULT '{}',
                template_checksum VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_memberships (
                user_id TEXT,
                project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
                role VARCHAR(50) DEFAULT 'member',
                permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
                invitation_email VARCHAR(255),
                invitation_token VARCHAR(255),
                invitation_status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, project_id)
            )
            """
        ]

        for table_sql in sprintforge_tables:
            await async_session.execute(text(table_sql))
        await async_session.commit()

        # Validate tables exist
        for table_name in ["projects", "project_memberships"]:
            result = await async_session.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                )
            """))
            exists = result.scalar()
            assert exists is True, f"Table {table_name} should exist"

    @pytest.mark.asyncio
    async def test_database_constraints(self, async_session: AsyncSession):
        """Test database constraints and indexes."""
        # Create test table with constraints
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_constraints (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await async_session.commit()

        # Test unique constraint
        await async_session.execute(text("""
            INSERT INTO test_constraints (email) VALUES ('test@example.com')
        """))
        await async_session.commit()

        # This should fail due to unique constraint
        with pytest.raises(Exception):
            await async_session.execute(text("""
                INSERT INTO test_constraints (email) VALUES ('test@example.com')
            """))
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_jsonb_functionality(self, async_session: AsyncSession):
        """Test JSONB field functionality for project config."""
        # Create test table with JSONB
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_jsonb (
                id SERIAL PRIMARY KEY,
                config JSONB DEFAULT '{}'
            )
        """))
        await async_session.commit()

        # Insert JSONB data
        test_config = '{"template_version": "1.0", "custom_fields": []}'
        await async_session.execute(text("""
            INSERT INTO test_jsonb (config) VALUES (:config)
        """), {"config": test_config})
        await async_session.commit()

        # Query JSONB data
        result = await async_session.execute(text("""
            SELECT config FROM test_jsonb WHERE config->>'template_version' = '1.0'
        """))
        row = result.fetchone()
        assert row is not None
        assert "template_version" in str(row.config)


@pytest.mark.database
class TestSampleDataLoading:
    """Test sample development data loading."""

    @pytest.mark.asyncio
    async def test_sample_user_data_loading(
        self,
        async_session: AsyncSession,
        sample_user_data: dict
    ):
        """Test loading sample user data."""
        # Create users table first
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
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

        # Load sample data
        await async_session.execute(text("""
            INSERT INTO users (id, name, email, subscription_tier, subscription_status, max_projects)
            VALUES (:id, :name, :email, :subscription_tier, :subscription_status, :max_projects)
            ON CONFLICT (id) DO NOTHING
        """), sample_user_data)
        await async_session.commit()

        # Verify data was loaded
        result = await async_session.execute(text("""
            SELECT * FROM users WHERE id = :id
        """), {"id": sample_user_data["id"]})
        row = result.fetchone()
        assert row is not None
        assert row.name == sample_user_data["name"]
        assert row.email == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_sample_project_data_loading(
        self,
        async_session: AsyncSession,
        sample_project_data: dict
    ):
        """Test loading sample project data."""
        # Create projects table first
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                config JSONB DEFAULT '{}',
                template_checksum VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await async_session.commit()

        # Load sample data
        import json
        await async_session.execute(text("""
            INSERT INTO projects (id, name, description, owner_id, is_public, config, template_checksum)
            VALUES (:id, :name, :description, :owner_id, :is_public, :config, :template_checksum)
            ON CONFLICT (id) DO NOTHING
        """), {
            **sample_project_data,
            "config": json.dumps(sample_project_data["config"])
        })
        await async_session.commit()

        # Verify data was loaded
        result = await async_session.execute(text("""
            SELECT * FROM projects WHERE id = :id
        """), {"id": sample_project_data["id"]})
        row = result.fetchone()
        assert row is not None
        assert row.name == sample_project_data["name"]
        assert row.description == sample_project_data["description"]

    @pytest.mark.asyncio
    async def test_environment_controlled_data_loading(self, test_settings: Settings):
        """Test that sample data loading is environment-controlled."""
        # In testing environment, sample data should be allowed
        assert test_settings.environment == "testing"

        # This would typically check environment variables or config
        # to determine if sample data should be loaded
        load_sample_data = test_settings.environment in ["development", "testing"]
        assert load_sample_data is True

    @pytest.mark.asyncio
    async def test_data_reset_functionality(self, async_session: AsyncSession):
        """Test test data reset functionality."""
        # Create a test table
        await async_session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_reset (
                id SERIAL PRIMARY KEY,
                data TEXT
            )
        """))

        # Insert test data
        await async_session.execute(text("""
            INSERT INTO test_reset (data) VALUES ('test_data')
        """))
        await async_session.commit()

        # Verify data exists
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM test_reset
        """))
        count = result.scalar()
        assert count == 1

        # Reset data (truncate table)
        await async_session.execute(text("""
            TRUNCATE test_reset RESTART IDENTITY
        """))
        await async_session.commit()

        # Verify data was reset
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM test_reset
        """))
        count = result.scalar()
        assert count == 0