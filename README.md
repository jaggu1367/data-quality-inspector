# Data Quality Framework

Check your data against rules—no database server needed. Uses Great Expectations and SQLite.

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

This loads rules from `rules/customers.json` and runs them on the sample data. You'll see pass/fail results for each rule.

---

## Common commands

| Command | What it does |
|---------|--------------|
| `python db_init.py` | Create the database (run once) |
| `python scripts/seed_dq_rules.py` | Load rules from `rules/*.json` into the database |
| `python scripts/run_expectations.py --data-source-name customers_csv --save-results` | Check data from a CSV source |
| `python scripts/run_expectations.py --all --save-results` | Check all data sources in config |

---

## Validate your data

### Option A: Use the built-in data sources

Data sources are defined in `config/data_sources.json`. To validate:

```bash
# Check one source (e.g. customers from CSV)
python scripts/run_expectations.py --data-source-name customers_csv --save-results

# Check all sources
python scripts/run_expectations.py --all --save-results
```

Load rules from JSON first:

```bash
python scripts/seed_dq_rules.py
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

df = pd.read_csv("data.csv")  # or any DataFrame

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

---

## Project layout

```
├── config/data_sources.json   Data source definitions
├── db_init.py                 One-time setup (creates database)
├── dq_framework/              Main package
├── rules/                     JSON rule files (customers.json, etc.)
├── scripts/
│   ├── load_csv_to_sqlite.py  Load CSV into data_store.db
│   ├── run_expectations.py    Run checks on data
│   └── seed_dq_rules.py      Load rules from JSON into database
├── dq_framework.db            Rules and validation history (created on first run)
└── data_store.db              Loaded CSV data (created by load_csv_to_sqlite)
```

---

## Rule types (quick reference)

Rules are defined with an `expectation_type` and `kwargs`. Examples:

| What you want to check | expectation_type | kwargs |
|------------------------|------------------|--------|
| Column exists | `expect_column_to_exist` | `{"column": "customer_id"}` |
| No nulls | `expect_column_values_to_not_be_null` | `{"column": "email"}` |
| Values in set | `expect_column_values_to_be_in_set` | `{"column": "status", "value_set": ["active", "inactive"]}` |
| Values in range | `expect_column_values_to_be_between` | `{"column": "age", "min_value": 0, "max_value": 120}` |
| Unique values | `expect_column_values_to_be_unique` | `{"column": "customer_id"}` |
| Regex pattern | `expect_column_values_to_match_regex` | `{"column": "email", "regex": "^.+@.+\\..+$"}` |
| Row count | `expect_table_row_count_to_be_between` | `{"min_value": 1, "max_value": 1000000}` |

See `rules/customers.json` for more examples. Full reference: [Expectation types](https://docs.greatexpectations.io/).

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
python -m dq_framework.cli validate --file data.csv --data-source-name customers --save-results
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
