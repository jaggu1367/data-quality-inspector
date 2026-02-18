"""
Default data quality rules and seeding logic.
"""

from dq_framework.core import DataQualityRule, db_manager

DEFAULT_RULES = [
    {
        "rule_name": "customer_id_not_null",
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "customer_id"},
        "rules_table_name": "customers",
        "description": "Ensure customer_id column has no null values",
    },
    {
        "rule_name": "status_valid_values",
        "expectation_type": "expect_column_values_to_be_in_set",
        "kwargs": {"column": "status", "value_set": ["active", "inactive", "pending"]},
        "rules_table_name": "customers",
        "description": "Ensure status column contains only valid values",
    },
    {
        "rule_name": "age_range_check",
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {"column": "age", "min_value": 0, "max_value": 120},
        "rules_table_name": "customers",
        "description": "Ensure age is between 0 and 120",
    },
    {
        "rule_name": "min_row_count",
        "expectation_type": "expect_table_row_count_to_be_between",
        "kwargs": {"min_value": 1, "max_value": 1000000},
        "rules_table_name": "customers",
        "description": "Ensure table has at least 1 row",
    },
    {
        "rule_name": "email_unique",
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "email"},
        "rules_table_name": "customers",
        "description": "Ensure email addresses are unique",
    },
]


def seed_data_quality_rules_if_empty() -> None:
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
