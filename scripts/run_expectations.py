"""
Run all active data quality rules from the data_quality_rules table against a data source.

Data can be loaded from a CSV file or a SQLite table. Use --source-id to specify
a source defined in config/data_sources.json; the config declares whether each source
is csv or sqlite.

Rules are read from the data_quality_rules table (active only). Results are optionally
saved to validation_results.

Usage (from project root):
  python scripts/run_expectations.py --source-id customers_csv --save-results
  python scripts/run_expectations.py --source-id customers_sqlite --save-results
  python scripts/run_expectations.py --source-id orders_csv
  python scripts/run_expectations.py --all --save-results   # run all sources from config
  python scripts/run_expectations.py --source-id customers_csv --send-report  # email report
  python scripts/run_expectations.py --source-id products_sqlite --log-results  # log results to console
"""
# Ensure distutils available for Python 3.12+ (PySpark toPandas uses it for compound-column expectations)
import setuptools  # noqa: F401

import sys
import os
import argparse
import json
from datetime import datetime

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dq_framework.core import db_manager
from dq_framework.data import load_data_from_source, load_sources_config
from dq_framework.reports import load_reports_config, maybe_write_html_report, send_email_report
from dq_framework.seeding import seed_data_quality_rules_if_empty
from dq_framework.services import DataQualityValidator

DEFAULT_SOURCES_CONFIG = "config/data_sources.json"
DEFAULT_REPORTS_CONFIG = "config/dq_report_config.json"


def _build_path_or_table(source_config: dict, root: str) -> str:
    """Build path_or_table string for source config."""
    st = source_config.get("data_source", "csv").lower()
    if st == "csv":
        p = source_config.get("path", "")
        return p if os.path.isabs(p) else os.path.join(root, p)
    if st == "sqlite":
        db = source_config.get("database", "")
        tbl = source_config.get("source_table", "")
        return f"{db}/{tbl}" if db and tbl else "N/A"
    if st == "hive":
        tbl = source_config.get("table") or source_config.get("source_table", "")
        return tbl or "N/A"
    return "N/A"


def _get_row_count(df) -> int:
    """Get row count for pandas or Spark DataFrame."""
    try:
        from pyspark.sql import DataFrame as SparkDataFrame
        if isinstance(df, SparkDataFrame):
            return df.count()
    except ImportError:
        pass
    return len(df)


def _get_columns(df) -> list:
    """Get column list for pandas or Spark DataFrame."""
    return list(df.columns)


def _log_validation_results_to_console(
    source_id: str,
    source_info: dict,
    result: dict,
) -> None:
    """Log validation results to console in a format similar to validation_results table."""
    print("\n  --- Validation Results (as logged to validation_results) ---")
    print(f"  source_id: {source_info.get('source_id', source_id)}")
    print(f"  data_source: {source_info.get('source_type', 'N/A')}")
    print(f"  path_or_table: {source_info.get('path_or_table', 'N/A')}")
    print(f"  rules_table: {result.get('rules_table_name', result.get('data_source_name', 'N/A'))}")
    print(f"  timestamp: {source_info.get('timestamp', 'N/A')}")
    print(f"  summary: {result['summary']['passed']}/{result['summary']['total_rules']} passed, {result['summary']['failed']} failed")
    print("  ---")
    for rule_name, rule_result in result["results"].items():
        success = rule_result.get("success", False)
        status = "PASS" if success else "FAIL"
        exc = rule_result.get("exception_info") or ""
        result_data = rule_result.get("result")
        print(f"  [{status}] {rule_name}")
        if not success and exc:
            print(f"      exception_info: {exc}")
        if result_data is not None:
            # Truncate large result payloads for console
            try:
                s = json.dumps(result_data, default=str)
                if len(s) > 200:
                    s = s[:200] + "..."
                print(f"      result: {s}")
            except (TypeError, ValueError):
                print(f"      result: {str(result_data)[:200]}")
    print("  ---")


def _run_one(
    source_id: str,
    source_config: dict,
    args: argparse.Namespace,
    root: str,
) -> tuple[bool, dict, dict]:
    """Run expectations for one source. Returns (success, source_info, result)."""
    source_type = source_config.get("data_source", "csv")
    engine = getattr(args, "engine", "pandas")
    print(f"\n{'='*60}")
    print(f"Source: {source_id} ({source_type}, engine={engine})")
    print("=" * 60)
    try:
        df, rules_key = load_data_from_source(source_config, root, engine=engine)
        if args.dataset_name and not args.all:
            rules_key = args.dataset_name
    except Exception as e:
        print(f"  Error: {e}")
        # Return structured info so email/HTML reports can be sent for the failure
        source_info = {
            "source_id": source_id,
            "source_type": source_type,
            "path_or_table": _build_path_or_table(source_config, root),
            "row_count": 0,
            "columns": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        result = {
            "success": False,
            "rules_table_name": source_config.get("rules_table", "N/A"),
            "summary": {"total_rules": 0, "passed": 0, "failed": 0},
            "results": {
                "load_error": {
                    "success": False,
                    "exception_info": str(e),
                }
            },
        }
        if getattr(args, "log_results", False):
            _log_validation_results_to_console(source_id, source_info, result)
        return False, source_info, result

    row_count = _get_row_count(df)
    columns = _get_columns(df)
    print(f"  Rows: {row_count}, Columns: {columns}")
    print(f"  Running active rules for '{rules_key}'...")

    source_info = {
        "source_id": source_id,
        "source_type": source_type,
        "path_or_table": _build_path_or_table(source_config, root),
        "row_count": row_count,
        "columns": columns,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Populate from data_sources.json for validation_results table
    source_id_val = source_config.get("source_id") or source_id
    data_source_val = source_config.get("data_source") or source_type or "csv"
    source_table_val = source_config.get("source_table") if source_type.lower() == "sqlite" else None

    with DataQualityValidator() as validator:
        result = validator.validate_dataset(
            df=df,
            data_source_name=rules_key,
            source_id=source_id_val,
            data_source=data_source_val,
            source_table=source_table_val,
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

    if getattr(args, "log_results", False):
        _log_validation_results_to_console(source_id, source_info, result)

    return result["success"], source_info, result


def main():
    parser = argparse.ArgumentParser(
        description="Run active data quality rules from data_quality_rules table against a data source (CSV or SQLite)"
    )
    parser.add_argument(
        "--source-id",
        "-s",
        help="Source ID from config/data_sources.json (e.g. customers_csv, customers_sqlite)",
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
    parser.add_argument(
        "--engine",
        choices=["pandas", "spark"],
        default="pandas",
        help="Data loading engine: pandas (default) or spark (PySpark)",
    )
    parser.add_argument("--dataset-name", default=None, help="Override rules_table from config (optional)")
    parser.add_argument("--seed-dq-rules", action="store_true", help="Load rules from JSON before validation (only for --source-id when specified, else all)")
    parser.add_argument("--save-results", action="store_true", help="Save validation results to the database")
    parser.add_argument("--log-results", action="store_true", help="Log validation results to console (same structure as validation_results table)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-expectation details")
    parser.add_argument("--send-report", action="store_true", help="Generate reports (email and/or HTML per config/dq_report_config.json)")
    parser.add_argument("--reports-config", default=DEFAULT_REPORTS_CONFIG, help=f"Path to reports config (default: {DEFAULT_REPORTS_CONFIG})")
    args = parser.parse_args()

    if not args.all and not args.source_id:
        parser.error("Either --source-id or --all is required")

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
        elif args.source_id:
            seed_cmd.extend(["--source-id", args.source_id])
            seed_cmd.extend(["--sources-config", args.sources_config])
        subprocess.run(seed_cmd, check=True, cwd=_root)
    else:
        seed_data_quality_rules_if_empty()
    print("   Database ready.")

    config = load_sources_config(args.sources_config, _root)
    sources_list = config.get("sources", [])
    sources_by_id = {s["source_id"]: s for s in sources_list if isinstance(s, dict) and "source_id" in s}

    if args.all:
        source_ids = list(sources_by_id.keys())
        if not source_ids:
            print("\nError: No sources found in config.")
            sys.exit(1)
        print(f"\nRunning expectations for {len(source_ids)} source(s): {source_ids}")
        exit_code = 0
        for source_id in source_ids:
            source_config = sources_by_id[source_id]
            success, source_info, result = _run_one(source_id, source_config, args, _root)
            if args.send_report and source_info and result:
                try:
                    if send_email_report(source_info, result, args.reports_config, _root):
                        print("  Email report sent.")
                except RuntimeError as e:
                    print(f"  Warning: {e}")
                html_path = maybe_write_html_report(source_info, result, args.reports_config, _root)
                if html_path:
                    print(f"  HTML report: {html_path}")
            if not success:
                exit_code = 1
        if exit_code == 1:
            print("\n" + "=" * 60)
            print("OVERALL: One or more sources had failing rules (see details above)")
            print("=" * 60)
        sys.exit(0)

    if args.source_id not in sources_by_id:
        print(f"\nError: Unknown source ID '{args.source_id}'. Available: {list(sources_by_id.keys())}")
        sys.exit(1)

    success, source_info, result = _run_one(args.source_id, sources_by_id[args.source_id], args, _root)
    if args.send_report and source_info and result:
        try:
            if send_email_report(source_info, result, args.reports_config, _root):
                print("\n  Email report sent.")
        except RuntimeError as e:
            print(f"\n  Warning: {e}")
        html_path = maybe_write_html_report(source_info, result, args.reports_config, _root)
        if html_path:
            print(f"\n  HTML report: {html_path}")
    if args.save_results:
        print("\n  Validation results saved to validation_results table.")
    print("\n" + "=" * 60)
    if not success:
        print("OVERALL: Validation FAILED (one or more rules did not pass)")
    print("=" * 60)
    sys.exit(0)  # always exit 0; failures are reported above


if __name__ == "__main__":
    main()
