"""
Repository for validation_results table. Single responsibility: validation result persistence.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import numpy as np

from dq_framework.core.models import DataQualityRule, ValidationResult


def _sanitize_for_json(obj: Any) -> Any:
    """Convert numpy types and other non-JSON-serializable objects for DB storage."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


class ValidationResultRepository:
    """Data access for validation_results. Used by the validator service."""

    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        rule_id: int,
        success: bool,
        rules_table_name: str,
        result: Optional[Dict[str, Any]] = None,
        exception_info: Optional[str] = None,
        source_id: Optional[str] = None,
        data_source: Optional[str] = None,
        source_table: Optional[str] = None,
        validation_timestamp: Optional[datetime] = None,
    ) -> ValidationResult:
        """Persist a single validation result."""
        sanitized_result = _sanitize_for_json(result) if result is not None else None
        vr = ValidationResult(
            rule_id=rule_id,
            validation_timestamp=validation_timestamp or datetime.now(),
            success=success,
            result=sanitized_result,
            exception_info=exception_info,
            rules_table_name=rules_table_name,
            source_id=source_id,
            data_source=data_source,
            source_table=source_table,
        )
        self._session.add(vr)
        self._session.flush()
        self._session.refresh(vr)
        return vr

    def add_batch(
        self,
        results_by_rule_name: Dict[str, Any],
        rules: List[DataQualityRule],
        rules_table_name: str,
        source_id: Optional[str] = None,
        data_source: Optional[str] = None,
        source_table: Optional[str] = None,
    ) -> None:
        """Persist validation results for multiple rules."""
        for rule in rules:
            result = results_by_rule_name.get(rule.rule_name, {})
            self.add(
                rule_id=rule.id,
                success=result.get("success", False),
                rules_table_name=rules_table_name,
                result=result.get("result"),
                exception_info=result.get("exception_info"),
                source_id=source_id,
                data_source=data_source,
                source_table=source_table,
            )

    def find_history(
        self,
        rule_id: Optional[int] = None,
        rules_table_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """Get validation history, optionally filtered by rule or rules_table."""
        query = self._session.query(ValidationResult)
        if rule_id is not None:
            query = query.filter(ValidationResult.rule_id == rule_id)
        if rules_table_name is not None:
            query = query.filter(ValidationResult.rules_table_name == rules_table_name)
        return query.order_by(ValidationResult.validation_timestamp.desc()).limit(limit).all()
