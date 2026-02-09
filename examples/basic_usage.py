"""
Basic usage examples for the Data Quality Framework
"""
import sys
import os

# Ensure project root is on path so dq_framework can be imported when run as script
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd

# Import database components
from dq_framework.database import db_manager
from dq_framework.rule_manager import RuleManager
from dq_framework.validator import DataQualityValidator


def example_create_rules():
    """Example: Create data quality rules"""
    print("Creating data quality rules...")
    
    with RuleManager() as rm:
        # Delete existing rules if they exist (for demo purposes)
        try:
            existing_rules = rm.get_rules_by_dataset("customers", active_only=False)
            for rule in existing_rules:
                rm.delete_rule(rule.id)
        except Exception:
            pass  # Ignore errors if tables don't exist yet
        # Example 1: Column not null check
        rm.create_rule(
            rule_name="customer_id_not_null",
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": "customer_id"},
            dataset_name="customers",
            description="Ensure customer_id column has no null values"
        )
        
        # Example 2: Column values in set
        rm.create_rule(
            rule_name="status_valid_values",
            expectation_type="expect_column_values_to_be_in_set",
            kwargs={"column": "status", "value_set": ["active", "inactive", "pending"]},
            dataset_name="customers",
            description="Ensure status column contains only valid values"
        )
        
        # Example 3: Column values between range
        rm.create_rule(
            rule_name="age_range_check",
            expectation_type="expect_column_values_to_be_between",
            kwargs={"column": "age", "min_value": 0, "max_value": 120},
            dataset_name="customers",
            description="Ensure age is between 0 and 120"
        )
        
        # Example 4: Table row count check
        rm.create_rule(
            rule_name="min_row_count",
            expectation_type="expect_table_row_count_to_be_between",
            kwargs={"min_value": 1, "max_value": 1000000},
            dataset_name="customers",
            description="Ensure table has at least 1 row"
        )
        
        # Example 5: Column unique check
        rm.create_rule(
            rule_name="email_unique",
            expectation_type="expect_column_values_to_be_unique",
            kwargs={"column": "email"},
            dataset_name="customers",
            description="Ensure email addresses are unique"
        )
        
        print("Rules created successfully!")


def example_validate_data():
    """Example: Validate data against rules"""
    print("\nValidating data...")
    
    # Create sample data
    data = {
        'customer_id': [1, 2, 3, 4, None],  # One null value - should fail
        'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'e@test.com'],
        'status': ['active', 'inactive', 'pending', 'active', 'invalid'],  # One invalid - should fail
        'age': [25, 30, 35, 150, 28]  # One out of range - should fail
    }
    df = pd.DataFrame(data)
    
    print(f"Sample data:\n{df}\n")
    
    # Validate the dataset
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            dataset_name="customers",
            batch_identifier="batch_001",
            save_results=True
        )
        
        print(f"Validation Results:")
        print(f"  Overall: {'PASSED' if result['success'] else 'FAILED'}")
        print(f"  Total Rules: {result['summary']['total_rules']}")
        print(f"  Passed: {result['summary']['passed']}")
        print(f"  Failed: {result['summary']['failed']}")
        
        print("\nDetailed Results:")
        for rule_name, rule_result in result['results'].items():
            status = "PASS" if rule_result.get('success') else "FAIL"
            print(f"  [{status}]: {rule_name}")
            if not rule_result.get('success'):
                if rule_result.get('exception_info'):
                    print(f"      Error: {rule_result['exception_info']}")
                elif rule_result.get('result'):
                    result_data = rule_result['result']
                    if 'result' in result_data:
                        unexpected_count = result_data['result'].get('unexpected_count', 0)
                        print(f"      Unexpected values: {unexpected_count}")


def example_query_rules():
    """Example: Query and manage rules"""
    print("\nQuerying rules...")
    
    with RuleManager() as rm:
        # Get all rules for a dataset
        rules = rm.get_rules_by_dataset("customers")
        print(f"Found {len(rules)} rules for 'customers' dataset:")
        for rule in rules:
            print(f"  - {rule.rule_name} ({rule.expectation_type})")
        
        # Get a specific rule
        rule = rm.get_rule_by_name("customer_id_not_null")
        if rule:
            print(f"\nRule details:")
            print(f"  ID: {rule.id}")
            print(f"  Name: {rule.rule_name}")
            print(f"  Type: {rule.expectation_type}")
            print(f"  Kwargs: {rule.kwargs}")
            print(f"  Active: {rule.is_active}")


def example_validation_history():
    """Example: Query validation history"""
    print("\nQuerying validation history...")
    
    with DataQualityValidator() as validator:
        history = validator.get_validation_history(
            dataset_name="customers",
            limit=10
        )
        
        print(f"Found {len(history)} recent validations:")
        for result in history:
            status = "PASS" if result.success else "FAIL"
            print(f"  [{result.validation_timestamp}] {status} - Rule ID: {result.rule_id}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("Data Quality Framework - Basic Usage Examples")
    print("=" * 60)
    
    # Ensure database tables exist (run db_init.py first, or we create them here)
    print("\n1. Ensuring database is initialized...")
    db_manager.create_tables()
    print("Database ready.")
    
    # Create rules
    print("\n2. Creating rules...")
    example_create_rules()
    
    # Query rules
    print("\n3. Querying rules...")
    example_query_rules()
    
    # Validate data
    print("\n4. Validating data...")
    example_validate_data()
    
    # Query validation history
    print("\n5. Querying validation history...")
    example_validation_history()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
