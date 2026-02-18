"""
Migrate validation_results table:
  1. batch_identifier -> source_id, data_source_name -> rules_table_name
  2. Reorder columns: audit (when) -> context (source) -> rule -> outcome

Run from project root: python scripts/migrate_validation_results.py

For existing databases with the old schema.
New databases get the correct schema from create_tables().
"""
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dq_framework.core import db_manager


# Canonical column order: id, validation_timestamp, source_id, data_source, source_table, rules_table_name, rule_id, success, result, exception_info
_VALIDATION_RESULTS_COLS = """(
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


def _has_column(cursor, table: str, column: str) -> bool:
    """Check if a table has a specific column."""
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def _get_column_order(cursor, table: str) -> list:
    """Get column names in table order."""
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def _recreate_indexes(cursor) -> None:
    """Create indexes on validation_results."""
    for idx in ["rule_id", "validation_timestamp", "success", "rules_table_name", "source_id"]:
        cursor.execute(f"CREATE INDEX ix_validation_results_{idx} ON validation_results ({idx})")


def migrate():
    """Migrate validation_results from old schema to new schema, reorder columns."""
    engine = db_manager.engine
    conn = engine.raw_connection()
    cursor = conn.cursor()
    migrated = False

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='validation_results'"
        )
        if not cursor.fetchone():
            return False

        if _has_column(cursor, "validation_results", "batch_identifier"):
            print("Migrating: batch_identifier -> source_id, data_source_name -> rules_table_name")
            cursor.execute("CREATE TABLE validation_results_new " + _VALIDATION_RESULTS_COLS)
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
            _recreate_indexes(cursor)
            conn.commit()
            migrated = True

        elif _has_column(cursor, "validation_results", "data_source_name") and not _has_column(cursor, "validation_results", "rules_table_name"):
            print("Migrating: data_source_name -> rules_table_name")
            cursor.execute("ALTER TABLE validation_results RENAME COLUMN data_source_name TO rules_table_name")
            cursor.execute("DROP INDEX IF EXISTS ix_validation_results_data_source_name")
            cursor.execute("CREATE INDEX ix_validation_results_rules_table_name ON validation_results (rules_table_name)")
            conn.commit()
            migrated = True

        # Reorder columns to meaningful order (audit -> context -> rule -> outcome)
        col_order = _get_column_order(cursor, "validation_results")
        desired_order = [
            "id", "validation_timestamp", "source_id", "data_source", "source_table",
            "rules_table_name", "rule_id", "success", "result", "exception_info",
        ]
        if col_order != desired_order and set(col_order) == set(desired_order):
            print("Migrating: reorder validation_results columns")
            cursor.execute("CREATE TABLE validation_results_new " + _VALIDATION_RESULTS_COLS)
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
            _recreate_indexes(cursor)
            conn.commit()
            migrated = True

        return migrated
    finally:
        conn.close()


def migrate_data_quality_rules():
    """Migrate data_quality_rules: data_source_name -> rules_table_name."""
    engine = db_manager.engine
    conn = engine.raw_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='data_quality_rules'"
        )
        if not cursor.fetchone():
            return False
        cursor.execute("PRAGMA table_info(data_quality_rules)")
        cols = [row[1] for row in cursor.fetchall()]
        if "data_source_name" in cols and "rules_table_name" not in cols:
            print("Migrating data_quality_rules: data_source_name -> rules_table_name")
            cursor.execute(
                "ALTER TABLE data_quality_rules RENAME COLUMN data_source_name TO rules_table_name"
            )
            cursor.execute("DROP INDEX IF EXISTS ix_data_quality_rules_data_source_name")
            cursor.execute("CREATE INDEX ix_data_quality_rules_rules_table_name ON data_quality_rules (rules_table_name)")
            conn.commit()
            return True
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("Checking schema migrations...")
    try:
        v_migrated = migrate()
        dq_migrated = migrate_data_quality_rules()
        if not v_migrated and not dq_migrated:
            print("  No migration needed (new schema or already migrated).")
        else:
            print("  Migration(s) complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
