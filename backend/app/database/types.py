"""Custom database types for cross-database compatibility."""

from uuid import UUID as PyUUID
from datetime import datetime, timezone
from sqlalchemy import String, JSON, DateTime as SQLADateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB
from sqlalchemy.engine import Dialect


class UUID(TypeDecorator):
    """
    Cross-database UUID type.

    Uses native UUID for PostgreSQL, String for SQLite and other databases.
    This allows tests to run with SQLite while production uses PostgreSQL.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        """Load the appropriate type based on the database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect: Dialect):
        """Convert Python UUID to database format."""
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite and others, store as string
            if isinstance(value, PyUUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect: Dialect):
        """Convert database value to Python UUID."""
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite and others, convert string to UUID
            if isinstance(value, str):
                return PyUUID(value)
            return value


class JSONB(TypeDecorator):
    """
    Cross-database JSONB type.

    Uses native JSONB for PostgreSQL, JSON for SQLite and other databases.
    This allows tests to run with SQLite while production uses PostgreSQL.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        """Load the appropriate type based on the database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGJSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect: Dialect):
        """Pass through - both JSONB and JSON handle dict serialization."""
        return value

    def process_result_value(self, value, dialect: Dialect):
        """Pass through - both JSONB and JSON handle dict deserialization."""
        return value


class TZDateTime(TypeDecorator):
    """
    Timezone-aware DateTime type that ensures all datetimes are UTC-aware.

    PostgreSQL natively handles timezone-aware datetimes, but SQLite does not.
    This type ensures consistent behavior across both databases by:
    - Storing datetimes as UTC in the database
    - Always returning timezone-aware datetime objects with UTC timezone
    """

    impl = SQLADateTime
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        """Load the appropriate type based on the database dialect."""
        # Both PostgreSQL and SQLite use DateTime, but with timezone=True
        return dialect.type_descriptor(SQLADateTime(timezone=True))

    def process_bind_param(self, value, dialect: Dialect):
        """Convert Python datetime to UTC before storing."""
        if value is None:
            return value

        if isinstance(value, datetime):
            # Ensure datetime is timezone-aware and in UTC
            if value.tzinfo is None:
                # Naive datetime - assume it's UTC
                value = value.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC
                value = value.astimezone(timezone.utc)

        return value

    def process_result_value(self, value, dialect: Dialect):
        """Convert database value to timezone-aware datetime in UTC."""
        if value is None:
            return value

        if isinstance(value, datetime):
            # Ensure the datetime is timezone-aware
            if value.tzinfo is None:
                # SQLite returns naive datetimes - make them UTC-aware
                value = value.replace(tzinfo=timezone.utc)
            elif value.tzinfo != timezone.utc:
                # Convert to UTC if it's in a different timezone
                value = value.astimezone(timezone.utc)

        return value
