"""
Repository for data_quality_rules table. Single responsibility: rule persistence.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from dq_framework.core.models import DataQualityRule


class RuleRepository:
    """Data access for data_quality_rules. Used by rule service and validator."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, rule_id: int) -> Optional[DataQualityRule]:
        """Get a rule by primary key."""
        return self._session.query(DataQualityRule).filter(DataQualityRule.id == rule_id).first()

    def find_by_name(self, rule_name: str) -> Optional[DataQualityRule]:
        """Get a rule by unique rule_name."""
        return self._session.query(DataQualityRule).filter(DataQualityRule.rule_name == rule_name).first()

    def find_active_by_data_source(self, data_source_name: str) -> List[DataQualityRule]:
        """Get all active rules for a data source."""
        return (
            self._session.query(DataQualityRule)
            .filter(
                DataQualityRule.data_source_name == data_source_name,
                DataQualityRule.is_active == True,
            )
            .all()
        )

    def find_all_active(self, data_source_name: Optional[str] = None) -> List[DataQualityRule]:
        """Get all active rules, optionally filtered by data source."""
        query = self._session.query(DataQualityRule).filter(DataQualityRule.is_active == True)
        if data_source_name is not None:
            query = query.filter(DataQualityRule.data_source_name == data_source_name)
        return query.all()

    def find_all(self, data_source_name: Optional[str] = None, active_only: bool = False) -> List[DataQualityRule]:
        """Get all rules, optionally filtered by data source and active status."""
        query = self._session.query(DataQualityRule)
        if active_only:
            query = query.filter(DataQualityRule.is_active == True)
        if data_source_name is not None:
            query = query.filter(DataQualityRule.data_source_name == data_source_name)
        return query.all()

    def add(
        self,
        rule_name: str,
        expectation_type: str,
        kwargs: Dict[str, Any],
        data_source_name: str,
        column_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> DataQualityRule:
        """Persist a new rule and return it."""
        rule = DataQualityRule(
            rule_name=rule_name,
            expectation_type=expectation_type,
            kwargs=kwargs,
            data_source_name=data_source_name,
            column_name=column_name,
            description=description,
            is_active=is_active,
        )
        self._session.add(rule)
        self._session.flush()
        self._session.refresh(rule)
        return rule

    def update(
        self,
        rule_id: int,
        rule_name: Optional[str] = None,
        expectation_type: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        data_source_name: Optional[str] = None,
        column_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[DataQualityRule]:
        """Update an existing rule. Returns updated rule or None if not found."""
        rule = self.find_by_id(rule_id)
        if not rule:
            return None
        if rule_name is not None:
            rule.rule_name = rule_name
        if expectation_type is not None:
            rule.expectation_type = expectation_type
        if kwargs is not None:
            rule.kwargs = kwargs
        if data_source_name is not None:
            rule.data_source_name = data_source_name
        if column_name is not None:
            rule.column_name = column_name
        if description is not None:
            rule.description = description
        if is_active is not None:
            rule.is_active = is_active
        self._session.flush()
        self._session.refresh(rule)
        return rule

    def delete_by_id(self, rule_id: int) -> bool:
        """Delete a rule by id. Returns True if deleted."""
        rule = self.find_by_id(rule_id)
        if not rule:
            return False
        self._session.delete(rule)
        self._session.flush()
        return True
