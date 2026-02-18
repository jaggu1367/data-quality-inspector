"""
Load any CSV file into a SQLite table.

Treats the first row as header by default. Table schema is inferred from the CSV.
Use --table to specify the target table name, or it is derived from the CSV filename.

Usage (from project root):
  python scripts/load_csv_to_sqlite.py --all          # Load all sample data (customers, orders, products)
  python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers
  python scripts/load_csv_to_sqlite.py --file data/other_data.csv
"""
import re
import sys
import os
import argparse

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pandas as pd
from sqlalchemy import create_engine

DEFAULT_CSV = "data/sample_customers_100.csv"
DATA_STORE_DB = "data_store.db"

SAMPLE_CSVS = [
    ("data/sample_customers_100.csv", "customers"),
    ("data/orders.csv", "orders"),
    ("data/products.csv", "products"),
]


def sanitize_column_name(name: str) -> str:
    """Sanitize column name for SQLite (e.g., spaces, special chars)."""
    # Replace spaces and invalid chars with underscore
    sanitized = re.sub(r"[^\w]", "_", str(name))
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "column"


def derive_table_name(csv_path: str) -> str:
    """Derive table name from CSV filename (without extension)."""
    basename = os.path.basename(csv_path)
    name, _ = os.path.splitext(basename)
    return sanitize_column_name(name) if name else "table"


def load_csv_to_sqlite(
    csv_path: str,
    table_name: str,
    *,
    header: bool = True,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> int:
    """Load CSV file into SQLite table. Returns number of rows loaded."""
    db_path = DATA_STORE_DB if os.path.isabs(DATA_STORE_DB) else os.path.join(_root, DATA_STORE_DB)
    # Use forward slashes for SQLAlchemy connection string (Windows compatibility)
    conn_str = f"sqlite:///{os.path.normpath(db_path).replace(os.sep, '/')}"
    engine = create_engine(conn_str)

    # Read CSV (first row as header by default)
    df = pd.read_csv(
        csv_path,
        header=0 if header else None,
        sep=delimiter,
        encoding=encoding,
    )

    # Sanitize column names for SQLite
    if header:
        df.columns = [sanitize_column_name(c) for c in df.columns]
    else:
        # Generate column names: col_0, col_1, ...
        df.columns = [f"col_{i}" for i in range(len(df.columns))]

    # Load into SQLite (replace existing data)
    rows_loaded = len(df)
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    return rows_loaded


def main():
    parser = argparse.ArgumentParser(
        description="Load any CSV file into SQLite table (header row by default)"
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Load all sample CSVs (customers, orders, products) into data_store.db",
    )
    parser.add_argument(
        "--file",
        "-f",
        default=DEFAULT_CSV,
        help=f"Path to CSV file (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--table",
        "-t",
        default=None,
        help="Target table name (default: derived from CSV filename)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="CSV has no header row; use col_0, col_1, ... as column names",
    )
    parser.add_argument(
        "--delimiter",
        "-d",
        default=",",
        help="CSV delimiter (default: ',')",
    )
    parser.add_argument(
        "--encoding",
        "-e",
        default="utf-8",
        help="CSV file encoding (default: utf-8)",
    )
    args = parser.parse_args()

    db_path = DATA_STORE_DB if os.path.isabs(DATA_STORE_DB) else os.path.join(_root, DATA_STORE_DB)

    if args.all:
        print("=" * 60)
        print("Load CSV to SQLite (all sample data)")
        print("=" * 60)
        print(f"\n  Database: {db_path}\n")
        try:
            total = 0
            for rel_path, table_name in SAMPLE_CSVS:
                csv_path = os.path.join(_root, rel_path) if not os.path.isabs(rel_path) else rel_path
                if not os.path.isfile(csv_path):
                    print(f"  Warning: {rel_path} not found, skipping.")
                    continue
                rows = load_csv_to_sqlite(csv_path, table_name, delimiter=args.delimiter, encoding=args.encoding)
                print(f"  Loaded {rows} rows into '{table_name}'")
                total += rows
            print(f"\n  Total: {total} rows loaded.")
            print("\n" + "=" * 60)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)
        return

    csv_path = args.file
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(_root, csv_path)

    if not os.path.isfile(csv_path):
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    table_name = args.table or derive_table_name(csv_path)

    print("=" * 60)
    print("Load CSV to SQLite")
    print("=" * 60)
    print(f"\n  CSV file:     {csv_path}")
    print(f"  Database:     {db_path}")
    print(f"  Target table: {table_name}")
    print(f"  Has header:   {not args.no_header}")

    try:
        rows = load_csv_to_sqlite(
            csv_path,
            table_name,
            header=not args.no_header,
            delimiter=args.delimiter,
            encoding=args.encoding,
        )
        print(f"\n  Loaded {rows} rows into '{table_name}' table.")
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
