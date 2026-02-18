"""
Backwards-compatible re-export of database and models.

Prefer: from dq_framework.core import db_manager, DataQualityRule, ValidationResult, Base
"""

from dq_framework.core import (
    Base,
    DataQualityRule,
    DatabaseManager,
    ValidationResult,
    db_manager,
)

__all__ = [
    "Base",
    "DataQualityRule",
    "ValidationResult",
    "DatabaseManager",
    "db_manager",
]
