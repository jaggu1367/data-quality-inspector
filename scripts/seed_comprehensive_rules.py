"""
Seed data_quality_rules with at least 2 cases per expectation type from ExpectationBuilder.
All rules target the 'customers' dataset (sample_customers_100.csv: customer_id, email, status, age).
Rules are marked as active. Run with: python scripts/run_expectations.py --save-results
"""
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dq_framework.database import db_manager, DataQualityRule

DATASET = "customers"

# At least 2 rules per expectation type from ExpectationBuilder.supported_expectations
COMPREHENSIVE_RULES = [
    # --- Column existence ---
    {"rule_name": "col_exist_customer_id", "expectation_type": "expect_column_to_exist", "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "Column customer_id exists"},
    {"rule_name": "col_exist_email", "expectation_type": "expect_column_to_exist", "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "Column email exists"},

    # --- Type list ---
    {"rule_name": "type_list_customer_id_int", "expectation_type": "expect_column_values_to_be_in_type_list",
     "kwargs": {"column": "customer_id", "type_list": ["int64", "int32", "integer"]},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id is integer type"},
    {"rule_name": "type_list_age_int", "expectation_type": "expect_column_values_to_be_in_type_list",
     "kwargs": {"column": "age", "type_list": ["int64", "int32", "integer"]},
     "dataset_name": DATASET, "column_name": "age", "description": "age is integer type"},

    # --- Of type ---
    {"rule_name": "of_type_status_str", "expectation_type": "expect_column_values_to_be_of_type",
     "kwargs": {"column": "status", "type_": "str"},
     "dataset_name": DATASET, "column_name": "status", "description": "status is string"},
    {"rule_name": "of_type_email_str", "expectation_type": "expect_column_values_to_be_of_type",
     "kwargs": {"column": "email", "type_": "str"},
     "dataset_name": DATASET, "column_name": "email", "description": "email is string"},

    # --- Not null ---
    {"rule_name": "not_null_customer_id", "expectation_type": "expect_column_values_to_not_be_null",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id not null"},
    {"rule_name": "not_null_email", "expectation_type": "expect_column_values_to_not_be_null",
     "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "email not null"},

    # --- Be null (expects nulls - will fail on our data, but maps the type) ---
    {"rule_name": "be_null_optional_field_1", "expectation_type": "expect_column_values_to_be_null",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "Expect nulls in customer_id (demo)"},
    {"rule_name": "be_null_optional_field_2", "expectation_type": "expect_column_values_to_be_null",
     "kwargs": {"column": "status"},
     "dataset_name": DATASET, "column_name": "status", "description": "Expect nulls in status (demo)"},

    # --- Unique ---
    {"rule_name": "unique_customer_id", "expectation_type": "expect_column_values_to_be_unique",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id unique"},
    {"rule_name": "unique_email", "expectation_type": "expect_column_values_to_be_unique",
     "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "email unique"},

    # --- Unique across table ---
    {"rule_name": "unique_across_customer_id", "expectation_type": "expect_column_values_to_be_unique_across_table",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id unique across table"},
    {"rule_name": "unique_across_email", "expectation_type": "expect_column_values_to_be_unique_across_table",
     "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "email unique across table"},

    # --- In set ---
    {"rule_name": "in_set_status", "expectation_type": "expect_column_values_to_be_in_set",
     "kwargs": {"column": "status", "value_set": ["active", "inactive", "pending"]},
     "dataset_name": DATASET, "column_name": "status", "description": "status in valid set"},
    {"rule_name": "in_set_status_strict", "expectation_type": "expect_column_values_to_be_in_set",
     "kwargs": {"column": "status", "value_set": ["active", "inactive", "pending", "suspended"]},
     "dataset_name": DATASET, "column_name": "status", "description": "status in extended set"},

    # --- Not in set ---
    {"rule_name": "not_in_set_status_bad", "expectation_type": "expect_column_values_to_not_be_in_set",
     "kwargs": {"column": "status", "value_set": ["invalid", "unknown", "deleted"]},
     "dataset_name": DATASET, "column_name": "status", "description": "status not in invalid set"},
    {"rule_name": "not_in_set_age_bad", "expectation_type": "expect_column_values_to_not_be_in_set",
     "kwargs": {"column": "age", "value_set": [-1, 999, 1000]},
     "dataset_name": DATASET, "column_name": "age", "description": "age not in invalid set"},

    # --- Between ---
    {"rule_name": "between_age", "expectation_type": "expect_column_values_to_be_between",
     "kwargs": {"column": "age", "min_value": 0, "max_value": 120},
     "dataset_name": DATASET, "column_name": "age", "description": "age between 0 and 120"},
    {"rule_name": "between_customer_id", "expectation_type": "expect_column_values_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 1, "max_value": 10000},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id in valid range"},

    # --- In numeric range ---
    {"rule_name": "numeric_range_age", "expectation_type": "expect_column_values_to_be_in_numeric_range",
     "kwargs": {"column": "age", "min_value": 18, "max_value": 100},
     "dataset_name": DATASET, "column_name": "age", "description": "age in numeric range"},
    {"rule_name": "numeric_range_customer_id", "expectation_type": "expect_column_values_to_be_in_numeric_range",
     "kwargs": {"column": "customer_id", "min_value": 1, "max_value": 1000},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id in numeric range"},

    # --- Min between ---
    {"rule_name": "min_between_age", "expectation_type": "expect_column_min_to_be_between",
     "kwargs": {"column": "age", "min_value": 0, "max_value": 50},
     "dataset_name": DATASET, "column_name": "age", "description": "age min between 0 and 50"},
    {"rule_name": "min_between_customer_id", "expectation_type": "expect_column_min_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 1, "max_value": 10},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id min between 1 and 10"},

    # --- Max between ---
    {"rule_name": "max_between_age", "expectation_type": "expect_column_max_to_be_between",
     "kwargs": {"column": "age", "min_value": 50, "max_value": 120},
     "dataset_name": DATASET, "column_name": "age", "description": "age max between 50 and 120"},
    {"rule_name": "max_between_customer_id", "expectation_type": "expect_column_max_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 90, "max_value": 110},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id max between 90 and 110"},

    # --- Mean between ---
    {"rule_name": "mean_between_age", "expectation_type": "expect_column_mean_to_be_between",
     "kwargs": {"column": "age", "min_value": 30, "max_value": 60},
     "dataset_name": DATASET, "column_name": "age", "description": "age mean between 30 and 60"},
    {"rule_name": "mean_between_customer_id", "expectation_type": "expect_column_mean_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 40, "max_value": 70},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id mean between 40 and 70"},

    # --- Median between ---
    {"rule_name": "median_between_age", "expectation_type": "expect_column_median_to_be_between",
     "kwargs": {"column": "age", "min_value": 30, "max_value": 60},
     "dataset_name": DATASET, "column_name": "age", "description": "age median between 30 and 60"},
    {"rule_name": "median_between_customer_id", "expectation_type": "expect_column_median_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 45, "max_value": 60},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id median between 45 and 60"},

    # --- Stdev between ---
    {"rule_name": "stdev_between_age", "expectation_type": "expect_column_stdev_to_be_between",
     "kwargs": {"column": "age", "min_value": 10, "max_value": 30},
     "dataset_name": DATASET, "column_name": "age", "description": "age stdev between 10 and 30"},
    {"rule_name": "stdev_between_customer_id", "expectation_type": "expect_column_stdev_to_be_between",
     "kwargs": {"column": "customer_id", "min_value": 25, "max_value": 35},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id stdev between 25 and 35"},

    # --- Quantile between ---
    {"rule_name": "quantile_age", "expectation_type": "expect_column_quantile_values_to_be_between",
     "kwargs": {"column": "age", "quantile_ranges": {"quantiles": [0.25, 0.5, 0.75], "value_ranges": [[18, 35], [35, 60], [60, 100]]}},
     "dataset_name": DATASET, "column_name": "age", "description": "age quantiles in ranges"},
    {"rule_name": "quantile_customer_id", "expectation_type": "expect_column_quantile_values_to_be_between",
     "kwargs": {"column": "customer_id", "quantile_ranges": {"quantiles": [0.25, 0.5, 0.75], "value_ranges": [[1, 30], [30, 70], [70, 100]]}},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id quantiles in ranges"},

    # --- Match regex ---
    {"rule_name": "regex_email", "expectation_type": "expect_column_values_to_match_regex",
     "kwargs": {"column": "email", "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
     "dataset_name": DATASET, "column_name": "email", "description": "email matches regex"},
    {"rule_name": "regex_status", "expectation_type": "expect_column_values_to_match_regex",
     "kwargs": {"column": "status", "regex": r"^(active|inactive|pending)$"},
     "dataset_name": DATASET, "column_name": "status", "description": "status matches regex"},

    # --- Not match regex ---
    {"rule_name": "not_regex_status_no_digit", "expectation_type": "expect_column_values_to_not_match_regex",
     "kwargs": {"column": "status", "regex": r"\d"},
     "dataset_name": DATASET, "column_name": "status", "description": "status has no digits"},
    {"rule_name": "not_regex_email_no_special", "expectation_type": "expect_column_values_to_not_match_regex",
     "kwargs": {"column": "email", "regex": r"[<>]"},
     "dataset_name": DATASET, "column_name": "email", "description": "email has no <> chars"},

    # --- Match regex list ---
    {"rule_name": "regex_list_status", "expectation_type": "expect_column_values_to_match_regex_list",
     "kwargs": {"column": "status", "regex_list": [r"^active$", r"^inactive$", r"^pending$"]},
     "dataset_name": DATASET, "column_name": "status", "description": "status matches one of regex list"},
    {"rule_name": "regex_list_email", "expectation_type": "expect_column_values_to_match_regex_list",
     "kwargs": {"column": "email", "regex_list": [r"@example\.com$", r"@test\.org$"]},
     "dataset_name": DATASET, "column_name": "email", "description": "email matches pattern list"},

    # --- Not match regex list ---
    {"rule_name": "not_regex_list_status", "expectation_type": "expect_column_values_to_not_match_regex_list",
     "kwargs": {"column": "status", "regex_list": [r"deleted", r"archived", r"expired"]},
     "dataset_name": DATASET, "column_name": "status", "description": "status not in invalid regex list"},
    {"rule_name": "not_regex_list_email", "expectation_type": "expect_column_values_to_not_match_regex_list",
     "kwargs": {"column": "email", "regex_list": [r"spam@", r"invalid@"]},
     "dataset_name": DATASET, "column_name": "email", "description": "email not matching bad patterns"},

    # --- Match like pattern ---
    {"rule_name": "like_email", "expectation_type": "expect_column_values_to_match_like_pattern",
     "kwargs": {"column": "email", "like_pattern": "%@%.%"},
     "dataset_name": DATASET, "column_name": "email", "description": "email matches like pattern"},
    {"rule_name": "like_status", "expectation_type": "expect_column_values_to_match_like_pattern",
     "kwargs": {"column": "status", "like_pattern": "act%"},
     "dataset_name": DATASET, "column_name": "status", "description": "status starts with act (active)"},

    # --- Not match like pattern ---
    {"rule_name": "not_like_email_spam", "expectation_type": "expect_column_values_to_not_match_like_pattern",
     "kwargs": {"column": "email", "like_pattern": "%spam%"},
     "dataset_name": DATASET, "column_name": "email", "description": "email does not contain spam"},
    {"rule_name": "not_like_status_deleted", "expectation_type": "expect_column_values_to_not_match_like_pattern",
     "kwargs": {"column": "status", "like_pattern": "%deleted%"},
     "dataset_name": DATASET, "column_name": "status", "description": "status does not contain deleted"},

    # --- Strftime format (sample data has no date column; use age as integer - may fail, but maps type) ---
    {"rule_name": "strftime_demo_1", "expectation_type": "expect_column_values_to_match_strftime_format",
     "kwargs": {"column": "status", "strftime_format": "%Y-%m-%d"},
     "dataset_name": DATASET, "column_name": "status", "description": "Strftime demo (may fail on non-date column)"},
    {"rule_name": "strftime_demo_2", "expectation_type": "expect_column_values_to_match_strftime_format",
     "kwargs": {"column": "email", "strftime_format": "%H:%M:%S"},
     "dataset_name": DATASET, "column_name": "email", "description": "Strftime demo 2 (may fail)"},

    # --- Dateutil parseable ---
    {"rule_name": "dateutil_email_demo", "expectation_type": "expect_column_values_to_be_dateutil_parseable",
     "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "Dateutil demo (may fail on non-date)"},
    {"rule_name": "dateutil_status_demo", "expectation_type": "expect_column_values_to_be_dateutil_parseable",
     "kwargs": {"column": "status"},
     "dataset_name": DATASET, "column_name": "status", "description": "Dateutil demo 2 (may fail)"},

    # --- JSON parseable ---
    {"rule_name": "json_email_demo", "expectation_type": "expect_column_values_to_be_json_parseable",
     "kwargs": {"column": "email"},
     "dataset_name": DATASET, "column_name": "email", "description": "JSON parseable demo (may fail)"},
    {"rule_name": "json_status_demo", "expectation_type": "expect_column_values_to_be_json_parseable",
     "kwargs": {"column": "status"},
     "dataset_name": DATASET, "column_name": "status", "description": "JSON parseable demo 2 (may fail)"},

    # --- Length between ---
    {"rule_name": "length_between_email", "expectation_type": "expect_column_value_lengths_to_be_between",
     "kwargs": {"column": "email", "min_value": 10, "max_value": 50},
     "dataset_name": DATASET, "column_name": "email", "description": "email length between 10 and 50"},
    {"rule_name": "length_between_status", "expectation_type": "expect_column_value_lengths_to_be_between",
     "kwargs": {"column": "status", "min_value": 3, "max_value": 20},
     "dataset_name": DATASET, "column_name": "status", "description": "status length between 3 and 20"},

    # --- Length equal ---
    {"rule_name": "length_equal_status_6", "expectation_type": "expect_column_value_lengths_to_equal",
     "kwargs": {"column": "status", "value": 6},
     "dataset_name": DATASET, "column_name": "status", "description": "status length equals 6 (inactive)"},
    {"rule_name": "length_equal_status_7", "expectation_type": "expect_column_value_lengths_to_equal",
     "kwargs": {"column": "status", "value": 7},
     "dataset_name": DATASET, "column_name": "status", "description": "status length equals 7 (pending)"},

    # --- Increasing (customer_id is 1..100) ---
    {"rule_name": "increasing_customer_id", "expectation_type": "expect_column_values_to_be_increasing",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "customer_id is increasing"},
    {"rule_name": "increasing_age_demo", "expectation_type": "expect_column_values_to_be_increasing",
     "kwargs": {"column": "age"},
     "dataset_name": DATASET, "column_name": "age", "description": "age increasing (may fail)"},

    # --- Decreasing ---
    {"rule_name": "decreasing_demo_1", "expectation_type": "expect_column_values_to_be_decreasing",
     "kwargs": {"column": "customer_id"},
     "dataset_name": DATASET, "column_name": "customer_id", "description": "Decreasing demo (will fail)"},
    {"rule_name": "decreasing_demo_2", "expectation_type": "expect_column_values_to_be_decreasing",
     "kwargs": {"column": "age"},
     "dataset_name": DATASET, "column_name": "age", "description": "Decreasing demo 2 (will fail)"},

    # --- Table row count between ---
    {"rule_name": "table_row_count_between", "expectation_type": "expect_table_row_count_to_be_between",
     "kwargs": {"min_value": 1, "max_value": 1000000},
     "dataset_name": DATASET, "description": "Table has 1 to 1M rows"},
    {"rule_name": "table_row_count_between_tight", "expectation_type": "expect_table_row_count_to_be_between",
     "kwargs": {"min_value": 50, "max_value": 150},
     "dataset_name": DATASET, "description": "Table has 50 to 150 rows"},

    # --- Table row count equal ---
    {"rule_name": "table_row_count_equal_100", "expectation_type": "expect_table_row_count_to_equal",
     "kwargs": {"value": 100},
     "dataset_name": DATASET, "description": "Table has exactly 100 rows"},
    {"rule_name": "table_row_count_equal_99", "expectation_type": "expect_table_row_count_to_equal",
     "kwargs": {"value": 99},
     "dataset_name": DATASET, "description": "Table has 99 rows (may fail)"},

    # --- Table column count between ---
    {"rule_name": "table_col_count_between", "expectation_type": "expect_table_column_count_to_be_between",
     "kwargs": {"min_value": 1, "max_value": 20},
     "dataset_name": DATASET, "description": "Table has 1 to 20 columns"},
    {"rule_name": "table_col_count_between_tight", "expectation_type": "expect_table_column_count_to_be_between",
     "kwargs": {"min_value": 3, "max_value": 5},
     "dataset_name": DATASET, "description": "Table has 3 to 5 columns"},

    # --- Table column count equal ---
    {"rule_name": "table_col_count_equal_4", "expectation_type": "expect_table_column_count_to_equal",
     "kwargs": {"value": 4},
     "dataset_name": DATASET, "description": "Table has exactly 4 columns"},
    {"rule_name": "table_col_count_equal_5", "expectation_type": "expect_table_column_count_to_equal",
     "kwargs": {"value": 5},
     "dataset_name": DATASET, "description": "Table has 5 columns (may fail)"},

    # --- Table columns match ordered list ---
    {"rule_name": "table_cols_ordered", "expectation_type": "expect_table_columns_to_match_ordered_list",
     "kwargs": {"column_list": ["customer_id", "email", "status", "age"]},
     "dataset_name": DATASET, "description": "Columns match ordered list"},
    {"rule_name": "table_cols_ordered_alt", "expectation_type": "expect_table_columns_to_match_ordered_list",
     "kwargs": {"column_list": ["customer_id", "email", "age", "status"]},
     "dataset_name": DATASET, "description": "Columns match alternate order (may fail)"},

    # --- Table columns match set ---
    {"rule_name": "table_cols_set", "expectation_type": "expect_table_columns_to_match_set",
     "kwargs": {"column_set": ["customer_id", "email", "status", "age"]},
     "dataset_name": DATASET, "description": "Columns match set"},
    {"rule_name": "table_cols_set_extended", "expectation_type": "expect_table_columns_to_match_set",
     "kwargs": {"column_set": ["customer_id", "email", "status", "age", "created_at"]},
     "dataset_name": DATASET, "description": "Columns include extra (may fail)"},

    # --- Compound unique ---
    {"rule_name": "compound_unique_cust_email", "expectation_type": "expect_compound_columns_to_be_unique",
     "kwargs": {"column_list": ["customer_id", "email"]},
     "dataset_name": DATASET, "description": "customer_id+email compound unique"},
    {"rule_name": "compound_unique_cust_status", "expectation_type": "expect_compound_columns_to_be_unique",
     "kwargs": {"column_list": ["customer_id", "status"]},
     "dataset_name": DATASET, "description": "customer_id+status compound unique"},
]


def seed_comprehensive_rules(replace_existing: bool = True):
    """Seed at least 2 rules per expectation type. If replace_existing, clears all first. Otherwise upserts: update if same rule_name+dataset exists."""
    session = db_manager.get_session()
    try:
        if replace_existing:
            deleted = session.query(DataQualityRule).delete()
            session.commit()
            print(f"  Cleared {deleted} existing rules.")

        added = 0
        updated = 0
        for r in COMPREHENSIVE_RULES:
            existing = session.query(DataQualityRule).filter(
                DataQualityRule.rule_name == r["rule_name"],
                DataQualityRule.dataset_name == r["dataset_name"],
            ).first()
            if existing:
                existing.expectation_type = r["expectation_type"]
                existing.kwargs = r["kwargs"]
                existing.column_name = r.get("column_name")
                existing.description = r.get("description")
                existing.is_active = True
                updated += 1
            else:
                rule = DataQualityRule(
                    rule_name=r["rule_name"],
                    expectation_type=r["expectation_type"],
                    kwargs=r["kwargs"],
                    dataset_name=r["dataset_name"],
                    column_name=r.get("column_name"),
                    description=r.get("description"),
                    is_active=True,
                )
                session.add(rule)
                added += 1
        session.commit()
        total = session.query(DataQualityRule).count()
        print(f"  Added {added}, updated {updated} rules. Total: {total} active rules.")
    finally:
        session.close()


def main():
    print("Seeding comprehensive data quality rules (2+ per expectation type)...")
    db_manager.create_tables()
    seed_comprehensive_rules(replace_existing=True)
    print("Done. Run: python scripts/run_expectations.py --save-results")


if __name__ == "__main__":
    main()
