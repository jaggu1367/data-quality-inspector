"""
Command-line interface for the Data Quality Framework
"""
import argparse
import json
import os
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
            rules_table_name=args.rules_table_name,
            column_name=args.column_name,
            description=args.description
        )
        print(f"Rule created successfully!")
        print(f"  ID: {rule.id}")
        print(f"  Name: {rule.rule_name}")
        print(f"  Type: {rule.expectation_type}")
        print(f"  Rules table: {rule.rules_table_name}")


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
            print(f"      Rules table: {rule.rules_table_name}")
            if rule.column_name:
                print(f"      Column: {rule.column_name}")
            if rule.description:
                print(f"      Description: {rule.description}")
            print()


def _resolve_source_context(args, root: str) -> tuple[Optional[str], str, Optional[str]]:
    """Resolve source_id, data_source, source_table from data_sources.json when possible."""
    sources_config = os.path.join(root, "config", "data_sources.json")
    if not os.path.isfile(sources_config):
        return args.source_id, "csv", None
    try:
        with open(sources_config, encoding="utf-8") as f:
            config = json.load(f)
        sources = config.get("sources", []) or []
        for s in sources:
            if not isinstance(s, dict) or "source_id" not in s:
                continue
            if args.source_id and s.get("source_id") == args.source_id:
                return (
                    s.get("source_id"),
                    s.get("data_source") or "csv",
                    s.get("source_table"),
                )
            # Match by path when source_id not provided
            if not args.source_id and s.get("data_source", "").lower() == "csv":
                path = s.get("path", "")
                full_path = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
                file_abspath = os.path.abspath(args.file)
                if os.path.normpath(file_abspath) == os.path.normpath(full_path):
                    return (
                        s.get("source_id"),
                        s.get("data_source") or "csv",
                        s.get("source_table"),
                    )
    except (json.JSONDecodeError, OSError):
        pass
    return args.source_id, "csv", None


def validate_file(args):
    """Validate a CSV file (or other source) against rules."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    engine = getattr(args, "engine", "pandas")
    try:
        if engine == "spark":
            from dq_framework.data import load_data_from_source
            # For CLI validate, we support CSV path as a simple source config
            source_config = {"data_source": "csv", "path": args.file, "rules_table": args.rules_table_name}
            df, _ = load_data_from_source(source_config, root, engine="spark")
            row_count = df.count()
        else:
            df = pd.read_csv(args.file)
            row_count = len(df)
        print(f"Loaded {row_count} rows from {args.file} (engine={engine})")
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)
    source_id, data_source, source_table = _resolve_source_context(args, root)
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            data_source_name=args.rules_table_name,
            source_id=source_id,
            data_source=data_source,
            source_table=source_table,
            save_results=args.save_results
        )
        
        print(f"\nValidation Results for rules table: {result.get('rules_table_name', result.get('data_source_name', 'N/A'))}")
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
    create_parser.add_argument('--rules-table-name', required=True, help='Rules table name (e.g. customers)')
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
    validate_parser.add_argument('--engine', choices=['pandas', 'spark'], default='pandas', help='Data engine: pandas (default) or spark')
    validate_parser.add_argument('--rules-table-name', required=True, help='Rules table name to match rules (e.g. customers)')
    validate_parser.add_argument('--source-id', help='Source ID for validation_results (optional)')
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
