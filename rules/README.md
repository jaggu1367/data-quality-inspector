# Rules Directory

This directory contains JSON files that define data quality rules for each dataset.

## Structure

Each dataset should have its own JSON file named `{dataset_name}.json`. For example:
- `customers.json` - Rules for the customers dataset
- `orders.json` - Rules for the orders dataset (if you add one)

## JSON Format

Each JSON file should contain an array of rule objects. Each rule object should have the following structure:

```json
{
  "rule_name": "unique_customer_id",
  "expectation_type": "expect_column_values_to_be_unique",
  "kwargs": {"column": "customer_id"},
  "dataset_name": "customers",
  "column_name": "customer_id",
  "description": "customer_id unique"
}
```

### Required Fields

- `rule_name`: Unique identifier for the rule (must be unique across all datasets)
- `expectation_type`: Great Expectations expectation type (e.g., `expect_column_values_to_be_unique`)
- `kwargs`: Dictionary of parameters for the expectation (e.g., `{"column": "customer_id"}`)
- `dataset_name`: Name of the dataset this rule applies to

### Optional Fields

- `column_name`: Column name (for convenience, extracted from kwargs if not provided)
- `description`: Human-readable description of what the rule validates

## Usage

To seed the database with rules from JSON files:

```bash
python scripts/seed_comprehensive_rules.py
```

This script will:
1. Scan the `rules/` directory for all `*.json` files
2. Load rules from each JSON file
3. Seed the database with all rules (replacing existing rules by default)

## Adding Rules for a New Dataset

1. Create a new JSON file named `{dataset_name}.json` in this directory
2. Add rule objects following the format above
3. Run `python scripts/seed_comprehensive_rules.py` to load the rules

## Example

See `customers.json` for a comprehensive example with 74 rules covering various expectation types.
