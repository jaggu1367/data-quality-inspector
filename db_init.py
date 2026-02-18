"""
Database initialization script.

Creates SQLite tables (data_quality_rules and validation_results) and seeds
data_quality_rules with default rules when the table is empty.

Usage (from project root):
    python db_init.py

Alternative:
    python -m dq_framework.cli init-db
    python scripts/init_database.py
"""
import sys
import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from dq_framework.core import config, db_manager
from dq_framework.seeding import seed_data_quality_rules_if_empty


def main():
    db_path = config.database.database_path
    print("Initializing database...")
    print(f"  Database file: {db_path}")
    try:
        db_manager.create_tables()
        seed_data_quality_rules_if_empty()
        print("  Database tables created successfully.")
        print("  Run validations: python scripts/run_expectations.py")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
