"""Custom database types for cross-database compatibility."""

from uuid import UUID as PyUUID
from sqlalchemy import String, JSON, TypeDecorator
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
