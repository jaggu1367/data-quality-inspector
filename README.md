# Data Quality Framework

> Validate your data with **Great Expectations** (v1.11.3) and store rules in a **SQLite** database—no separate database server needed.

---

## What’s in this repo?

- **Define rules** (e.g. “this column must not be null”, “values must be in this set”) and store them in SQLite.
- **Validate** DataFrames, CSV files, or SQLite tables against those rules and get pass/fail results.
- **Data sources config**—declare CSV and SQLite sources in `config/data_sources.json` and run validations by source name.
- **Load CSV into SQLite**—use `load_csv_to_sqlite.py` to load CSV data into `data_store.db` for validation.
- **Track history** of every validation (timestamps, batch IDs, full results).
- **Use from code or CLI**—create rules, list them, and run validations from Python or the command line.

**You need:** Python 3.8+ and `pip`. SQLite is included with Python.

---

## Table of contents

- [Get started in 3 steps](#get-started-in-3-steps)
- [Run the examples](#run-the-examples)
- [Data sources and loading](#data-sources-and-loading)
- [Quick start in code](#quick-start-in-code)
- [Configuration](#configuration)
- [Command-line interface](#command-line-interface)
- [Working with the database](#working-with-the-database)
- [Database schema (reference)](#database-schema-reference)
- [API reference](#api-reference)
- [Expectation types reference](#expectation-types-reference)
- [Project layout](#project-layout)
- [Requirements & support](#requirements--support)

---

## Get started in 3 steps

Run these from the **project root** (the folder that contains `dq_framework`, `examples`, and `db_init.py`).

### Step 1: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create the database and tables

```bash
python db_init.py
```

You should see something like:

```
Initializing database...
  Database file: dq_framework.db
  Database tables created successfully.
  You can now run: python examples/basic_usage.py  or  python examples/advanced_usage.py
```

A file `dq_framework.db` will appear in the project root. That’s your SQLite database.

> **Tip:** If you forget this step and run the examples anyway, they will create the tables for you. Running `db_init.py` first is still recommended so everything is set up before you try the examples.

### Step 3: Run an example

```bash
python examples/basic_usage.py
```

Then try:

```bash
python examples/advanced_usage.py
```

That’s it—you’re set up.

---

## Run the examples

From the project root:

| What you want to do        | Command                          |
|----------------------------|----------------------------------|
| One-time DB setup          | `python db_init.py`              |
| Basic rules + validation   | `python examples/basic_usage.py` |
| Regex, stats, table rules  | `python examples/advanced_usage.py` |
| Load CSV into SQLite (`data_store.db`) | `python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers` |
| Run rules from CSV source | `python scripts/run_expectations.py --data-source-name customers_csv --save-results` |
| Run rules from SQLite source | `python scripts/run_expectations.py --data-source-name customers_sqlite --save-results` |
| Run rules on data source | `python scripts/run_expectations.py --data-source-name customers_csv --save-results --verbose` |

Make sure you’ve run `python db_init.py` at least once (or the example scripts will create the tables when you run them).

---

## Data sources and loading

The framework supports validating data from **CSV files** or **SQLite tables**. Define sources in `config/data_sources.json` and run validations by source name.

### Data sources config

Edit `config/data_sources.json` to declare your sources:

```json
{
  "sources": [
    {
      "data_source_name": "customers_csv",
      "type": "csv",
      "path": "data/sample_customers_100.csv",
      "rules_table": "customers"
    },
    {
      "data_source_name": "customers_sqlite",
      "type": "sqlite",
      "database": "data_store.db",
      "table": "customers",
      "rules_table": "customers"
    }
  ]
}
```

Each source has:
- **`data_source_name`**: unique identifier for the source (e.g. customers_csv, customers_sqlite)
- **`type`**: `"csv"` or `"sqlite"`
- **`rules_table`**: used to match rules (e.g. rules for `rules_table: "customers"` → `rules/customers.json`)
- **CSV**: `path` — path to the CSV file (relative to project root)
- **SQLite**: `database` and `table` — database file and table name

### Load CSV into SQLite

Use `load_csv_to_sqlite.py` to load CSV data into `data_store.db`:

```bash
python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers
```

Data is stored in `data_store.db` in the project root (separate from `dq_framework.db`, which holds rules and validation results).

### Run expectations by source name

```bash
# From CSV source (config)
python scripts/run_expectations.py --data-source-name customers_csv --save-results

# From SQLite source (config)
python scripts/run_expectations.py --data-source-name customers_sqlite --save-results

# Custom config file
python scripts/run_expectations.py --data-source-name customers_sqlite --sources-config path/to/sources.json
```

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
        data_source_name="customers",
        description="Ensure customer_id has no null values"
    )
    rm.create_rule(
        rule_name="status_valid",
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "status", "value_set": ["active", "inactive", "pending"]},
        data_source_name="customers",
        description="Validate status values"
    )
```

### 2. Validate data

```python
import pandas as pd
from dq_framework.validator import DataQualityValidator

df = pd.read_csv("data.csv")  # or build a DataFrame

with DataQualityValidator() as validator:
    result = validator.validate_dataset(
        df=df,
        data_source_name="customers",
        batch_identifier="batch_001",
        save_results=True
    )
    print(f"Validation: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Passed: {result['summary']['passed']}/{result['summary']['total_rules']}")
```

---

## Configuration

By default the framework uses a SQLite file named `dq_framework.db` in the project root.

To use a different path, create a `.env` file in the project root:

```env
DB_PATH=path/to/your/dq_framework.db
```

The database file is created automatically the first time you run `db_init.py` or any code that uses the framework.

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
    --data-source-name "users" \
    --description "Email must not be null"
```

### List rules

```bash
python -m dq_framework.cli list-rules
python -m dq_framework.cli list-rules --active-only
```

### Validate a CSV file

```bash
python -m dq_framework.cli validate \
    --file data.csv \
    --data-source-name "customers" \
    --batch-id "batch_001" \
    --save-results \
    --verbose
```

### Run expectations from data sources

Use `run_expectations.py` with `--data-source-name` to validate from CSV or SQLite (as defined in `config/data_sources.json`):

```bash
# From CSV or SQLite source (by name)
python scripts/run_expectations.py --data-source-name customers_csv --save-results
python scripts/run_expectations.py --data-source-name customers_sqlite --save-results --verbose

```

### Load CSV into SQLite

```bash
python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers
```

---

## Working with the database

The framework uses two SQLite databases:

| Database | Purpose |
|----------|---------|
| `dq_framework.db` | Rules (`data_quality_rules`), validation results (`validation_results`). Override with `DB_PATH` in `.env`. |
| `data_store.db` | Data loaded from CSV via `load_csv_to_sqlite.py`. Used when validating from SQLite sources. |

- **Location:** Both files are in the project root by default. Override `dq_framework.db` with `DB_PATH` in `.env`.
- **Backup:** Copy the `.db` file, or use SQLite’s backup/restore. No separate server to manage.

### Query from Python (SQLAlchemy)

```python
from dq_framework.database import db_manager, DataQualityRule, ValidationResult

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
-- Active rules for a dataset
SELECT * FROM data_quality_rules WHERE data_source_name = 'customers' AND is_active = 1;

-- Recent validation results
SELECT rule_id, success, validation_timestamp FROM validation_results ORDER BY validation_timestamp DESC LIMIT 10;
```

---

## Database schema (reference)

The framework uses two tables.

| Table                   | Purpose |
|-------------------------|--------|
| `data_quality_rules`    | Rule definitions (name, expectation type, kwargs, dataset, etc.) |
| `validation_results`    | One row per validation run (rule_id, success, timestamp, result JSON, etc.) |

Detailed column descriptions, relationships, and example queries are in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

---

## API reference

### RuleManager

```python
from dq_framework.rule_manager import RuleManager

with RuleManager() as rm:
    rule = rm.create_rule(rule_name="...", expectation_type="...", kwargs={...}, data_source_name="...")
    rules = rm.get_rules_by_data_source("customers")
    rule = rm.get_rule_by_name("rule_name")
    rm.update_rule(rule_id, kwargs={...})
    rm.deactivate_rule(rule_id)
    rm.activate_rule(rule_id)
```

### DataQualityValidator

```python
from dq_framework.validator import DataQualityValidator

with DataQualityValidator() as validator:
    result = validator.validate_dataset(df=df, data_source_name="customers")
    result = validator.validate_rule(df=df, rule_id=1)
    history = validator.get_validation_history(data_source_name="customers")
```

---

## Expectation types reference

The framework uses **Great Expectations v1.11.3**. Rules are stored with an `expectation_type` and a `kwargs` object. Below is a reference for each supported expectation type: configuration parameters and example usage.

### Column existence and type

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_to_exist` | Ensure the column exists in the table. |
| `expect_column_values_to_be_in_type_list` | All non-null values must be one of the given pandas/dtype names. |
| `expect_column_values_to_be_of_type` | All non-null values must be of a single type (e.g. `str`, `int`). |

**Configuration and usage**

- **`expect_column_to_exist`**
  - **kwargs:** `column` (str, required) — column name.
  - **Example:** `{"column": "customer_id"}`

- **`expect_column_values_to_be_in_type_list`**
  - **kwargs:** `column` (str), `type_list` (list of str) — e.g. `["int64", "int32", "integer"]`.
  - **Example:** `{"column": "age", "type_list": ["int64", "int32", "integer"]}`

- **`expect_column_values_to_be_of_type`**
  - **kwargs:** `column` (str), `type_` (str) — e.g. `"str"`, `"int"`.
  - **Example:** `{"column": "status", "type_": "str"}`

---

### Null values

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_not_be_null` | No null/NaN values in the column. |
| `expect_column_values_to_be_null` | All values in the column must be null (useful for optional columns that should be empty). |

**Configuration and usage**

- **`expect_column_values_to_not_be_null`**
  - **kwargs:** `column` (str, required).
  - **Example:** `{"column": "email"}`

- **`expect_column_values_to_be_null`**
  - **kwargs:** `column` (str, required).
  - **Example:** `{"column": "optional_notes"}`

---

### Uniqueness

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_be_unique` | All non-null values in the column must be unique. |
| `expect_column_values_to_be_unique_across_table` | Column values must be unique when considered across the table (same as unique for a single column). |

**Configuration and usage**

- **`expect_column_values_to_be_unique`**
  - **kwargs:** `column` (str, required).
  - **Example:** `{"column": "customer_id"}`

- **`expect_column_values_to_be_unique_across_table`**
  - **kwargs:** `column` (str, required).
  - **Example:** `{"column": "email"}`

---

### Set membership

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_be_in_set` | Every non-null value must be in the given set. |
| `expect_column_values_to_not_be_in_set` | No value may be in the given set (e.g. invalid sentinels). |

**Configuration and usage**

- **`expect_column_values_to_be_in_set`**
  - **kwargs:** `column` (str), `value_set` (list) — allowed values. Types must match column (e.g. strings or numbers).
  - **Example:** `{"column": "status", "value_set": ["active", "inactive", "pending"]}`

- **`expect_column_values_to_not_be_in_set`**
  - **kwargs:** `column` (str), `value_set` (list) — disallowed values.
  - **Example:** `{"column": "age", "value_set": [-1, 999, 1000]}`

---

### Range and comparison (per value)

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_be_between` | Each value must be between `min_value` and `max_value` (inclusive by default). |
| `expect_column_values_to_be_in_numeric_range` | Each value must be in the given numeric range. |
| `expect_column_min_to_be_between` | The column’s minimum value must be between two numbers. |
| `expect_column_max_to_be_between` | The column’s maximum value must be between two numbers. |

**Configuration and usage**

- **`expect_column_values_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value` (optional: `strict_min`, `strict_max` booleans).
  - **Example:** `{"column": "age", "min_value": 0, "max_value": 120}`

- **`expect_column_values_to_be_in_numeric_range`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 18, "max_value": 100}`

- **`expect_column_min_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 0, "max_value": 50}`

- **`expect_column_max_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 50, "max_value": 120}`

---

### Statistical (column aggregates)

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_mean_to_be_between` | Column mean must be between two numbers. |
| `expect_column_median_to_be_between` | Column median must be between two numbers. |
| `expect_column_stdev_to_be_between` | Column standard deviation must be between two numbers. |
| `expect_column_quantile_values_to_be_between` | Specified quantiles must fall within given ranges. |

**Configuration and usage**

- **`expect_column_mean_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 30, "max_value": 60}`

- **`expect_column_median_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 30, "max_value": 60}`

- **`expect_column_stdev_to_be_between`**
  - **kwargs:** `column` (str), `min_value`, `max_value`.
  - **Example:** `{"column": "age", "min_value": 10, "max_value": 30}`

- **`expect_column_quantile_values_to_be_between`**
  - **kwargs:** `column` (str), `quantile_ranges` (dict) with:
    - `quantiles`: list of floats (e.g. `[0.25, 0.5, 0.75]`)
    - `value_ranges`: list of `[min, max]` pairs, one per quantile.
  - **Example:** `{"column": "age", "quantile_ranges": {"quantiles": [0.25, 0.5, 0.75], "value_ranges": [[18, 35], [35, 60], [60, 100]]}}`

---

### Pattern matching (regex and LIKE)

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_match_regex` | Each value must match the given regex. |
| `expect_column_values_to_not_match_regex` | No value may match the regex. |
| `expect_column_values_to_match_regex_list` | Each value must match at least one regex in the list. |
| `expect_column_values_to_not_match_regex_list` | No value may match any regex in the list. |
| `expect_column_values_to_match_like_pattern` | Values must match a SQL-like pattern (`%` and `_`). |
| `expect_column_values_to_not_match_like_pattern` | No value may match the LIKE pattern. |

**Configuration and usage**

- **`expect_column_values_to_match_regex`**
  - **kwargs:** `column` (str), `regex` (str). Escape backslashes in JSON (e.g. `\\d`).
  - **Example:** `{"column": "email", "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"}`

- **`expect_column_values_to_not_match_regex`**
  - **kwargs:** `column` (str), `regex` (str).
  - **Example:** `{"column": "status", "regex": "\\\\d"}`  (no digits)

- **`expect_column_values_to_match_regex_list`**
  - **kwargs:** `column` (str), `regex_list` (list of str).
  - **Example:** `{"column": "status", "regex_list": ["^active$", "^inactive$", "^pending$"]}`

- **`expect_column_values_to_not_match_regex_list`**
  - **kwargs:** `column` (str), `regex_list` (list of str).
  - **Example:** `{"column": "email", "regex_list": ["spam@", "invalid@"]}`

- **`expect_column_values_to_match_like_pattern`**
  - **kwargs:** `column` (str), `like_pattern` (str) — use `%` for any string, `_` for one character.
  - **Example:** `{"column": "email", "like_pattern": "%@%.%"}`

- **`expect_column_values_to_not_match_like_pattern`**
  - **kwargs:** `column` (str), `like_pattern` (str).
  - **Example:** `{"column": "email", "like_pattern": "%spam%"}`

---

### Date/time and format

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_match_strftime_format` | Non-null values must be parseable as dates in the given strftime format. |
| `expect_column_values_to_be_dateutil_parseable` | Non-null values must be parseable with dateutil (flexible date strings). |
| `expect_column_values_to_be_json_parseable` | Non-null values must be valid JSON. |

**Configuration and usage**

- **`expect_column_values_to_match_strftime_format`**
  - **kwargs:** `column` (str), `strftime_format` (str) — e.g. `"%Y-%m-%d"`, `"%H:%M:%S"`.
  - **Example:** `{"column": "created_at", "strftime_format": "%Y-%m-%d"}`

- **`expect_column_values_to_be_dateutil_parseable`**
  - **kwargs:** `column` (str).
  - **Example:** `{"column": "created_at"}`

- **`expect_column_values_to_be_json_parseable`**
  - **kwargs:** `column` (str).
  - **Example:** `{"column": "metadata"}`

---

### String length

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_value_lengths_to_be_between` | Length of each value (e.g. string length) must be between min and max. |
| `expect_column_value_lengths_to_equal` | Length of each value must equal a fixed value. |

**Configuration and usage**

- **`expect_column_value_lengths_to_be_between`**
  - **kwargs:** `column` (str), `min_value` (int), `max_value` (int).
  - **Example:** `{"column": "email", "min_value": 10, "max_value": 50}`

- **`expect_column_value_lengths_to_equal`**
  - **kwargs:** `column` (str), `value` (int).
  - **Example:** `{"column": "status", "value": 6}`

---

### Order

| Expectation type | Purpose |
|------------------|--------|
| `expect_column_values_to_be_increasing` | Values must be non-decreasing (allow equal). |
| `expect_column_values_to_be_decreasing` | Values must be non-increasing (allow equal). |

**Configuration and usage**

- **`expect_column_values_to_be_increasing`**
  - **kwargs:** `column` (str).
  - **Example:** `{"column": "customer_id"}`

- **`expect_column_values_to_be_decreasing`**
  - **kwargs:** `column` (str).
  - **Example:** `{"column": "sort_order"}`

---

### Table-level

| Expectation type | Purpose |
|------------------|--------|
| `expect_table_row_count_to_be_between` | Number of rows must be between min and max. |
| `expect_table_row_count_to_equal` | Number of rows must equal a value. |
| `expect_table_column_count_to_be_between` | Number of columns must be between min and max. |
| `expect_table_column_count_to_equal` | Number of columns must equal a value. |
| `expect_table_columns_to_match_ordered_list` | Column names must match the list exactly and in order. |
| `expect_table_columns_to_match_set` | Set of column names must match (order ignored). |
| `expect_compound_columns_to_be_unique` | Combination of listed columns must be unique per row. |

**Configuration and usage**

- **`expect_table_row_count_to_be_between`**
  - **kwargs:** `min_value` (int), `max_value` (int). No `column`.
  - **Example:** `{"min_value": 1, "max_value": 1000000}`

- **`expect_table_row_count_to_equal`**
  - **kwargs:** `value` (int).
  - **Example:** `{"value": 100}`

- **`expect_table_column_count_to_be_between`**
  - **kwargs:** `min_value` (int), `max_value` (int).
  - **Example:** `{"min_value": 3, "max_value": 5}`

- **`expect_table_column_count_to_equal`**
  - **kwargs:** `value` (int).
  - **Example:** `{"value": 4}`

- **`expect_table_columns_to_match_ordered_list`**
  - **kwargs:** `column_list` (list of str) — exact names and order.
  - **Example:** `{"column_list": ["customer_id", "email", "status", "age"]}`

- **`expect_table_columns_to_match_set`**
  - **kwargs:** `column_set` (list of str) — set of names; order does not matter.
  - **Example:** `{"column_set": ["customer_id", "email", "status", "age"]}`

- **`expect_compound_columns_to_be_unique`**
  - **kwargs:** `column_list` (list of str) — columns that together must be unique.
  - **Example:** `{"column_list": ["customer_id", "email"]}`

---

### Creating rules with expectation types

**From code:**

```python
from dq_framework.rule_manager import RuleManager

with RuleManager() as rm:
    rm.create_rule(
        rule_name="email_format",
        expectation_type="expect_column_values_to_match_regex",
        kwargs={"column": "email", "regex": "^[^@]+@[^@]+\\.[^@]+$"},
        data_source_name="users",
        description="Email must match basic email pattern"
    )
```

**From CLI:**

```bash
python -m dq_framework.cli create-rule \
    --rule-name "email_format" \
    --expectation-type "expect_column_values_to_match_regex" \
    --kwargs '{"column": "email", "regex": "^[^@]+@[^@]+\\.[^@]+$"}' \
    --data-source-name "users" \
    --description "Email must match basic email pattern"
```

**From JSON (e.g. for seeding):** Each rule object should have `rule_name`, `expectation_type`, `kwargs`, `data_source_name`, and optionally `column_name` and `description`. See `rules/customers.json` for examples of every type above.

For more details on Great Expectations behavior (e.g. `mostly`, `strict_min`, `strict_max`), see [Great Expectations Documentation](https://docs.greatexpectations.io/).

---

## Project layout

```
dq-ge-poc/
├── config/
│   └── data_sources.json   ← Declare CSV and SQLite sources for run_expectations
├── db_init.py              ← Run this first to create the database and seed data_quality_rules
├── dq_framework/            ← Main package (modular: config, persistence, validation)
│   ├── config.py
│   ├── database.py         ← Models: DataQualityRule, ValidationResult; DatabaseManager
│   ├── repositories/       ← Data access (data_quality_rules, validation_results)
│   │   ├── rule_repository.py
│   │   └── validation_result_repository.py
│   ├── rule_manager.py     ← Rule service (CRUD using RuleRepository)
│   ├── expectation_builder.py
│   ├── validator.py        ← Runs active rules, saves to validation_results
│   └── cli.py
├── examples/
│   ├── basic_usage.py      ← Good first script to run
│   └── advanced_usage.py
├── scripts/
│   ├── init_database.py    ← Alternative to db_init.py (tables only)
│   ├── load_csv_to_sqlite.py  ← Load CSV into data_store.db
│   └── run_expectations.py   ← Run active rules from data_quality_rules (CSV or SQLite via config)
├── requirements.txt
├── setup.py
├── .env.example
├── dq_framework.db         ← Created when you run db_init.py (rules, validation results)
├── data_store.db           ← Created when you run load_csv_to_sqlite.py (loaded data)
├── README.md
└── DATABASE_SCHEMA.md      ← Full schema and query examples
```

---

## Requirements & support

- **Python:** 3.8+
- **Dependencies:** See `requirements.txt` (includes Great Expectations 1.11.3; SQLite is built into Python).

For bugs or questions, open an issue in the repository. For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).
