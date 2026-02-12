"""
Run all active data quality rules from the data_quality_rules table against a data source.

Data can be loaded from a CSV file or a SQLite table. Use --data-source-name to specify
a source defined in config/data_sources.json; the config declares whether each source
is csv or sqlite.

Rules are read from the data_quality_rules table (active only). Results are optionally
saved to validation_results.

Usage (from project root):
  python scripts/run_expectations.py --data-source-name customers_csv --save-results
  python scripts/run_expectations.py --data-source-name customers_sqlite --save-results
  python scripts/run_expectations.py --file data/sample_customers_100.csv --dataset-name customers --save-results
"""
import json
import sys
import os
import argparse

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd
from sqlalchemy import create_engine
from dq_framework.database import db_manager
from dq_framework.validator import DataQualityValidator
from db_init import seed_data_quality_rules_if_empty

DEFAULT_CSV = "data/sample_customers_100.csv"
DEFAULT_DATASET = "customers"
DEFAULT_SOURCES_CONFIG = "config/data_sources.json"


def load_sources_config(config_path: str) -> dict:
    """Load data sources configuration from JSON file."""
    path = config_path if os.path.isabs(config_path) else os.path.join(_root, config_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data sources config not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_data_from_source(source_config: dict, root_dir: str) -> tuple[pd.DataFrame, str]:
    """
    Load data from a source (csv or sqlite). Returns (DataFrame, dataset_name).
    """
    source_type = source_config.get("type", "csv").lower()
    dataset_name = source_config.get("dataset_name", "dataset")

    if source_type == "csv":
        path = source_config.get("path")
        if not path:
            raise ValueError("CSV source must have 'path'")
        full_path = path if os.path.isabs(path) else os.path.join(root_dir, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        df = pd.read_csv(full_path)
        return df, dataset_name

    if source_type == "sqlite":
        database = source_config.get("database")
        table = source_config.get("table")
        if not database or not table:
            raise ValueError("SQLite source must have 'database' and 'table'")
        db_path = database if os.path.isabs(database) else os.path.join(root_dir, database)
        conn_str = f"sqlite:///{os.path.normpath(db_path).replace(os.sep, '/')}"
        engine = create_engine(conn_str)
        df = pd.read_sql_table(table, engine)
        return df, dataset_name

    raise ValueError(f"Unknown source type: {source_type}. Expected 'csv' or 'sqlite'.")


def main():
    parser = argparse.ArgumentParser(
        description="Run active data quality rules from data_quality_rules table against a data source (CSV or SQLite)"
    )
    parser.add_argument(
        "--data-source-name",
        "-s",
        default=None,
        help="Name of the data source from config/data_sources.json (e.g. customers_csv, customers_sqlite)",
    )
    parser.add_argument(
        "--sources-config",
        default=DEFAULT_SOURCES_CONFIG,
        help=f"Path to data sources config (default: {DEFAULT_SOURCES_CONFIG})",
    )
    parser.add_argument("--file", default=DEFAULT_CSV, help=f"Path to CSV (legacy; used when --data-source-name not set; default: {DEFAULT_CSV})")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET, help=f"Dataset name for rules (default: {DEFAULT_DATASET})")
    parser.add_argument("--comprehensive", action="store_true", help="Seed 2+ rules per expectation type before running")
    parser.add_argument("--batch-id", default=None, help="Optional batch identifier for validation_results")
    parser.add_argument("--save-results", action="store_true", help="Save validation results to the database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-expectation details")
    args = parser.parse_args()

    print("=" * 60)
    print("Data Quality: Run active rules from data_quality_rules")
    print("=" * 60)

    print("\n1. Initializing database...")
    db_manager.create_tables()
    if args.comprehensive:
        import subprocess
        subprocess.run([sys.executable, os.path.join(_root, "scripts", "seed_comprehensive_rules.py")], check=True, cwd=_root)
    else:
        seed_data_quality_rules_if_empty()
    print("   Database ready.")

    # Load data: either from config (--data-source-name) or legacy CSV (--file)
    if args.data_source_name:
        config = load_sources_config(args.sources_config)
        sources = config.get("sources", {})
        if args.data_source_name not in sources:
            print(f"\nError: Unknown data source '{args.data_source_name}'. Available: {list(sources.keys())}")
            sys.exit(1)
        source_config = sources[args.data_source_name]
        source_type = source_config.get("type", "csv")
        print(f"\n2. Loading from source '{args.data_source_name}' ({source_type})...")
        try:
            df, dataset_name = load_data_from_source(source_config, _root)
            if args.dataset_name != DEFAULT_DATASET:
                dataset_name = args.dataset_name  # Override with CLI if provided
        except (FileNotFoundError, ValueError) as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        csv_path = args.file
        if not os.path.isabs(csv_path):
            csv_path = os.path.join(_root, csv_path)
        if not os.path.isfile(csv_path):
            print(f"\nError: CSV not found: {csv_path}")
            sys.exit(1)
        print(f"\n2. Loading CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        dataset_name = args.dataset_name

    print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")

    print(f"\n3. Running all active rules for dataset '{dataset_name}'...")
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            dataset_name=dataset_name,
            batch_identifier=args.batch_id,
            save_results=args.save_results,
        )

    total = result["summary"]["total_rules"]
    passed = result["summary"]["passed"]
    failed = result["summary"]["failed"]

    print("\n" + "-" * 60)
    print("RESULTS")
    print("-" * 60)
    print(f"  Overall:        {'PASSED' if result['success'] else 'FAILED'}")
    print(f"  Total rules:    {total}")
    print(f"  Passed:         {passed}")
    print(f"  Failed:         {failed}")

    if args.verbose or failed > 0:
        print("\n  Per-expectation:")
        for rule_name, rule_result in result["results"].items():
            ok = rule_result.get("success", False)
            symbol = "PASS" if ok else "FAIL"
            print(f"    [{symbol}] {rule_name}")
            if not ok:
                if rule_result.get("exception_info"):
                    err = rule_result["exception_info"]
                    print(f"        Error: {(err or '')[:200]}")
                else:
                    res = (rule_result.get("result") or {})
                    if isinstance(res, dict):
                        inner = res.get("result") or res
                        if isinstance(inner, dict) and "unexpected_count" in inner:
                            print(f"        Unexpected count: {inner['unexpected_count']}")

    if args.save_results:
        print("\n  Validation results saved to validation_results table.")

    print("\n" + "=" * 60)
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
