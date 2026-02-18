# Database Schema Documentation

## Overview

The Data Quality Framework uses SQLite as its database backend. The database file (`dq_framework.db`) is created automatically in the project root when you first run the application.

**Tables used:** `data_quality_rules` (active rules to run) and `validation_results` (audit trail of runs).

## Database File

- **Default Location**: `dq_framework.db` (project root)
- **Customizable**: Set `DB_PATH` environment variable to change location
- **Format**: SQLite 3 database file
- **Backup**: Simply copy the `.db` file to backup

## Tables

### 1. `data_quality_rules`

Stores the active rules used for validation. The framework runs all active rules from this table (e.g. when running `scripts/run_expectations.py` or `DataQualityValidator.validate_dataset()`).

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `rule_name` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Human-readable rule name (e.g., "customer_id_not_null") |
| `expectation_type` | VARCHAR(255) | NOT NULL, INDEXED | Great Expectations expectation type |
| `kwargs` | JSON/TEXT | NOT NULL | JSON object with expectation parameters |
| `rules_table_name` | VARCHAR(255) | NOT NULL, INDEXED | Rules table (e.g. customers) this rule applies to |
| `column_name` | VARCHAR(255) | NULLABLE | Optional column name (for convenience) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether rule is active |
| `description` | TEXT | NULLABLE | Human-readable description |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last update timestamp |

#### Example Query

```sql
-- Get all active rules for a dataset
SELECT rule_name, expectation_type, kwargs 
FROM data_quality_rules 
WHERE rules_table_name = 'customers' AND is_active = 1;
```

### 2. `validation_results`

Stores results of each validation execution, creating an audit trail. Columns are ordered for readability: identity → when → context (source) → rule → outcome.

#### Columns (in table order)

| # | Column | Type | Constraints | Description |
|---|--------|------|-------------|-------------|
| 1 | `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| 2 | `validation_timestamp` | DATETIME | NOT NULL, INDEXED | When validation executed |
| 3 | `source_id` | VARCHAR(255) | NULLABLE, INDEXED | Source ID from config (e.g. customers_sqlite) |
| 4 | `data_source` | VARCHAR(255) | NULLABLE | Source type: "csv" or "sqlite" |
| 5 | `source_table` | VARCHAR(255) | NULLABLE | Table name for SQLite; null for CSV |
| 6 | `rules_table_name` | VARCHAR(255) | NOT NULL, INDEXED | Rules table (e.g. customers) that was validated |
| 7 | `rule_id` | INTEGER | NOT NULL, FOREIGN KEY, INDEXED | References `data_quality_rules.id` |
| 8 | `success` | BOOLEAN | NOT NULL, INDEXED | Pass (True) or fail (False) |
| 9 | `result` | JSON/TEXT | NULLABLE | Complete GE result object as JSON |
| 10 | `exception_info` | TEXT | NULLABLE | Error message if exception occurred |

#### Example Query

```sql
-- Get recent validation failures
SELECT r.rule_name, v.validation_timestamp, v.exception_info
FROM validation_results v
JOIN data_quality_rules r ON v.rule_id = r.id
WHERE v.success = 0
ORDER BY v.validation_timestamp DESC
LIMIT 10;
```

## Relationships

- **One-to-Many**: One `data_quality_rules` record can have many `validation_results` records
- **Foreign Key**: `validation_results.rule_id` → `data_quality_rules.id`

## Indexes

Automatically created indexes for performance:

- `data_quality_rules.rule_name` (UNIQUE)
- `data_quality_rules.expectation_type`
- `data_quality_rules.rules_table_name`
- `validation_results.rule_id`
- `validation_results.validation_timestamp`
- `validation_results.success`
- `validation_results.rules_table_name`
- `validation_results.source_id`

## Common Operations

### View All Tables

```sql
SELECT name FROM sqlite_master WHERE type='table';
```

### View Table Schema

```sql
.schema data_quality_rules
.schema validation_results
```

### Count Records

```sql
SELECT COUNT(*) FROM data_quality_rules;
SELECT COUNT(*) FROM validation_results;
```

### Get Validation Statistics

```sql
SELECT 
    r.rule_name,
    COUNT(v.id) as total_validations,
    SUM(CASE WHEN v.success = 1 THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN v.success = 0 THEN 1 ELSE 0 END) as failed
FROM data_quality_rules r
LEFT JOIN validation_results v ON r.id = v.rule_id
WHERE r.is_active = 1
GROUP BY r.id, r.rule_name;
```
