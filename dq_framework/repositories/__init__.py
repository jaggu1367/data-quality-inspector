"""
Data access layer: repositories for data_quality_rules and validation_results.
"""

from dq_framework.repositories.rule_repository import RuleRepository
from dq_framework.repositories.validation_result_repository import ValidationResultRepository

__all__ = ["RuleRepository", "ValidationResultRepository"]
