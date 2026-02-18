# Data Quality Inspector

> Validate your data with **Great Expectations** (v1.11.3) and store rules in a **SQLite** database—no separate database server needed.

**First time here?** Run these four commands from the project root:

```bash
pip install -r requirements.txt
python db_init.py
python scripts/load_csv_to_sqlite.py --all
python scripts/run_expectations.py --source-id customers_sqlite --save-results --verbose
```

For more detail and options, see [First-time setup](#first-time-setup) below.

---

## First-time setup

Follow these steps from the **project root** (the folder that contains `dq_framework`, `scripts`, and `db_init.py`).

### 1. Check Python

You need **Python 3.8+** and **pip**. Check your versions:

```bash
python --version
pip --version
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

You're ready when this completes without errors.

### 3. Initialize the database

```bash
python db_init.py
```

You should see: *"Database tables created successfully."* A file `dq_framework.db` will appear in the project root—this stores your rules and validation history.

### 4. Load sample data (for SQLite sources)

The sample config uses SQLite tables. Load CSV files into `data_store.db`:

| Command | Description |
|---------|-------------|
| `python scripts/load_csv_to_sqlite.py --all` | Load all sample data (customers, orders, products) |
| `python scripts/load_csv_to_sqlite.py -a` | Same as `--all` (short form) |
| `python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers` | Load a specific CSV into a named table |
| `python scripts/load_csv_to_sqlite.py -f data/orders.csv -t orders` | Short form: load `orders.csv` into `orders` table |
| `python scripts/load_csv_to_sqlite.py --file data/products.csv` | Load a file; table name is derived from filename (`products`) |
| `python scripts/load_csv_to_sqlite.py` | Load default file (`data/sample_customers_100.csv`); table name from filename |
| `python scripts/load_csv_to_sqlite.py --file data/file.csv --no-header` | Load CSV without header row (columns become `col_0`, `col_1`, …) |
| `python scripts/load_csv_to_sqlite.py --all --delimiter ";"` | Load all with semicolon delimiter |
| `python scripts/load_csv_to_sqlite.py -f data/file.csv --encoding utf-16` | Load with specific encoding |

**Options:** `-f/--file` path, `-t/--table` name, `--no-header`, `-d/--delimiter` (default `,`), `-e/--encoding` (default `utf-8`). Use `--all` or `-a` to load all sample CSVs at once.

### 5. Run your first validation

```bash
python scripts/run_expectations.py --source-id customers_sqlite --save-results --verbose
```

You should see validation results: *"Overall: PASSED (or FAILED)"* with rule-by-rule pass/fail details.

---

**You're all set.** From here you can validate other sources or all sources at once (see [Run validations](#run-validations)).

---

## Quick reference

| I want to… | Command |
|------------|---------|
| **Load all sample data into SQLite** | `python scripts/load_csv_to_sqlite.py --all` |
| **Run validations** | `python scripts/run_expectations.py --source-id customers_sqlite --save-results` |
| **Validate all sources** | `python scripts/run_expectations.py --all --save-results` |
| **List rules** | `python -m dq_framework.cli list-rules` |

---

## What’s in this repo?

- **Define rules** (e.g., “this column must not be null”, “values must be in this set”) and store them in SQLite.
- **Validate** DataFrames, SQLite tables, or CSV files against those rules and get pass/fail results.
- **Track history** of every validation (timestamps, batch IDs, full results).
- **Use from code or CLI**—create rules, list them, and run validations from Python or the command line.

**Requirements:** Python 3.8+ and pip. SQLite is included with Python.

---

## Table of contents

- [First-time setup](#first-time-setup)
- [Run validations](#run-validations)
- [Configuration](#configuration)
- [Quick start in code](#quick-start-in-code)
- [Command-line interface](#command-line-interface)
- [Working with the database](#working-with-the-database)
- [Database schema (reference)](#database-schema-reference)
- [API reference](#api-reference)
- [Project layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [Requirements & support](#requirements--support)

---

## Run validations

After [first-time setup](#first-time-setup), you can run validations anytime. Data sources are defined in `config/data_sources.json`.

| What you want to do | Command |
|---------------------|---------|
| Validate customers (SQLite) | `python scripts/run_expectations.py --source-id customers_sqlite --save-results` |
| Validate orders (SQLite) | `python scripts/run_expectations.py --source-id orders_sqlite --save-results` |
| Validate products (SQLite) | `python scripts/run_expectations.py --source-id products_sqlite --save-results` |
| **Validate all sources** | `python scripts/run_expectations.py --all --save-results` |
| Generate HTML/email report | `python scripts/run_expectations.py --all --save-results --send-report` |

Add `--verbose` to any command to see per-rule pass/fail details.

---

## Configuration

### Database

By default, the framework uses a SQLite file named `dq_framework.db` in the project root.

To use a different path, copy `.env.example` to `.env` and set:

```env
DB_PATH=path/to/your/dq_framework.db
```

### Data sources

Edit `config/data_sources.json` to define your data sources. Each source specifies:

- `source_id` — unique identifier (e.g., `customers_sqlite`)
- `data_source` — `csv` or `sqlite`
- `path` (for CSV) or `database` + `source_table` (for SQLite, e.g. `data_store.db` and `customers`)
- `rules_table` — name used to look up rules (e.g., `customers` matches rules in `rules/customers.json`)

---

## Quick start in code

### 1. Create rules

```python
from dq_framework.rule_manager import RuleManager

with RuleManager() as rm:
    rm.create_rule(
        rule_name="customer_id_not_null",
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "customer_id"},
        rules_table_name="customers",
        description="Ensure customer_id has no null values"
    )
    rm.create_rule(
        rule_name="status_valid",
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "status", "value_set": ["active", "inactive", "pending"]},
        rules_table_name="customers",
        description="Validate status values"
    )
```

### 2. Validate data

```python
import pandas as pd
from dq_framework.validator import DataQualityValidator
from sqlalchemy import create_engine

# Load from SQLite table
engine = create_engine("sqlite:///data_store.db")
df = pd.read_sql_table("customers", engine)

with DataQualityValidator() as validator:
    result = validator.validate_dataset(
        df=df,
        rules_table_name="customers",
        source_id="customers_sqlite",
        data_source="sqlite",
        source_table="customers",
        save_results=True
    )
    print(f"Validation: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Passed: {result['summary']['passed']}/{result['summary']['total_rules']}")
```

> **Note:** Use `rules_table_name` to match the rules; it corresponds to `rules_table` in `config/data_sources.json` or the JSON filename in `rules/` (e.g., `customers`).

---

## Command-line interface

All commands are run from the project root.

### Initialize the database (recommended before first use)

```bash
python db_init.py
```

Or:

```bash
python -m dq_framework.cli init-db
```

### Create a rule

```bash
python -m dq_framework.cli create-rule \
    --rule-name "email_not_null" \
    --expectation-type "expect_column_values_to_not_be_null" \
    --kwargs '{"column": "email"}' \
    --rules-table-name "users" \
    --description "Email must not be null"
```

### List rules

```bash
python -m dq_framework.cli list-rules
python -m dq_framework.cli list-rules --active-only
```

### Validate data

For SQLite tables (recommended), use `run_expectations.py`:

```bash
python scripts/run_expectations.py --source-id customers_sqlite --save-results --verbose
```

For CSV files, use the CLI:

```bash
python -m dq_framework.cli validate \
    --file data/sample_customers_100.csv \
    --rules-table-name "customers" \
    --source-id "customers_csv" \
    --save-results \
    --verbose
```

---

## Working with the database

- **Location:** By default, `dq_framework.db` is in the project root. Override with `DB_PATH` in `.env`.
- **Backup:** Copy the `.db` file, or use SQLite’s backup/restore. No separate server to manage.

### Query from Python (SQLAlchemy)

```python
from dq_framework.core import db_manager, DataQualityRule, ValidationResult

session = db_manager.get_session()
rules = session.query(DataQualityRule).filter(DataQualityRule.is_active == True).all()
results = session.query(ValidationResult).order_by(ValidationResult.validation_timestamp.desc()).limit(10).all()
session.close()
```

### Query with Python’s built-in sqlite3

```python
import sqlite3
conn = sqlite3.connect('dq_framework.db')
cursor = conn.cursor()
cursor.execute("SELECT rule_name, expectation_type FROM data_quality_rules WHERE is_active = 1")
rules = cursor.fetchall()
conn.close()
```

### Use a GUI

You can open `dq_framework.db` with [DB Browser for SQLite](https://sqlitebrowser.org/), [DBeaver](https://dbeaver.io/), or [SQLiteStudio](https://sqlitestudio.pl/).

### Useful SQL (in sqlite3 or a GUI)

```sql
-- Active rules for a data source
SELECT * FROM data_quality_rules WHERE rules_table_name = 'customers' AND is_active = 1;

-- Recent validation results
SELECT rule_id, success, validation_timestamp FROM validation_results ORDER BY validation_timestamp DESC LIMIT 10;
```

---

## Database schema (reference)

The framework uses two tables:

| Table | Purpose |
|-------|---------|
| `data_quality_rules` | Rule definitions (name, expectation type, kwargs, data source, etc.) |
| `validation_results` | One row per validation run (columns: id, when, source context, rule_id, outcome) |

Detailed column descriptions, relationships, and example queries are in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

---

## API reference

### RuleManager

```python
from dq_framework.rule_manager import RuleManager

with RuleManager() as rm:
    rule = rm.create_rule(rule_name="...", expectation_type="...", kwargs={...}, rules_table_name="...")
    rules = rm.get_rules_by_rules_table_name("customers")
    rule = rm.get_rule_by_name("rule_name")
    rm.update_rule(rule_id, kwargs={...})
    rm.deactivate_rule(rule_id)
    rm.activate_rule(rule_id)
```

### DataQualityValidator

```python
from dq_framework.validator import DataQualityValidator

with DataQualityValidator() as validator:
    result = validator.validate_dataset(df, data_source_name="customers")  # data_source_name = rules_table
    result = validator.validate_rule(df, rule_id=1)
    history = validator.get_validation_history(rules_table_name="customers")
```

---

## Supported expectation types

The framework supports **Great Expectations v1.11.3** expectation types, including:

- **Column:** `expect_column_values_to_not_be_null`, `expect_column_values_to_be_unique`, `expect_column_values_to_be_in_set`, `expect_column_values_to_be_between`, `expect_column_values_to_match_regex`, `expect_column_mean_to_be_between`, `expect_column_stdev_to_be_between`, and more.
- **Table:** `expect_table_row_count_to_be_between`, `expect_table_column_count_to_equal`, `expect_table_columns_to_match_set`, `expect_compound_columns_to_be_unique`, etc.

Full list and parameters: [Great Expectations Documentation](https://docs.greatexpectations.io/).

---

## Project layout

```
data-quality-inspector/
├── db_init.py              ← Run first: creates database and seeds default rules
├── dq_framework/           ← Main package
│   ├── core/               ← Config, database models, connection
│   ├── repositories/       ← Data access (rules, validation results)
│   ├── services/           ← RuleManager, DataQualityValidator
│   ├── expectations/       ← Great Expectations integration
│   ├── reports/            ← HTML and email report generation
│   ├── data/               ← Data source loading (CSV, SQLite)
│   ├── seeding/            ← Default rules and seeding logic
│   └── cli.py
├── config/
│   └── data_sources.json   ← Define SQLite tables and CSV data sources
├── rules/                  ← Rule definitions (JSON), e.g. customers.json
├── scripts/
│   ├── run_expectations.py ← Main validation script (run rules against data sources)
│   ├── seed_dq_rules.py    ← Load rules from JSON into database
│   ├── init_database.py    ← Alternative to db_init.py (tables only)
│   └── load_csv_to_sqlite.py   ← Load sample CSVs into data_store.db
├── data/                   ← Sample CSV files (loaded into data_store.db for SQLite sources)
├── requirements.txt
├── setup.py
├── .env.example            ← Copy to .env to customize DB_PATH
├── dq_framework.db         ← Created when you run db_init.py
├── README.md
└── DATABASE_SCHEMA.md      ← Full schema and query examples
```

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| **No active rules found** | Run `python db_init.py` (Step 3 of [First-time setup](#first-time-setup)) |
| **FileNotFoundError** (data file) | Run `python scripts/load_csv_to_sqlite.py --all` (Step 4 of [First-time setup](#first-time-setup)) to create `data_store.db` |
| **ModuleNotFoundError: dq_framework** | Run all commands from the project root (the folder with `db_init.py`), or run `pip install -e .` |
| **Unknown data source** | Check that the source name exists in `config/data_sources.json` |

---

## Requirements & support

- **Python:** 3.8+
- **Dependencies:** See `requirements.txt` (includes Great Expectations 1.11.3; SQLite is built into Python).

For bugs or questions, open an issue in the repository. For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md) if available.
