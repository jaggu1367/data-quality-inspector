"""
Rule service: CRUD and query for data quality rules. Uses RuleRepository (data_quality_rules only).
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from dq_framework.database import DataQualityRule, db_manager
from dq_framework.repositories import RuleRepository


class RuleManager:
    """Service for managing data quality rules. All rules live in data_quality_rules table."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session or db_manager.get_session()
        self._own_session = session is None
        self._repo = RuleRepository(self._session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            if exc_type:
                self._session.rollback()
            else:
                self._session.commit()
            self._session.close()

    def create_rule(
        self,
        rule_name: str,
        expectation_type: str,
        kwargs: Dict[str, Any],
        data_source_name: str,
        column_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> DataQualityRule:
        """Create a new data quality rule in data_quality_rules."""
        rule = self._repo.add(
            rule_name=rule_name,
            expectation_type=expectation_type,
            kwargs=kwargs,
            data_source_name=data_source_name,
            column_name=column_name,
            description=description,
            is_active=is_active,
        )
        if self._own_session:
            self._session.commit()
            self._session.refresh(rule)
        return rule

    def get_rule(self, rule_id: int) -> Optional[DataQualityRule]:
        """Get a rule by ID."""
        return self._repo.find_by_id(rule_id)

    def get_rule_by_name(self, rule_name: str) -> Optional[DataQualityRule]:
        """Get a rule by name."""
        return self._repo.find_by_name(rule_name)

    def get_rules_by_data_source(self, data_source_name: str, active_only: bool = True) -> List[DataQualityRule]:
        """Get all rules for a data source. By default only active rules."""
        return self._repo.find_all(data_source_name=data_source_name, active_only=active_only)

    def get_all_rules(self, active_only: bool = True, data_source_name: Optional[str] = None) -> List[DataQualityRule]:
        """Get all rules, optionally only active and/or filtered by data source."""
        return self._repo.find_all(data_source_name=data_source_name, active_only=active_only)

    def update_rule(
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
        """Update an existing rule."""
        rule = self._repo.update(
            rule_id,
            rule_name=rule_name,
            expectation_type=expectation_type,
            kwargs=kwargs,
            data_source_name=data_source_name,
            column_name=column_name,
            description=description,
            is_active=is_active,
        )
        if rule and self._own_session:
            self._session.commit()
            self._session.refresh(rule)
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule."""
        ok = self._repo.delete_by_id(rule_id)
        if ok and self._own_session:
            self._session.commit()
        return ok

    def deactivate_rule(self, rule_id: int) -> Optional[DataQualityRule]:
        """Deactivate a rule (soft delete)."""
        return self.update_rule(rule_id, is_active=False)

    def activate_rule(self, rule_id: int) -> Optional[DataQualityRule]:
        """Activate a rule."""
        return self.update_rule(rule_id, is_active=True)
