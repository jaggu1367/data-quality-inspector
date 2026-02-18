"""
Database connection and manager for the Data Quality Framework.
"""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dq_framework.core.config import config
from dq_framework.core.models import Base


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or config.database.connection_string
        self.engine = create_engine(self.connection_string, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()


db_manager = DatabaseManager()
