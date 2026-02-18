"""
Data module: data source configuration and loading.
"""

from dq_framework.data.loaders import (
    load_data_from_source,
    load_sources_config,
)

__all__ = ["load_data_from_source", "load_sources_config"]
