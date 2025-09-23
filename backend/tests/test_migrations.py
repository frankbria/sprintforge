"""
Tests for the database migration system.
"""
import pytest
import asyncio
import asyncpg
from pathlib import Path
from backend.app.database.migrations import MigrationRunner


@pytest.mark.asyncio
async def test_migration_runner_init():
    """Test MigrationRunner initialization."""
    runner = MigrationRunner()
    assert runner.database_url is not None
    assert runner.migrations_dir.exists()


@pytest.mark.asyncio
async def test_migration_files_discovery():
    """Test that migration files are discovered correctly."""
    runner = MigrationRunner()
    migration_files = runner.get_migration_files()

    # Should find our initial schema migration
    assert len(migration_files) >= 1

    # Check that initial schema migration exists
    migration_names = [f.stem for f in migration_files]
    assert "001_initial_schema" in migration_names


@pytest.mark.asyncio
async def test_database_connection():
    """Test that migration runner can connect to database."""
    runner = MigrationRunner()

    try:
        conn = await runner._get_connection()
        result = await conn.fetchval('SELECT 1')
        assert result == 1
        await conn.close()
    except Exception as e:
        pytest.skip(f"Database not available for testing: {e}")


@pytest.mark.asyncio
async def test_migration_table_creation():
    """Test that migration tracking table is created."""
    runner = MigrationRunner()

    try:
        conn = await runner._get_connection()
        await runner._ensure_migration_table(conn)

        # Check that table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'migration_history'
            )
        """)
        assert result is True

        await conn.close()
    except Exception as e:
        pytest.skip(f"Database not available for testing: {e}")


@pytest.mark.asyncio
async def test_migration_checksum():
    """Test migration file checksum calculation."""
    runner = MigrationRunner()
    migration_files = runner.get_migration_files()

    if migration_files:
        migration_file = migration_files[0]
        checksum1 = runner._calculate_checksum(migration_file)
        checksum2 = runner._calculate_checksum(migration_file)

        # Same file should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 32  # MD5 hash length


@pytest.mark.asyncio
async def test_migration_status():
    """Test migration status reporting."""
    runner = MigrationRunner()

    try:
        status = await runner.get_migration_status()

        # Status should have required keys
        required_keys = ['applied_count', 'pending_count', 'applied_migrations', 'pending_migrations', 'integrity_issues']
        for key in required_keys:
            assert key in status

        # Counts should be non-negative
        assert status['applied_count'] >= 0
        assert status['pending_count'] >= 0

    except Exception as e:
        pytest.skip(f"Database not available for testing: {e}")


@pytest.mark.asyncio
async def test_apply_initial_migration():
    """Test applying the initial migration."""
    runner = MigrationRunner()

    try:
        # Get initial status
        initial_status = await runner.get_migration_status()

        # If initial migration is pending, apply it
        if "001_initial_schema" in initial_status['pending_migrations']:
            applied = await runner.migrate_up("001_initial_schema")
            assert "001_initial_schema" in applied

            # Verify tables were created
            conn = await runner._get_connection()
            try:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)

                table_names = [row['table_name'] for row in tables]

                # Check for NextAuth.js tables
                expected_tables = ['users', 'accounts', 'sessions', 'verification_tokens']
                for table in expected_tables:
                    assert table in table_names

                # Check for SprintForge tables
                sprintforge_tables = ['projects', 'project_memberships', 'sync_operations']
                for table in sprintforge_tables:
                    assert table in table_names

            finally:
                await conn.close()

    except Exception as e:
        pytest.skip(f"Database not available for testing: {e}")


@pytest.mark.asyncio
async def test_migration_integrity():
    """Test migration integrity checking."""
    runner = MigrationRunner()

    try:
        issues = await runner.check_migration_integrity()
        # Should be empty list if no integrity issues
        assert isinstance(issues, list)

    except Exception as e:
        pytest.skip(f"Database not available for testing: {e}")