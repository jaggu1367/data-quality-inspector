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

from dq_framework.database import db_manager, DataQualityRule
from dq_framework.config import config

# Default rows for data_quality_rules (seed only when table is empty).
# For comprehensive rules (2+ per expectation type), run: python scripts/seed_comprehensive_rules.py
DEFAULT_RULES = [
    {
        "rule_name": "customer_id_not_null",
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "customer_id"},
        "dataset_name": "customers",
        "description": "Ensure customer_id column has no null values",
    },
    {
        "rule_name": "status_valid_values",
        "expectation_type": "expect_column_values_to_be_in_set",
        "kwargs": {"column": "status", "value_set": ["active", "inactive", "pending"]},
        "dataset_name": "customers",
        "description": "Ensure status column contains only valid values",
    },
    {
        "rule_name": "age_range_check",
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {"column": "age", "min_value": 0, "max_value": 120},
        "dataset_name": "customers",
        "description": "Ensure age is between 0 and 120",
    },
    {
        "rule_name": "min_row_count",
        "expectation_type": "expect_table_row_count_to_be_between",
        "kwargs": {"min_value": 1, "max_value": 1000000},
        "dataset_name": "customers",
        "description": "Ensure table has at least 1 row",
    },
    {
        "rule_name": "email_unique",
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "email"},
        "dataset_name": "customers",
        "description": "Ensure email addresses are unique",
    },
]


def seed_data_quality_rules_if_empty():
    """Insert default rules into data_quality_rules when the table is empty."""
    session = db_manager.get_session()
    try:
        if session.query(DataQualityRule).count() > 0:
            return
        for row in DEFAULT_RULES:
            session.add(DataQualityRule(**row))
        session.commit()
        print("  data_quality_rules table seeded with default rows.")
    finally:
        session.close()


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
