"""
Database models and connection handling for data quality rules and validation results.
Uses SQLite by default. Only data_quality_rules and validation_results are used.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional

from dq_framework.config import config

Base = declarative_base()


class DataQualityRule(Base):
    """Model for storing data quality rules"""
    __tablename__ = "data_quality_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255), nullable=False, unique=True, index=True)
    expectation_type = Column(String(255), nullable=False, index=True)
    kwargs = Column(JSON, nullable=False)  # Store kwargs as JSON
    dataset_name = Column(String(255), nullable=False, index=True)
    column_name = Column(String(255), nullable=True)  # Optional column name
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), nullable=False)
    
    # Relationship to validation results
    validation_results = relationship("ValidationResult", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataQualityRule(id={self.id}, rule_name='{self.rule_name}', expectation_type='{self.expectation_type}')>"


class ValidationResult(Base):
    """Model for storing validation results"""
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("data_quality_rules.id"), nullable=False, index=True)
    validation_timestamp = Column(DateTime, default=lambda: datetime.now(), nullable=False, index=True)
    success = Column(Boolean, nullable=False, index=True)
    result = Column(JSON, nullable=True)  # Store full GE result as JSON
    exception_info = Column(Text, nullable=True)  # Store exception if validation failed
    dataset_name = Column(String(255), nullable=False, index=True)
    batch_identifier = Column(String(255), nullable=True)  # Identifier for the data batch validated
    
    # Relationship to rule
    rule = relationship("DataQualityRule", back_populates="validation_results")
    
    def __repr__(self):
        return f"<ValidationResult(id={self.id}, rule_id={self.rule_id}, success={self.success}, timestamp={self.validation_timestamp})>"


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or config.database.connection_string
        self.engine = create_engine(self.connection_string, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
