"""
Advanced usage examples for the Data Quality Framework
"""
import pandas as pd
from dq_framework.database import db_manager
from dq_framework.rule_manager import RuleManager
from dq_framework.validator import DataQualityValidator


def example_regex_validation():
    """Example: Using regex validations"""
    print("Creating regex validation rules...")
    
    with RuleManager() as rm:
        # Email format validation
        rm.create_rule(
            rule_name="email_format_check",
            expectation_type="expect_column_values_to_match_regex",
            kwargs={"column": "email", "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
            dataset_name="users",
            description="Validate email format using regex"
        )
        
        # Phone number validation (US format)
        rm.create_rule(
            rule_name="phone_format_check",
            expectation_type="expect_column_values_to_match_regex",
            kwargs={"column": "phone", "regex": r"^\(\d{3}\) \d{3}-\d{4}$"},
            dataset_name="users",
            description="Validate phone number format"
        )
    
    # Test data
    data = {
        'email': ['valid@example.com', 'invalid-email', 'another@test.org'],
        'phone': ['(123) 456-7890', '123-456-7890', '(999) 888-7777']
    }
    df = pd.DataFrame(data)
    
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(df, dataset_name="users")
        print(f"\nRegex validation results: {'PASSED' if result['success'] else 'FAILED'}")


def example_statistical_validation():
    """Example: Using statistical validations"""
    print("\nCreating statistical validation rules...")
    
    with RuleManager() as rm:
        # Mean value check
        rm.create_rule(
            rule_name="salary_mean_check",
            expectation_type="expect_column_mean_to_be_between",
            kwargs={"column": "salary", "min_value": 50000, "max_value": 100000},
            dataset_name="employees",
            description="Ensure average salary is between 50k and 100k"
        )
        
        # Standard deviation check
        rm.create_rule(
            rule_name="salary_stdev_check",
            expectation_type="expect_column_stdev_to_be_between",
            kwargs={"column": "salary", "min_value": 10000, "max_value": 30000},
            dataset_name="employees",
            description="Ensure salary standard deviation is reasonable"
        )
    
    # Test data
    import numpy as np
    np.random.seed(42)
    data = {
        'salary': np.random.normal(75000, 15000, 100)
    }
    df = pd.DataFrame(data)
    
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(df, dataset_name="employees")
        print(f"Statistical validation results: {'PASSED' if result['success'] else 'FAILED'}")


def example_table_level_validation():
    """Example: Table-level validations"""
    print("\nCreating table-level validation rules...")
    
    with RuleManager() as rm:
        # Column count check
        rm.create_rule(
            rule_name="required_columns_check",
            expectation_type="expect_table_column_count_to_equal",
            kwargs={"value": 4},
            dataset_name="orders",
            description="Ensure table has exactly 4 columns"
        )
        
        # Column names check (use list for JSON serialization in DB)
        rm.create_rule(
            rule_name="column_names_check",
            expectation_type="expect_table_columns_to_match_set",
            kwargs={"column_set": ["order_id", "customer_id", "product_id", "quantity"]},
            dataset_name="orders",
            description="Ensure table has required columns"
        )
    
    # Test data
    data = {
        'order_id': [1, 2, 3],
        'customer_id': [101, 102, 103],
        'product_id': [201, 202, 203],
        'quantity': [2, 1, 3]
    }
    df = pd.DataFrame(data)
    
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(df, dataset_name="orders")
        print(f"Table-level validation results: {'PASSED' if result['success'] else 'FAILED'}")


def example_rule_management():
    """Example: Managing rules (update, deactivate, activate)"""
    print("\nManaging rules...")
    
    with RuleManager() as rm:
        # Create a rule
        rule = rm.create_rule(
            rule_name="test_rule",
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": "test_column"},
            dataset_name="test_dataset",
            description="Test rule"
        )
        print(f"Created rule: {rule.rule_name} (ID: {rule.id})")
        
        # Update rule
        updated_rule = rm.update_rule(
            rule_id=rule.id,
            description="Updated test rule description",
            kwargs={"column": "updated_column"}
        )
        print(f"Updated rule: {updated_rule.description}")
        
        # Deactivate rule
        deactivated_rule = rm.deactivate_rule(rule.id)
        print(f"Deactivated rule: {deactivated_rule.is_active}")
        
        # Activate rule
        activated_rule = rm.activate_rule(rule.id)
        print(f"Activated rule: {activated_rule.is_active}")


def _ensure_clean_rules():
    """Remove rules that examples will create so the script can be run repeatedly."""
    rule_names = [
        "email_format_check",
        "phone_format_check",
        "salary_mean_check",
        "salary_stdev_check",
        "required_columns_check",
        "column_names_check",
        "test_rule",
    ]
    with RuleManager() as rm:
        for name in rule_names:
            rule = rm.get_rule_by_name(name)
            if rule:
                rm.delete_rule(rule.id)


def main():
    """Run advanced examples"""
    print("=" * 60)
    print("Data Quality Framework - Advanced Usage Examples")
    print("=" * 60)
    
    # Ensure database tables exist (run db_init.py first, or we create them here)
    db_manager.create_tables()
    # Remove existing demo rules so examples can run again without UNIQUE errors
    _ensure_clean_rules()
    
    # Run examples
    example_regex_validation()
    example_statistical_validation()
    example_table_level_validation()
    example_rule_management()
    
    print("\n" + "=" * 60)
    print("Advanced examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
