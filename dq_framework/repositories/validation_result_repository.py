"""
Repository for validation_results table. Single responsibility: validation result persistence.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from dq_framework.database import DataQualityRule, ValidationResult


class ValidationResultRepository:
    """Data access for validation_results. Used by the validator service."""

    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        rule_id: int,
        success: bool,
        dataset_name: str,
        result: Optional[Dict[str, Any]] = None,
        exception_info: Optional[str] = None,
        batch_identifier: Optional[str] = None,
        validation_timestamp: Optional[datetime] = None,
    ) -> ValidationResult:
        """Persist a single validation result."""
        vr = ValidationResult(
            rule_id=rule_id,
            validation_timestamp=validation_timestamp or datetime.now(),
            success=success,
            result=result,
            exception_info=exception_info,
            dataset_name=dataset_name,
            batch_identifier=batch_identifier,
        )
        self._session.add(vr)
        self._session.flush()
        self._session.refresh(vr)
        return vr

    def add_batch(
        self,
        results_by_rule_name: Dict[str, Any],
        rules: List[DataQualityRule],
        dataset_name: str,
        batch_identifier: Optional[str] = None,
    ) -> None:
        """Persist validation results for multiple rules."""
        for rule in rules:
            result = results_by_rule_name.get(rule.rule_name, {})
            self.add(
                rule_id=rule.id,
                success=result.get("success", False),
                dataset_name=dataset_name,
                result=result.get("result"),
                exception_info=result.get("exception_info"),
                batch_identifier=batch_identifier,
            )

    def find_history(
        self,
        rule_id: Optional[int] = None,
        dataset_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """Get validation history, optionally filtered by rule or dataset."""
        query = self._session.query(ValidationResult)
        if rule_id is not None:
            query = query.filter(ValidationResult.rule_id == rule_id)
        if dataset_name is not None:
            query = query.filter(ValidationResult.dataset_name == dataset_name)
        return query.order_by(ValidationResult.validation_timestamp.desc()).limit(limit).all()
