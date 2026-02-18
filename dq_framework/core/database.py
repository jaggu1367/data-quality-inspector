"""
Database connection and manager for the Data Quality Framework.
"""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dq_framework.core.config import config
from dq_framework.core.models import Base


def _validation_results_new_order_cols() -> str:
    """Canonical column order: id, validation_timestamp, source_id, data_source, source_table, rules_table_name, rule_id, success, result, exception_info."""
    return """(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        validation_timestamp DATETIME NOT NULL,
        source_id VARCHAR(255),
        data_source VARCHAR(255),
        source_table VARCHAR(255),
        rules_table_name VARCHAR(255) NOT NULL,
        rule_id INTEGER NOT NULL,
        success BOOLEAN NOT NULL,
        result TEXT,
        exception_info TEXT,
        FOREIGN KEY(rule_id) REFERENCES data_quality_rules (id)
    )"""


def _recreate_validation_results_indexes(cursor, conn) -> None:
    """Create indexes on validation_results."""
    cursor.execute("CREATE INDEX ix_validation_results_rule_id ON validation_results (rule_id)")
    cursor.execute("CREATE INDEX ix_validation_results_validation_timestamp ON validation_results (validation_timestamp)")
    cursor.execute("CREATE INDEX ix_validation_results_success ON validation_results (success)")
    cursor.execute("CREATE INDEX ix_validation_results_rules_table_name ON validation_results (rules_table_name)")
    cursor.execute("CREATE INDEX ix_validation_results_source_id ON validation_results (source_id)")


def _migrate_validation_results(engine) -> None:
    """Migrate validation_results: batch_identifier->source_id, data_source_name->rules_table_name, then reorder columns."""
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='validation_results'"
            )
            if not cursor.fetchone():
                return
            cursor.execute("PRAGMA table_info(validation_results)")
            rows = cursor.fetchall()
            cols = [row[1] for row in rows]
            col_order = [row[1] for row in rows]

            # Migration 1: batch_identifier -> source_id + data_source + source_table
            if "batch_identifier" in cols:
                cursor.execute(
                    "CREATE TABLE validation_results_new " + _validation_results_new_order_cols()
                )
                cursor.execute("""
                    INSERT INTO validation_results_new (
                        id, validation_timestamp, source_id, data_source, source_table,
                        rules_table_name, rule_id, success, result, exception_info
                    )
                    SELECT id, validation_timestamp, batch_identifier, NULL, NULL,
                        data_source_name, rule_id, success, result, exception_info
                    FROM validation_results
                """)
                cursor.execute("DROP TABLE validation_results")
                cursor.execute("ALTER TABLE validation_results_new RENAME TO validation_results")
                _recreate_validation_results_indexes(cursor, conn)
                conn.commit()
                cursor.execute("PRAGMA table_info(validation_results)")
                col_order = [row[1] for row in cursor.fetchall()]

            # Migration 2: data_source_name -> rules_table_name (for tables that have data_source_name)
            elif "data_source_name" in cols and "rules_table_name" not in cols:
                cursor.execute(
                    "ALTER TABLE validation_results RENAME COLUMN data_source_name TO rules_table_name"
                )
                cursor.execute("DROP INDEX IF EXISTS ix_validation_results_data_source_name")
                cursor.execute("CREATE INDEX ix_validation_results_rules_table_name ON validation_results (rules_table_name)")
                conn.commit()
                cursor.execute("PRAGMA table_info(validation_results)")
                col_order = [row[1] for row in cursor.fetchall()]

            # Migration 3: reorder columns to meaningful order (audit -> context -> rule -> outcome)
            # New order: id, validation_timestamp, source_id, data_source, source_table, rules_table_name, rule_id, success, result, exception_info
            desired_order = [
                "id", "validation_timestamp", "source_id", "data_source", "source_table",
                "rules_table_name", "rule_id", "success", "result", "exception_info",
            ]
            if col_order != desired_order and set(col_order) == set(desired_order):
                cursor.execute(
                    "CREATE TABLE validation_results_new " + _validation_results_new_order_cols()
                )
                cursor.execute("""
                    INSERT INTO validation_results_new (
                        id, validation_timestamp, source_id, data_source, source_table,
                        rules_table_name, rule_id, success, result, exception_info
                    )
                    SELECT id, validation_timestamp, source_id, data_source, source_table,
                        rules_table_name, rule_id, success, result, exception_info
                    FROM validation_results
                """)
                cursor.execute("DROP TABLE validation_results")
                cursor.execute("ALTER TABLE validation_results_new RENAME TO validation_results")
                _recreate_validation_results_indexes(cursor, conn)
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # Non-fatal; create_all may still work


def _migrate_data_quality_rules(engine) -> None:
    """Migrate data_quality_rules: data_source_name -> rules_table_name."""
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='data_quality_rules'"
            )
            if not cursor.fetchone():
                return
            cursor.execute("PRAGMA table_info(data_quality_rules)")
            cols = [row[1] for row in cursor.fetchall()]
            if "data_source_name" in cols and "rules_table_name" not in cols:
                cursor.execute(
                    "ALTER TABLE data_quality_rules RENAME COLUMN data_source_name TO rules_table_name"
                )
                cursor.execute("DROP INDEX IF EXISTS ix_data_quality_rules_data_source_name")
                cursor.execute("CREATE INDEX ix_data_quality_rules_rules_table_name ON data_quality_rules (rules_table_name)")
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


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
        _migrate_validation_results(self.engine)
        _migrate_data_quality_rules(self.engine)
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
