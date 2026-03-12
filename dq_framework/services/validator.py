"""
Validation service: runs active data_quality_rules against data and persists to validation_results.

Supports both pandas and PySpark DataFrames.
"""

from typing import Any, Dict, List, Optional, Union

import pandas as pd
from sqlalchemy.orm import Session

from dq_framework.core import db_manager
from dq_framework.core.models import ValidationResult
from dq_framework.expectations import ExpectationBuilder
from dq_framework.repositories import ValidationResultRepository
from dq_framework.services.rule_manager import RuleManager


class DataQualityValidator:
    """Runs all active rules from data_quality_rules against a dataset."""

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
        df: Union[pd.DataFrame, Any],
        data_source_name: str,
        source_id: Optional[str] = None,
        data_source: Optional[str] = None,
        source_table: Optional[str] = None,
        save_results: bool = True,
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a dataset against all active rules for that data source.
        reference_data: Optional dict mapping source_id -> DataFrame for referential
            integrity rules (expect_column_values_to_reference).
        """
        rules = self._rule_manager.get_rules_by_rules_table_name(
            data_source_name, active_only=True
        )  # data_source_name param is the rules_table (e.g. "customers")

        if not rules:
            return {
                "success": True,
                "message": f"No active rules found for data source: {data_source_name}",
                "results": {},
                "summary": {"total_rules": 0, "passed": 0, "failed": 0},
            }

        validation_results = self._expectation_builder.validate_dataframe(
            df, rules, reference_data=reference_data
        )

        if save_results:
            self._result_repo.add_batch(
                results_by_rule_name=validation_results,
                rules=rules,
                rules_table_name=data_source_name,
                source_id=source_id,
                data_source=data_source,
                source_table=source_table,
            )
            if self._own_session:
                self._session.commit()

        passed = sum(1 for r in validation_results.values() if r.get("success", False))
        failed = len(validation_results) - passed

        return {
            "success": failed == 0,
            "rules_table_name": data_source_name,
            "data_source_name": data_source_name,
            "source_id": source_id,
            "data_source": data_source,
            "source_table": source_table,
            "results": validation_results,
            "summary": {
                "total_rules": len(rules),
                "passed": passed,
                "failed": failed,
            },
        }

    def validate_rule(
        self,
        df: Union[pd.DataFrame, Any],
        rule_id: int,
        source_id: Optional[str] = None,
        data_source: Optional[str] = None,
        source_table: Optional[str] = None,
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
                rules_table_name=rule.rules_table_name,
                result=result.get("result"),
                exception_info=result.get("exception_info"),
                source_id=source_id,
                data_source=data_source,
                source_table=source_table,
            )
            if self._own_session:
                self._session.commit()

        return {
            "success": result.get("success", False),
            "rule_id": rule_id,
            "rule_name": rule.rule_name,
            "result": result,
            "source_id": source_id,
            "data_source": data_source,
            "source_table": source_table,
        }

    def get_validation_history(
        self,
        rule_id: Optional[int] = None,
        rules_table_name: Optional[str] = None,
        data_source_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """Get validation history from validation_results table."""
        rules_table = rules_table_name or data_source_name
        return self._result_repo.find_history(
            rule_id=rule_id, rules_table_name=rules_table, limit=limit
        )
