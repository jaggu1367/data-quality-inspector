"""
Core module: configuration, database models, and connection handling.
"""

from dq_framework.core.config import config, Config, DatabaseConfig, GEConfig
from dq_framework.core.models import Base, DataQualityRule, ValidationResult
from dq_framework.core.database import DatabaseManager, db_manager

__all__ = [
    "config",
    "Config",
    "DatabaseConfig",
    "GEConfig",
    "Base",
    "DataQualityRule",
    "ValidationResult",
    "DatabaseManager",
    "db_manager",
]
