"""
Database migration system for SprintForge.
Handles forward and backward migrations with tracking.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import List, Optional, Tuple

import asyncpg
import structlog
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class MigrationRunner:
    """Handles database migrations with forward/backward capability."""

    def __init__(self, database_url: Optional[str] = None):
        settings = get_settings()
        self.database_url = database_url or settings.database_url

        # Convert SQLAlchemy URL to asyncpg format if needed
        if self.database_url.startswith("postgresql+asyncpg://"):
            self.database_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")

        self.migrations_dir = Path(__file__).parent.parent.parent / "migrations"

    async def _get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of migration file."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    async def _ensure_migration_table(self, conn: asyncpg.Connection) -> None:
        """Ensure migration_history table exists."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64) NOT NULL
            )
        """)

    async def get_applied_migrations(self) -> List[Tuple[str, str]]:
        """Get list of applied migrations with checksums."""
        conn = await self._get_connection()
        try:
            await self._ensure_migration_table(conn)

            rows = await conn.fetch("""
                SELECT migration_name, checksum
                FROM migration_history
                ORDER BY applied_at
            """)

            return [(row['migration_name'], row['checksum']) for row in rows]
        finally:
            await conn.close()

    def get_migration_files(self) -> List[Path]:
        """Get sorted list of migration files."""
        if not self.migrations_dir.exists():
            return []

        migration_files = [
            f for f in self.migrations_dir.glob("*.sql")
            if f.name.endswith(".sql")
        ]

        return sorted(migration_files)

    async def check_migration_integrity(self) -> List[str]:
        """Check if applied migrations match file checksums."""
        issues = []
        applied_migrations = dict(await self.get_applied_migrations())

        for migration_file in self.get_migration_files():
            migration_name = migration_file.stem

            if migration_name in applied_migrations:
                file_checksum = self._calculate_checksum(migration_file)
                db_checksum = applied_migrations[migration_name]

                if file_checksum != db_checksum:
                    issues.append(
                        f"Migration {migration_name} checksum mismatch: "
                        f"file={file_checksum}, db={db_checksum}"
                    )

        return issues

    async def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file."""
        migration_name = migration_file.stem
        logger.info("Applying migration", migration=migration_name)

        conn = await self._get_connection()
        try:
            # Read migration SQL
            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            # Calculate checksum
            checksum = self._calculate_checksum(migration_file)

            # Execute migration in transaction
            async with conn.transaction():
                # Execute the migration SQL
                await conn.execute(migration_sql)

                # Record migration (if not already recorded by the SQL)
                try:
                    await conn.execute("""
                        INSERT INTO migration_history (migration_name, checksum)
                        VALUES ($1, $2)
                        ON CONFLICT (migration_name) DO NOTHING
                    """, migration_name, checksum)
                except Exception:
                    # Migration might record itself
                    pass

            logger.info("Migration applied successfully", migration=migration_name)
            return True

        except Exception as e:
            logger.error("Migration failed", migration=migration_name, error=str(e))
            raise
        finally:
            await conn.close()

    async def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration (if rollback SQL exists)."""
        rollback_file = self.migrations_dir / f"{migration_name}_rollback.sql"

        if not rollback_file.exists():
            raise FileNotFoundError(f"Rollback file not found: {rollback_file}")

        logger.info("Rolling back migration", migration=migration_name)

        conn = await self._get_connection()
        try:
            # Read rollback SQL
            with open(rollback_file, 'r') as f:
                rollback_sql = f.read()

            # Execute rollback in transaction
            async with conn.transaction():
                await conn.execute(rollback_sql)

                # Remove from migration history
                await conn.execute("""
                    DELETE FROM migration_history
                    WHERE migration_name = $1
                """, migration_name)

            logger.info("Migration rolled back successfully", migration=migration_name)
            return True

        except Exception as e:
            logger.error("Rollback failed", migration=migration_name, error=str(e))
            raise
        finally:
            await conn.close()

    async def migrate_up(self, target_migration: Optional[str] = None) -> List[str]:
        """Apply pending migrations up to target (or all if None)."""
        applied_migrations = {name for name, _ in await self.get_applied_migrations()}
        migration_files = self.get_migration_files()

        applied_list = []

        for migration_file in migration_files:
            migration_name = migration_file.stem

            # Skip if already applied
            if migration_name in applied_migrations:
                continue

            # Apply migration
            await self.apply_migration(migration_file)
            applied_list.append(migration_name)

            # Stop if we reached target
            if target_migration and migration_name == target_migration:
                break

        return applied_list

    async def migrate_down(self, target_migration: str) -> List[str]:
        """Rollback migrations down to target (exclusive)."""
        applied_migrations = [name for name, _ in await self.get_applied_migrations()]

        # Find migrations to rollback (reverse order)
        rollback_list = []
        found_target = False

        for migration_name in reversed(applied_migrations):
            if migration_name == target_migration:
                found_target = True
                break

            rollback_list.append(migration_name)

        if not found_target and target_migration:
            raise ValueError(f"Target migration not found: {target_migration}")

        # Rollback migrations
        rolled_back = []
        for migration_name in rollback_list:
            await self.rollback_migration(migration_name)
            rolled_back.append(migration_name)

        return rolled_back

    async def get_migration_status(self) -> dict:
        """Get current migration status."""
        applied_migrations = await self.get_applied_migrations()
        migration_files = self.get_migration_files()
        integrity_issues = await self.check_migration_integrity()

        pending_migrations = []
        for migration_file in migration_files:
            migration_name = migration_file.stem
            if migration_name not in [name for name, _ in applied_migrations]:
                pending_migrations.append(migration_name)

        return {
            "applied_count": len(applied_migrations),
            "pending_count": len(pending_migrations),
            "applied_migrations": [name for name, _ in applied_migrations],
            "pending_migrations": pending_migrations,
            "integrity_issues": integrity_issues
        }


async def run_migrations():
    """CLI function to run migrations."""
    runner = MigrationRunner()

    try:
        status = await runner.get_migration_status()
        print(f"Applied migrations: {status['applied_count']}")
        print(f"Pending migrations: {status['pending_count']}")

        if status['integrity_issues']:
            print("⚠️  Migration integrity issues:")
            for issue in status['integrity_issues']:
                print(f"  - {issue}")
            return False

        if status['pending_migrations']:
            print(f"Applying {len(status['pending_migrations'])} pending migrations...")
            applied = await runner.migrate_up()
            print(f"✅ Applied migrations: {', '.join(applied)}")
        else:
            print("✅ All migrations are up to date")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(run_migrations())