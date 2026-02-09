"""
Validation service: runs active data_quality_rules against data and persists to validation_results.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from dq_framework.database import DataQualityRule, ValidationResult, db_manager
from dq_framework.rule_manager import RuleManager
from dq_framework.expectation_builder import ExpectationBuilder
from dq_framework.repositories import ValidationResultRepository


class DataQualityValidator:
    """Runs all active rules from data_quality_rules against a dataset and saves results to validation_results."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session or db_manager.get_session()
        self._own_session = session is None
        self._rule_manager = RuleManager(session=self._session)
        self._result_repo = ValidationResultRepository(self._session)
        self._expectation_builder = ExpectationBuilder()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            if exc_type:
                self._session.rollback()
            else:
                self._session.commit()
            self._session.close()

    def validate_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        batch_identifier: Optional[str] = None,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a dataset against all active rules for that dataset (from data_quality_rules).

        Args:
            df: pandas DataFrame to validate
            dataset_name: Name of the dataset (must match rule dataset_name)
            batch_identifier: Optional identifier for this batch
            save_results: Whether to save to validation_results table

        Returns:
            Dictionary with success, results, and summary (total_rules, passed, failed).
        """
        rules = self._rule_manager.get_rules_by_dataset(dataset_name, active_only=True)

        if not rules:
            return {
                "success": True,
                "message": f"No active rules found for dataset: {dataset_name}",
                "results": {},
                "summary": {"total_rules": 0, "passed": 0, "failed": 0},
            }

        validation_results = self._expectation_builder.validate_dataframe(df, rules)

        if save_results:
            self._result_repo.add_batch(
                results_by_rule_name=validation_results,
                rules=rules,
                dataset_name=dataset_name,
                batch_identifier=batch_identifier,
            )
            if self._own_session:
                self._session.commit()

        passed = sum(1 for r in validation_results.values() if r.get("success", False))
        failed = len(validation_results) - passed

        return {
            "success": failed == 0,
            "dataset_name": dataset_name,
            "batch_identifier": batch_identifier,
            "results": validation_results,
            "summary": {
                "total_rules": len(rules),
                "passed": passed,
                "failed": failed,
            },
        }

    def validate_rule(
        self,
        df: pd.DataFrame,
        rule_id: int,
        batch_identifier: Optional[str] = None,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """Validate a dataset against a single rule by id."""
        rule = self._rule_manager.get_rule(rule_id)
        if not rule:
            return {"success": False, "error": f"Rule with ID {rule_id} not found"}
        if not rule.is_active:
            return {"success": False, "error": f"Rule {rule.rule_name} is not active"}

        validation_results = self._expectation_builder.validate_dataframe(df, [rule])
        result = validation_results.get(rule.rule_name, {})

        if save_results:
            self._result_repo.add(
                rule_id=rule.id,
                success=result.get("success", False),
                dataset_name=rule.dataset_name,
                result=result.get("result"),
                exception_info=result.get("exception_info"),
                batch_identifier=batch_identifier,
            )
            if self._own_session:
                self._session.commit()

        return {
            "success": result.get("success", False),
            "rule_id": rule_id,
            "rule_name": rule.rule_name,
            "result": result,
            "batch_identifier": batch_identifier,
        }

    def get_validation_history(
        self,
        rule_id: Optional[int] = None,
        dataset_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """Get validation history from validation_results table."""
        return self._result_repo.find_history(rule_id=rule_id, dataset_name=dataset_name, limit=limit)
