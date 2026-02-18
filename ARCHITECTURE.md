# Data Quality Framework - Architecture

## Package Structure

The framework is organized into modular Python packages with clear separation of concerns:

```
dq_framework/
├── core/                 # Configuration, models, database
│   ├── config.py         # Pydantic settings (database, GE)
│   ├── models.py         # SQLAlchemy ORM (DataQualityRule, ValidationResult)
│   └── database.py       # DatabaseManager, connection handling
│
├── repositories/         # Data access layer
│   ├── rule_repository.py
│   └── validation_result_repository.py
│
├── services/             # Business logic
│   ├── rule_manager.py   # CRUD for rules
│   └── validator.py      # Validation orchestration
│
├── expectations/         # Great Expectations integration
│   └── expectation_builder.py
│
├── reports/              # Report generation
│   ├── config.py         # Shared reports config loading
│   ├── email_report.py
│   └── html_report.py
│
├── data/                  # Data source loading
│   └── loaders.py        # CSV/SQLite source config and loading
│
├── seeding/               # Default rules and seeding
│   └── default_rules.py
│
├── cli.py                 # Command-line interface
└── [backwards-compat]      # Re-exports (database.py, config.py, etc.)
```

## Design Principles

- **Single Responsibility**: Each module has a focused purpose
- **Dependency Inversion**: Services depend on abstractions (repositories), not implementations
- **Backwards Compatibility**: Existing imports (`from dq_framework.database import db_manager`) still work via re-exports

## Usage Examples

```python
# Preferred imports (new structure)
from dq_framework.core import db_manager, DataQualityRule, config
from dq_framework.services import DataQualityValidator, RuleManager
from dq_framework.reports import maybe_write_html_report, send_email_report
from dq_framework.data import load_sources_config, load_data_from_source
from dq_framework.seeding import seed_data_quality_rules_if_empty

# Legacy imports (still supported)
from dq_framework.database import db_manager
from dq_framework.validator import DataQualityValidator
```

## Scripts

- `db_init.py` - Initialize DB and seed default rules
- `scripts/run_expectations.py` - Run validations against configured sources
- `scripts/seed_dq_rules.py` - Seed rules from JSON files
- `scripts/init_database.py` - Create tables only
- `scripts/load_csv_to_sqlite.py` - Load CSV into SQLite

## Entry Points

After `pip install -e .`:
- `dq init-db` - Initialize database
- `dq create-rule` - Create a rule
- `dq list-rules` - List rules
- `dq validate` - Validate a CSV file
