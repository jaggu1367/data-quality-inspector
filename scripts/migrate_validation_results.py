"""
Migrate validation_results table: batch_identifier -> source_id, data_source_name -> rules_table_name.

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


def _has_column(cursor, table: str, column: str) -> bool:
    """Check if a table has a specific column."""
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def migrate():
    """Migrate validation_results from old schema to new schema."""
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
            cursor.execute("""
                CREATE TABLE validation_results_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER NOT NULL,
                    validation_timestamp DATETIME NOT NULL,
                    success BOOLEAN NOT NULL,
                    result TEXT,
                    exception_info TEXT,
                    rules_table_name VARCHAR(255) NOT NULL,
                    source_id VARCHAR(255),
                    data_source VARCHAR(255),
                    source_table VARCHAR(255),
                    FOREIGN KEY(rule_id) REFERENCES data_quality_rules (id)
                )
            """)
            cursor.execute("""
                INSERT INTO validation_results_new (
                    id, rule_id, validation_timestamp, success, result, exception_info,
                    rules_table_name, source_id, data_source, source_table
                )
                SELECT id, rule_id, validation_timestamp, success, result, exception_info,
                    data_source_name, batch_identifier, NULL, NULL
                FROM validation_results
            """)
            cursor.execute("DROP TABLE validation_results")
            cursor.execute("ALTER TABLE validation_results_new RENAME TO validation_results")
            for idx in ["rule_id", "validation_timestamp", "success", "rules_table_name", "source_id"]:
                cursor.execute(f"CREATE INDEX ix_validation_results_{idx} ON validation_results ({idx})")
            conn.commit()
            migrated = True

        elif _has_column(cursor, "validation_results", "data_source_name") and not _has_column(cursor, "validation_results", "rules_table_name"):
            print("Migrating: data_source_name -> rules_table_name")
            cursor.execute("ALTER TABLE validation_results RENAME COLUMN data_source_name TO rules_table_name")
            cursor.execute("DROP INDEX IF EXISTS ix_validation_results_data_source_name")
            cursor.execute("CREATE INDEX ix_validation_results_rules_table_name ON validation_results (rules_table_name)")
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
