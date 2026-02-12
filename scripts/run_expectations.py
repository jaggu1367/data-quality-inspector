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
  python scripts/run_expectations.py --data-source-name orders_csv
  python scripts/run_expectations.py --all --save-results   # run all sources from config
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
    Load data from a source (csv or sqlite). Returns (DataFrame, rules_table).
    rules_table: used for rule matching; uses rules_table if present, else data_source_name.
    """
    source_type = source_config.get("type", "csv").lower()
    rules_table = source_config.get("rules_table") or source_config.get("data_source_name", "dataset")

    if source_type == "csv":
        path = source_config.get("path")
        if not path:
            raise ValueError("CSV source must have 'path'")
        full_path = path if os.path.isabs(path) else os.path.join(root_dir, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        df = pd.read_csv(full_path)
        return df, rules_table

    if source_type == "sqlite":
        database = source_config.get("database")
        table = source_config.get("table")
        if not database or not table:
            raise ValueError("SQLite source must have 'database' and 'table'")
        db_path = database if os.path.isabs(database) else os.path.join(root_dir, database)
        conn_str = f"sqlite:///{os.path.normpath(db_path).replace(os.sep, '/')}"
        engine = create_engine(conn_str)
        df = pd.read_sql_table(table, engine)
        return df, rules_table

    raise ValueError(f"Unknown source type: {source_type}. Expected 'csv' or 'sqlite'.")


def _run_one(
    data_source_name: str,
    source_config: dict,
    args: argparse.Namespace,
    root: str,
) -> bool:
    """Run expectations for one source. Returns True if all passed, False otherwise."""
    source_type = source_config.get("type", "csv")
    print(f"\n{'='*60}")
    print(f"Source: {data_source_name} ({source_type})")
    print("=" * 60)
    try:
        df, rules_key = load_data_from_source(source_config, root)
        if args.dataset_name and not args.all:
            rules_key = args.dataset_name
    except (FileNotFoundError, ValueError) as e:
        print(f"  Error: {e}")
        return False

    print(f"  Rows: {len(df)}, Columns: {list(df.columns)}")
    print(f"  Running active rules for '{rules_key}'...")

    batch_id = args.batch_id or (f"{data_source_name}" if args.all else None)
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            data_source_name=rules_key,
            batch_identifier=batch_id,
            save_results=args.save_results,
        )

    total = result["summary"]["total_rules"]
    passed = result["summary"]["passed"]
    failed = result["summary"]["failed"]

    print("\n  RESULTS:")
    print(f"    Overall: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"    Rules:   {passed}/{total} passed, {failed} failed")

    if args.verbose or failed > 0:
        for rule_name, rule_result in result["results"].items():
            ok = rule_result.get("success", False)
            symbol = "PASS" if ok else "FAIL"
            print(f"    [{symbol}] {rule_name}")
            if not ok and rule_result.get("exception_info"):
                print(f"        Error: {(rule_result['exception_info'] or '')[:150]}")

    return result["success"]


def main():
    parser = argparse.ArgumentParser(
        description="Run active data quality rules from data_quality_rules table against a data source (CSV or SQLite)"
    )
    parser.add_argument(
        "--data-source-name",
        "-s",
        help="Name of the data source from config/data_sources.json (e.g. customers_csv, customers_sqlite)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run expectations for all data sources in config",
    )
    parser.add_argument(
        "--sources-config",
        default=DEFAULT_SOURCES_CONFIG,
        help=f"Path to data sources config (default: {DEFAULT_SOURCES_CONFIG})",
    )
    parser.add_argument("--dataset-name", default=None, help="Override rules_table from config (optional)")
    parser.add_argument("--seed-dq-rules", action="store_true", help="Load rules from JSON before validation (only for --data-source-name when specified, else all)")
    parser.add_argument("--batch-id", default=None, help="Optional batch identifier for validation_results")
    parser.add_argument("--save-results", action="store_true", help="Save validation results to the database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-expectation details")
    args = parser.parse_args()

    if not args.all and not args.data_source_name:
        parser.error("Either --data-source-name or --all is required")

    print("=" * 60)
    print("Data Quality: Run active rules from data_quality_rules")
    print("=" * 60)

    print("\n1. Initializing database...")
    db_manager.create_tables()
    if args.seed_dq_rules:
        import subprocess
        seed_cmd = [sys.executable, os.path.join(_root, "scripts", "seed_dq_rules.py")]
        if args.all:
            pass  # seed all rules when --all
        elif args.data_source_name:
            seed_cmd.extend(["--data-source-name", args.data_source_name])
            seed_cmd.extend(["--sources-config", args.sources_config])
        subprocess.run(seed_cmd, check=True, cwd=_root)
    else:
        seed_data_quality_rules_if_empty()
    print("   Database ready.")

    config = load_sources_config(args.sources_config)
    sources_list = config.get("sources", [])
    sources_by_name = {s["data_source_name"]: s for s in sources_list if isinstance(s, dict) and "data_source_name" in s}

    if args.all:
        data_source_names = list(sources_by_name.keys())
        if not data_source_names:
            print("\nError: No sources found in config.")
            sys.exit(1)
        print(f"\nRunning expectations for {len(data_source_names)} source(s): {data_source_names}")
        exit_code = 0
        for dsn in data_source_names:
            source_config = sources_by_name[dsn]
            if _run_one(dsn, source_config, args, _root):
                continue
            exit_code = 1
        sys.exit(exit_code)

    if args.data_source_name not in sources_by_name:
        print(f"\nError: Unknown data source '{args.data_source_name}'. Available: {list(sources_by_name.keys())}")
        sys.exit(1)

    success = _run_one(args.data_source_name, sources_by_name[args.data_source_name], args, _root)
    if args.save_results:
        print("\n  Validation results saved to validation_results table.")
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
