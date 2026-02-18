"""
Database models for data quality rules and validation results.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DataQualityRule(Base):
    """Model for storing data quality rules."""

    __tablename__ = "data_quality_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255), nullable=False, unique=True, index=True)
    expectation_type = Column(String(255), nullable=False, index=True)
    kwargs = Column(JSON, nullable=False)
    rules_table_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), nullable=False
    )

    validation_results = relationship(
        "ValidationResult", back_populates="rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<DataQualityRule(id={self.id}, rule_name='{self.rule_name}', "
            f"expectation_type='{self.expectation_type}')>"
        )


class ValidationResult(Base):
    """Model for storing validation results.

    Column order (audit → context → rule → outcome):
      id, validation_timestamp, source_id, data_source, source_table,
      rules_table_name, rule_id, success, result, exception_info
    """

    __tablename__ = "validation_results"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    # When (audit)
    validation_timestamp = Column(
        DateTime, default=lambda: datetime.now(), nullable=False, index=True
    )
    # Context: what was validated
    source_id = Column(String(255), nullable=True, index=True)
    data_source = Column(String(255), nullable=True)  # "csv" or "sqlite"
    source_table = Column(String(255), nullable=True)  # table name for sqlite, null for csv
    rules_table_name = Column(String(255), nullable=False, index=True)
    # Rule reference
    rule_id = Column(Integer, ForeignKey("data_quality_rules.id"), nullable=False, index=True)
    # Outcome
    success = Column(Boolean, nullable=False, index=True)
    result = Column(JSON, nullable=True)
    exception_info = Column(Text, nullable=True)

    rule = relationship("DataQualityRule", back_populates="validation_results")

    def __repr__(self) -> str:
        return (
            f"<ValidationResult(id={self.id}, rule_id={self.rule_id}, "
            f"success={self.success}, timestamp={self.validation_timestamp})>"
        )
