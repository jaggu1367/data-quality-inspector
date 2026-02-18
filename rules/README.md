# Rules Directory

This directory contains JSON files that define data quality rules for each dataset.

Rules are matched by `rules_table`. Both CSV and SQLite sources share the same rules when they use the same `rules_table` (e.g. `customers_csv` and `customers_sqlite` both use `customers.json`).

## Structure

Each dataset should have its own JSON file named `{rules_table}.json`. The `rules_table` comes from `config/data_sources.json`—each source declares a `rules_table` that maps to the rules file.

| data_sources.json (source_id, rules_table) | rules/ |
|-------------------------------------------|--------|
| `customers_csv` (rules_table: customers) | `customers.json` |
| `customers_sqlite` (rules_table: customers) | `customers.json` |

Examples:
- `customers.json` - Rules for the customers dataset (used by both customers_csv and customers_sqlite)
- `orders.json` - Rules for the orders dataset (if you add a source with rules_table "orders")

## JSON Format

Each JSON file should contain an array of rule objects. Each rule object should have the following structure:

```json
{
  "rule_name": "unique_customer_id",
  "expectation_type": "expect_column_values_to_be_unique",
  "kwargs": {"column": "customer_id"},
  "rules_table_name": "customers",
  "column_name": "customer_id",
  "description": "customer_id unique"
}
```

### Required Fields

- `rule_name`: Unique identifier for the rule (must be unique across all datasets)
- `expectation_type`: Great Expectations expectation type (e.g., `expect_column_values_to_be_unique`)
- `kwargs`: Dictionary of parameters for the expectation (e.g., `{"column": "customer_id"}`)
- `rules_table_name`: Rules table (e.g. customers) this rule applies to

### Optional Fields

- `column_name`: Column name (for convenience, extracted from kwargs if not provided)
- `description`: Human-readable description of what the rule validates

## Usage

To seed the database with rules from JSON files:

```bash
python scripts/seed_dq_rules.py
```

This script will:
1. Scan the `rules/` directory for all `*.json` files
2. Load rules from each JSON file
3. Seed the database with all rules (replacing existing rules by default)

## Adding Rules for a New Dataset

1. Add a source with `rules_table` (and for SQLite: `database` + `source_table`) in `config/data_sources.json`
2. Create `rules/{rules_table}.json` (e.g. copy from `customers.json` as a template)
3. Edit the rules file to match your dataset schema
4. Run `python scripts/seed_dq_rules.py` to load the rules into the database

## Example

See `customers.json` for a full example with rules covering various expectation types.
