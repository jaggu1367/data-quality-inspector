# Data Quality Framework

> Validate your data with **Great Expectations** (v1.11.3) and store rules in a **SQLite** database—no separate database server needed.

---

## What’s in this repo?

- **Define rules** (e.g. “this column must not be null”, “values must be in this set”) and store them in SQLite.
- **Validate** DataFrames or CSV files against those rules and get pass/fail results.
- **Track history** of every validation (timestamps, batch IDs, full results).
- **Use from code or CLI**—create rules, list them, and run validations from Python or the command line.

**You need:** Python 3.8+ and `pip`. SQLite is included with Python.

---

## Table of contents

- [Get started in 3 steps](#get-started-in-3-steps)
- [Run the examples](#run-the-examples)
- [Quick start in code](#quick-start-in-code)
- [Configuration](#configuration)
- [Command-line interface](#command-line-interface)
- [Working with the database](#working-with-the-database)
- [Database schema (reference)](#database-schema-reference)
- [API reference](#api-reference)
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
| Run all DB rules on sample CSV (100 rows) | `python scripts/run_expectations_on_sample.py --save-results --verbose` |

Make sure you’ve run `python db_init.py` at least once (or the example scripts will create the tables when you run them).

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
        dataset_name="customers",
        description="Ensure customer_id has no null values"
    )
    rm.create_rule(
        rule_name="status_valid",
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={"column": "status", "value_set": ["active", "inactive", "pending"]},
        dataset_name="customers",
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
        dataset_name="customers",
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
    --dataset-name "users" \
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
    --dataset-name "customers" \
    --batch-id "batch_001" \
    --save-results \
    --verbose
```

---

## Working with the database

- **Location:** By default, `dq_framework.db` is in the project root. Override with `DB_PATH` in `.env`.
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
SELECT * FROM data_quality_rules WHERE dataset_name = 'customers' AND is_active = 1;

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
    rule = rm.create_rule(rule_name="...", expectation_type="...", kwargs={...}, dataset_name="...")
    rules = rm.get_rules_by_dataset("customers")
    rule = rm.get_rule_by_name("rule_name")
    rm.update_rule(rule_id, kwargs={...})
    rm.deactivate_rule(rule_id)
    rm.activate_rule(rule_id)
```

### DataQualityValidator

```python
from dq_framework.validator import DataQualityValidator

with DataQualityValidator() as validator:
    result = validator.validate_dataset(df, dataset_name="customers")
    result = validator.validate_rule(df, rule_id=1)
    history = validator.get_validation_history(dataset_name="customers")
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
dq-ge-poc/
├── db_init.py              ← Run this first to create the database and seed data_quality_rules
├── dq_framework/           ← Main package (modular: config, persistence, validation)
│   ├── config.py
│   ├── database.py         ← Models: DataQualityRule, ValidationResult; DatabaseManager
│   ├── repositories/      ← Data access (data_quality_rules, validation_results)
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
│   └── run_expectations_on_sample.py  ← Run active rules from data_quality_rules on a CSV
├── requirements.txt
├── setup.py
├── .env.example
├── dq_framework.db         ← Created when you run db_init.py or the examples
├── README.md
└── DATABASE_SCHEMA.md      ← Full schema and query examples
```

---

## Requirements & support

- **Python:** 3.8+
- **Dependencies:** See `requirements.txt` (includes Great Expectations 1.11.3; SQLite is built into Python).

For bugs or questions, open an issue in the repository. For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).
