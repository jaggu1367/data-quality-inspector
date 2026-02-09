"""
Command-line interface for the Data Quality Framework
"""
import argparse
import json
import sys
from typing import Optional
import pandas as pd

from dq_framework.database import db_manager
from dq_framework.rule_manager import RuleManager
from dq_framework.validator import DataQualityValidator


def init_db(args):
    """Initialize database tables"""
    print("Creating database tables...")
    db_manager.create_tables()
    print("Database tables created successfully!")


def create_rule(args):
    """Create a new data quality rule"""
    with RuleManager() as rm:
        kwargs = json.loads(args.kwargs) if isinstance(args.kwargs, str) else args.kwargs
        
        rule = rm.create_rule(
            rule_name=args.rule_name,
            expectation_type=args.expectation_type,
            kwargs=kwargs,
            dataset_name=args.dataset_name,
            column_name=args.column_name,
            description=args.description
        )
        print(f"Rule created successfully!")
        print(f"  ID: {rule.id}")
        print(f"  Name: {rule.rule_name}")
        print(f"  Type: {rule.expectation_type}")
        print(f"  Dataset: {rule.dataset_name}")


def list_rules(args):
    """List all rules"""
    with RuleManager() as rm:
        rules = rm.get_all_rules(active_only=args.active_only)
        
        if not rules:
            print("No rules found.")
            return
        
        print(f"\nFound {len(rules)} rule(s):\n")
        for rule in rules:
            status = "Active" if rule.is_active else "Inactive"
            print(f"  [{rule.id}] {rule.rule_name} ({status})")
            print(f"      Type: {rule.expectation_type}")
            print(f"      Dataset: {rule.dataset_name}")
            if rule.column_name:
                print(f"      Column: {rule.column_name}")
            if rule.description:
                print(f"      Description: {rule.description}")
            print()


def validate_file(args):
    """Validate a CSV file against rules"""
    # Load CSV file
    try:
        df = pd.read_csv(args.file)
        print(f"Loaded {len(df)} rows from {args.file}")
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            dataset_name=args.dataset_name,
            batch_identifier=args.batch_id,
            save_results=args.save_results
        )
        
        print(f"\nValidation Results for dataset: {result['dataset_name']}")
        print(f"  Total Rules: {result['summary']['total_rules']}")
        print(f"  Passed: {result['summary']['passed']}")
        print(f"  Failed: {result['summary']['failed']}")
        print(f"  Overall: {'PASSED' if result['success'] else 'FAILED'}")
        
        if args.verbose:
            print("\nDetailed Results:")
            for rule_name, rule_result in result['results'].items():
                status = "✓" if rule_result.get('success') else "✗"
                print(f"  {status} {rule_name}: {rule_result.get('success', False)}")
                if rule_result.get('exception_info'):
                    print(f"      Error: {rule_result['exception_info']}")


def main():
    parser = argparse.ArgumentParser(description="Data Quality Framework CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init DB command
    init_parser = subparsers.add_parser('init-db', help='Initialize database tables')
    init_parser.set_defaults(func=init_db)
    
    # Create rule command
    create_parser = subparsers.add_parser('create-rule', help='Create a new data quality rule')
    create_parser.add_argument('--rule-name', required=True, help='Rule name')
    create_parser.add_argument('--expectation-type', required=True, help='Great Expectations expectation type')
    create_parser.add_argument('--kwargs', required=True, help='JSON string of kwargs')
    create_parser.add_argument('--dataset-name', required=True, help='Dataset name')
    create_parser.add_argument('--column-name', help='Column name (if applicable)')
    create_parser.add_argument('--description', help='Rule description')
    create_parser.set_defaults(func=create_rule)
    
    # List rules command
    list_parser = subparsers.add_parser('list-rules', help='List all rules')
    list_parser.add_argument('--active-only', action='store_true', help='Show only active rules')
    list_parser.set_defaults(func=list_rules)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a CSV file')
    validate_parser.add_argument('--file', required=True, help='Path to CSV file')
    validate_parser.add_argument('--dataset-name', required=True, help='Dataset name')
    validate_parser.add_argument('--batch-id', help='Batch identifier')
    validate_parser.add_argument('--save-results', action='store_true', help='Save results to database')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    validate_parser.set_defaults(func=validate_file)
    
    args = parser.parse_args()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
