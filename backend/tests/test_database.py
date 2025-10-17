"""
Database connectivity and migration tests using SQLite.
"""
import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_sqlite_connection():
    """Test basic SQLite connection using test environment."""
    settings = get_settings()

    # Verify we're using SQLite for tests
    assert 'sqlite' in settings.database_url.lower()

    engine = create_async_engine(
        settings.database_url,
        echo=False
    )

    try:
        async with engine.begin() as conn:
            # Simple query test
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_engine():
    """Test SQLAlchemy async engine connection with SQLite."""
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False
    )

    try:
        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1

            # Test that we can create a simple table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """))

            # Insert test data
            await conn.execute(text("""
                INSERT INTO test_table (id, name) VALUES (1, 'test')
            """))

            # Query test data
            result = await conn.execute(text("SELECT name FROM test_table WHERE id = 1"))
            row = result.fetchone()
            assert row[0] == 'test'

            # Clean up
            await conn.execute(text("DROP TABLE test_table"))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_session_creation():
    """Test that we can create async database sessions."""
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False
    )

    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
    finally:
        await engine.dispose()
