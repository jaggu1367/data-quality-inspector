"""
Data Quality Framework based on Great Expectations v1.11.3

Package structure:
  - core: Configuration, database models, connection
  - repositories: Data access layer (rules, validation results)
  - services: Business logic (RuleManager, DataQualityValidator)
  - expectations: Great Expectations integration
  - reports: HTML and email report generation
  - data: Data source configuration and loading
  - seeding: Default rules and seeding logic
"""

__version__ = "0.1.0"

# Backwards-compatible exports
from dq_framework.core import (
    Base,
    Config,
    DataQualityRule,
    DatabaseConfig,
    DatabaseManager,
    GEConfig,
    ValidationResult,
    config,
    db_manager,
)
from dq_framework.services import DataQualityValidator, RuleManager
from dq_framework.expectations import ExpectationBuilder, PandasDataset
from dq_framework.reports import (
    build_html_report,
    load_reports_config,
    maybe_write_html_report,
    send_email_report,
    write_html_report,
)

__all__ = [
    "__version__",
    "Base",
    "Config",
    "DatabaseConfig",
    "DatabaseManager",
    "DataQualityRule",
    "DataQualityValidator",
    "ExpectationBuilder",
    "GEConfig",
    "PandasDataset",
    "RuleManager",
    "ValidationResult",
    "build_html_report",
    "config",
    "db_manager",
    "load_reports_config",
    "maybe_write_html_report",
    "send_email_report",
    "write_html_report",
]
