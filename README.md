# Data Quality Framework

Check your data against rules—no database server needed. Uses Great Expectations and SQLite.

---

## Contents

- [What is this?](#what-is-this)
- [Get started (3 steps)](#get-started-3-steps)
- [Common commands](#common-commands)
- [Validate your data](#validate-your-data)
  - [Full options example](#full-options-example)
- [Data sources config](#data-sources-config)
- [Use from Python](#use-from-python)
- [Expectation types reference](#expectation-types-reference)
- [CLI commands](#cli-commands)
- [Configuration](#configuration)
- [Project layout](#project-layout)
- [Database details](#database-details)

---

## What is this?

This framework lets you:

1. **Define rules** (e.g. "customer_id must not be null", "status must be active/inactive/pending")
2. **Run checks** on CSV files or SQLite tables
3. **See pass/fail results** and keep a history of every run

Rules are stored in a local SQLite file. You can run checks from the command line or from Python.

---

## Get started (3 steps)

**Requirements:** Python 3.8+ and pip.

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Set up the database

```bash
python db_init.py
```

You should see: "Database tables created successfully." A file `dq_framework.db` will appear in the project folder.

### 3. Run a demo

```bash
python scripts/seed_dq_rules.py
python scripts/run_expectations.py --data-source-name customers_csv --save-results
```

Or use the SQLite source (after loading CSV data):

```bash
python scripts/load_csv_to_sqlite.py --file data/sample_customers_100.csv --table customers
python scripts/seed_dq_rules.py
python scripts/run_expectations.py --data-source-name customers_sqlite --save-results
```

This loads rules from `rules/customers.json` and runs them on the sample data. You'll see pass/fail results for each rule.

---

## Common commands

| Command | What it does |
|---------|--------------|
| `python db_init.py` | Create the database (run once) |
| `python scripts/seed_dq_rules.py` | Load rules from `rules/*.json` into the database |
| `python scripts/run_expectations.py --data-source-name customers_csv --save-results` | Check CSV data source |
| `python scripts/run_expectations.py --data-source-name customers_sqlite --save-results` | Check SQLite data source |
| `python scripts/run_expectations.py --all --save-results` | Check all data sources |
| `python scripts/run_expectations.py --data-source-name customers_sqlite --seed-dq-rules --save-results` | Load rules, then validate SQLite source |
| `python scripts/run_expectations.py --data-source-name customers_csv --send-report` | Run validation and generate reports (email and/or HTML per config) |
| `python scripts/seed_dq_rules.py --data-source-name customers_sqlite` | Load only customers rules (keeps others) |

---

## Validate your data

### Option A: Use the built-in data sources

Data sources are defined in `config/data_sources.json`. To validate:

```bash
# Check one source (customers from CSV)
python scripts/run_expectations.py --data-source-name customers_csv --save-results

# Check one source (customers from SQLite - requires data_store.db with customers table)
python scripts/run_expectations.py --data-source-name customers_sqlite --save-results

# Check all sources
python scripts/run_expectations.py --all --save-results

# Load rules for one source, then validate (single source only)
python scripts/run_expectations.py --data-source-name customers_csv --seed-dq-rules --save-results
python scripts/run_expectations.py --data-source-name customers_sqlite --seed-dq-rules --save-results

# Load all rules, then validate all sources
python scripts/run_expectations.py --all --seed-dq-rules --save-results
```

Load rules from JSON first:

```bash
# Load all rules (customers, orders, products)
python scripts/seed_dq_rules.py

# Or load only rules for one source (e.g. customers)
python scripts/seed_dq_rules.py --data-source-name customers_csv
# or for SQLite source (uses same rules_table "customers")
python scripts/seed_dq_rules.py --data-source-name customers_sqlite
```

### Option B: Load your own CSV

1. Load your CSV into SQLite:

   ```bash
   python scripts/load_csv_to_sqlite.py --file your_file.csv --table your_table
   ```

2. Add a source to `config/data_sources.json` (see format below).

3. Add rules in `rules/your_table.json` (see `rules/customers.json` for examples).

4. Seed and run:

   ```bash
   python scripts/seed_dq_rules.py
   python scripts/run_expectations.py --data-source-name your_source --save-results
   ```

   Or combine: `python scripts/run_expectations.py --data-source-name your_source --seed-dq-rules` loads rules for that source only, then validates.

### Full options example

Run with all available options (useful for scheduled jobs or CI):

```bash
python scripts/run_expectations.py \
  --data-source-name customers_sqlite \
  --seed-dq-rules \
  --save-results \
  --send-report \
  --verbose \
  --batch-id "nightly-2024-01-15" \
  --sources-config config/data_sources.json \
  --reports-config config/dq_report_config.json
```

Or for all sources with full options:

```bash
python scripts/run_expectations.py \
  --all \
  --seed-dq-rules \
  --save-results \
  --send-report \
  --verbose \
  --batch-id "nightly-run" \
  --sources-config config/data_sources.json \
  --reports-config config/dq_report_config.json
```

| Option | Description |
|--------|-------------|
| `--data-source-name`, `-s` | Single source to validate (e.g. `customers_csv`, `customers_sqlite`) |
| `--all`, `-a` | Validate all sources from config |
| `--sources-config` | Path to data sources config (default: `config/data_sources.json`) |
| `--dataset-name` | Override rules_table from config (optional) |
| `--seed-dq-rules` | Load rules from JSON before validation |
| `--batch-id` | Batch identifier for validation_results |
| `--save-results` | Persist results to database |
| `--verbose`, `-v` | Print per-rule details |
| `--send-report` | Generate email and/or HTML reports |
| `--reports-config` | Path to reports config (default: `config/dq_report_config.json`) |

---

## Data sources config

Edit `config/data_sources.json` to declare where your data lives:

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

- **data_source_name**: Unique name for this source.
- **type**: `"csv"` or `"sqlite"`.
- **rules_table**: Which rules file to use (e.g. `"customers"` → `rules/customers.json`).
- **path** (CSV): Path to the CSV file.
- **database** + **table** (SQLite): Database file and table name.

---

## Use from Python

### Create rules

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
```

### Run validation

```python
import pandas as pd
from dq_framework.validator import DataQualityValidator

# From CSV
df = pd.read_csv("data/sample_customers_100.csv")

# Or from SQLite (same structure as customers_sqlite source)
# from sqlalchemy import create_engine
# engine = create_engine("sqlite:///data_store.db")
# df = pd.read_sql_table("customers", engine)

with DataQualityValidator() as validator:
    result = validator.validate_dataset(
        df=df,
        data_source_name="customers",
        save_results=True
    )
    print(f"Passed: {result['summary']['passed']}/{result['summary']['total_rules']}")
    print(f"Overall: {'PASSED' if result['success'] else 'FAILED'}")
```

---

## Configuration

- **Database:** Uses `dq_framework.db` in the project root by default.
- **Custom path:** Create a `.env` file with `DB_PATH=path/to/your.db`.

### Reports (Email and HTML)

Use `--send-report` when running expectations to generate reports. Both report types use the same two-layer content:
- **Layer 1:** Input data source details (name, type, path/table, row count, columns, timestamp)
- **Layer 2:** Data quality report (overall status, passed/failed counts, per-rule results)

Configure in `config/dq_report_config.json`:

```json
{
  "email": {
    "enabled": false,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "username": "",
    "password": "",
    "from_address": "",
    "to_addresses": [],
    "subject": "Data Quality Report: {data_source_name}"
  },
  "html": {
    "enabled": true,
    "output_dir": "html_reports"
  }
}
```

- **Email:** Set `email.enabled` to `true` and configure SMTP when you have credentials. When disabled or `to_addresses` is empty, no email is sent.
- **HTML:** Set `html.enabled` to `true` to write reports to `output_dir` (relative to project root or absolute). Files are named `{data_source_name}_{timestamp}.html`.

Use `--reports-config` to point to a custom config path.

---

## Project layout

```
├── config/data_sources.json   Data source definitions
├── config/dq_report_config.json   Report config (email, HTML)
├── db_init.py                 One-time setup (creates database)
├── dq_framework/              Main package
├── rules/                     JSON rule files (customers.json, etc.)
├── scripts/
│   ├── load_csv_to_sqlite.py  Load CSV into data_store.db
│   ├── run_expectations.py    Run checks on data
│   └── seed_dq_rules.py      Load rules from JSON into database
├── dq_framework.db            Rules and validation history (created on first run)
├── data_store.db              Loaded CSV data (created by load_csv_to_sqlite)
└── html_reports/              HTML reports (when html.enabled in dq_report_config)
```

---

## Expectation types reference

Rules use an `expectation_type` (Great Expectations) and `kwargs` (parameters). Each rule in `rules/*.json` or created via code has this structure:

```json
{
  "rule_name": "unique_customer_id",
  "expectation_type": "expect_column_values_to_be_unique",
  "kwargs": {"column": "customer_id"},
  "data_source_name": "customers",
  "description": "customer_id unique"
}
```

Below is the full list of supported expectation types with kwargs and examples.

### Column existence and type

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_to_exist` | Column must exist | `column` (str) | `{"column": "customer_id"}` |
| `expect_column_values_to_be_in_type_list` | Values must be one of the given dtypes | `column`, `type_list` (e.g. `["int64","int32","integer"]`) | `{"column": "age", "type_list": ["int64", "int32", "integer"]}` |
| `expect_column_values_to_be_of_type` | Values must be a single type | `column`, `type_` (e.g. `"str"`, `"int"`) | `{"column": "status", "type_": "str"}` |

### Null values

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_not_be_null` | No null/NaN values | `column` | `{"column": "email"}` |
| `expect_column_values_to_be_null` | All values must be null (for optional empty columns) | `column` | `{"column": "notes"}` |

### Uniqueness

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_be_unique` | All non-null values unique | `column` | `{"column": "customer_id"}` |
| `expect_column_values_to_be_unique_across_table` | Column unique across table | `column` | `{"column": "email"}` |

### Set membership

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_be_in_set` | Every value must be in the set | `column`, `value_set` | `{"column": "status", "value_set": ["active", "inactive", "pending"]}` |
| `expect_column_values_to_not_be_in_set` | No value may be in the set | `column`, `value_set` | `{"column": "status", "value_set": ["invalid", "deleted"]}` |

### Range and comparison (per value)

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_be_between` | Each value between min and max | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 0, "max_value": 120}` |
| `expect_column_values_to_be_in_numeric_range` | Each value in numeric range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 18, "max_value": 100}` |
| `expect_column_min_to_be_between` | Column's min value in range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 0, "max_value": 50}` |
| `expect_column_max_to_be_between` | Column's max value in range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 50, "max_value": 120}` |

### Statistical (column aggregates)

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_mean_to_be_between` | Column mean in range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 30, "max_value": 60}` |
| `expect_column_median_to_be_between` | Column median in range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 30, "max_value": 60}` |
| `expect_column_stdev_to_be_between` | Column std dev in range | `column`, `min_value`, `max_value` | `{"column": "age", "min_value": 10, "max_value": 30}` |
| `expect_column_quantile_values_to_be_between` | Quantiles in given ranges | `column`, `quantile_ranges` | `{"column": "age", "quantile_ranges": {"quantiles": [0.25, 0.5, 0.75], "value_ranges": [[18, 35], [35, 60], [60, 100]]}}` |

### Pattern matching (regex and LIKE)

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_match_regex` | Each value matches regex | `column`, `regex` | `{"column": "email", "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}` |
| `expect_column_values_to_not_match_regex` | No value matches regex | `column`, `regex` | `{"column": "status", "regex": "\\d"}` (no digits) |
| `expect_column_values_to_match_regex_list` | Each value matches at least one regex | `column`, `regex_list` | `{"column": "status", "regex_list": ["^active$", "^inactive$", "^pending$"]}` |
| `expect_column_values_to_not_match_regex_list` | No value matches any regex | `column`, `regex_list` | `{"column": "email", "regex_list": ["spam@", "invalid@"]}` |
| `expect_column_values_to_match_like_pattern` | Values match SQL-like pattern (`%`, `_`) | `column`, `like_pattern` | `{"column": "email", "like_pattern": "%@%.%"}` |
| `expect_column_values_to_not_match_like_pattern` | No value matches LIKE pattern | `column`, `like_pattern` | `{"column": "email", "like_pattern": "%spam%"}` |

### Date/time and format

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_match_strftime_format` | Values parseable as dates in given format | `column`, `strftime_format` | `{"column": "created_at", "strftime_format": "%Y-%m-%d"}` |
| `expect_column_values_to_be_dateutil_parseable` | Values parseable with dateutil | `column` | `{"column": "created_at"}` |
| `expect_column_values_to_be_json_parseable` | Values are valid JSON | `column` | `{"column": "metadata"}` |

### String length

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_value_lengths_to_be_between` | Length of each value in range | `column`, `min_value`, `max_value` | `{"column": "email", "min_value": 10, "max_value": 50}` |
| `expect_column_value_lengths_to_equal` | Length of each value equals value | `column`, `value` | `{"column": "status", "value": 6}` |

### Order

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_column_values_to_be_increasing` | Values non-decreasing | `column` | `{"column": "customer_id"}` |
| `expect_column_values_to_be_decreasing` | Values non-increasing | `column` | `{"column": "sort_order"}` |

### Table-level

| Expectation type | Purpose | kwargs | Example |
|------------------|---------|--------|---------|
| `expect_table_row_count_to_be_between` | Row count in range | `min_value`, `max_value` | `{"min_value": 1, "max_value": 1000000}` |
| `expect_table_row_count_to_equal` | Row count equals value | `value` | `{"value": 100}` |
| `expect_table_column_count_to_be_between` | Column count in range | `min_value`, `max_value` | `{"min_value": 1, "max_value": 20}` |
| `expect_table_column_count_to_equal` | Column count equals value | `value` | `{"value": 4}` |
| `expect_table_columns_to_match_ordered_list` | Column names match list (order matters) | `column_list` | `{"column_list": ["customer_id", "email", "status", "age"]}` |
| `expect_table_columns_to_match_set` | Column names match set (order ignored) | `column_set` | `{"column_set": ["customer_id", "email", "status", "age"]}` |
| `expect_compound_columns_to_be_unique` | Combination of columns unique per row | `column_list` | `{"column_list": ["customer_id", "email"]}` |

### Creating rules

**From code:**
```python
from dq_framework.rule_manager import RuleManager
with RuleManager() as rm:
    rm.create_rule(
        rule_name="email_format",
        expectation_type="expect_column_values_to_match_regex",
        kwargs={"column": "email", "regex": "^[^@]+@[^@]+\\.[^@]+$"},
        data_source_name="users",
        description="Email format"
    )
```

**From JSON:** Add objects to `rules/your_table.json`. See `rules/customers.json` for examples of every type above.

For more Great Expectations options (e.g. `mostly`, `strict_min`), see [Great Expectations docs](https://docs.greatexpectations.io/).

---

## CLI commands

```bash
# Create database
python -m dq_framework.cli init-db

# Create a rule
python -m dq_framework.cli create-rule \
  --rule-name "email_not_null" \
  --expectation-type "expect_column_values_to_not_be_null" \
  --kwargs '{"column": "email"}' \
  --data-source-name "users"

# List rules
python -m dq_framework.cli list-rules

# Validate a CSV file
python -m dq_framework.cli validate --file data/sample_customers_100.csv --data-source-name customers --save-results
```

---

## Database details

- **dq_framework.db**: Stores rules and validation results. Use [DB Browser for SQLite](https://sqlitebrowser.org/) or any SQLite GUI to inspect.
- **data_store.db**: Stores data loaded from CSV via `load_csv_to_sqlite.py`.
- **Schema:** See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for table definitions.

---

## Requirements

- Python 3.8+
- Dependencies in `requirements.txt` (includes Great Expectations 1.11.3)
- SQLite (included with Python)

For bugs or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).
