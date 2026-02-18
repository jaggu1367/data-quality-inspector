"""
Backwards-compatible re-export of configuration.

Prefer: from dq_framework.core import config, Config, DatabaseConfig, GEConfig
"""

from dq_framework.core.config import Config, DatabaseConfig, GEConfig, config

__all__ = ["config", "Config", "DatabaseConfig", "GEConfig"]
