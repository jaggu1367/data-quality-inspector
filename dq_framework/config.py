"""
Configuration management for the Data Quality Framework
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DatabaseConfig(BaseSettings):
    """SQLite database configuration"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    
    # SQLite database file path (defaults to local file)
    database_path: str = Field(default="dq_framework.db")
    
    def __init__(self, **kwargs):
        # Load from environment variables if not provided
        super().__init__(**kwargs)
        self.database_path = os.getenv("DB_PATH", self.database_path)
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string for SQLite"""
        return f"sqlite:///{self.database_path}"


class GEConfig(BaseSettings):
    """Great Expectations configuration"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    
    data_context_root_dir: Optional[str] = Field(default=None)
    expectations_store_name: str = Field(default="expectations_store")
    validations_store_name: str = Field(default="validations_store")
    evaluation_parameter_store_name: str = Field(default="evaluation_parameter_store")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_context_root_dir = os.getenv("GE_DATA_CONTEXT_ROOT_DIR", self.data_context_root_dir)
        self.expectations_store_name = os.getenv("GE_EXPECTATIONS_STORE_NAME", self.expectations_store_name)
        self.validations_store_name = os.getenv("GE_VALIDATIONS_STORE_NAME", self.validations_store_name)
        self.evaluation_parameter_store_name = os.getenv("GE_EVALUATION_PARAMETER_STORE_NAME", self.evaluation_parameter_store_name)


class Config(BaseSettings):
    """Main configuration"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ge: GEConfig = Field(default_factory=GEConfig)


# Global config instance
config = Config()
