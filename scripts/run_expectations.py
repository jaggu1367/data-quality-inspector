"""
Run all active data quality rules from the data_quality_rules table against a sample CSV.

Rules are read from the data_quality_rules table (active only). Results are optionally
saved to validation_results.

Usage (from project root):
  python scripts/run_expectations.py
  python scripts/run_expectations.py --file data/sample_customers_100.csv --dataset-name customers --save-results
"""
import sys
import os
import argparse

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd
from dq_framework.database import db_manager
from dq_framework.validator import DataQualityValidator
from db_init import seed_data_quality_rules_if_empty

DEFAULT_CSV = "data/sample_customers_100.csv"
DEFAULT_DATASET = "customers"


def main():
    parser = argparse.ArgumentParser(
        description="Run active data quality rules from data_quality_rules table against a CSV"
    )
    parser.add_argument("--file", default=DEFAULT_CSV, help=f"Path to CSV (default: {DEFAULT_CSV})")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET, help=f"Dataset name for rules (default: {DEFAULT_DATASET})")
    parser.add_argument("--comprehensive", action="store_true", help="Seed 2+ rules per expectation type before running")
    parser.add_argument("--batch-id", default=None, help="Optional batch identifier for validation_results")
    parser.add_argument("--save-results", action="store_true", help="Save validation results to the database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-expectation details")
    args = parser.parse_args()

    print("=" * 60)
    print("Data Quality: Run active rules from data_quality_rules on CSV")
    print("=" * 60)

    print("\n1. Initializing database...")
    db_manager.create_tables()
    if args.comprehensive:
        import subprocess
        subprocess.run([sys.executable, os.path.join(_root, "scripts", "seed_comprehensive_rules.py")], check=True, cwd=_root)
    else:
        seed_data_quality_rules_if_empty()
    print("   Database ready.")

    csv_path = args.file
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(_root, csv_path)
    if not os.path.isfile(csv_path):
        print(f"\nError: CSV not found: {csv_path}")
        sys.exit(1)
    print(f"\n2. Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")

    print(f"\n3. Running all active rules for dataset '{args.dataset_name}'...")
    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            dataset_name=args.dataset_name,
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
