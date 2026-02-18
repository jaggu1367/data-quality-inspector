"""
Data source configuration and loading for CSV and SQLite.
"""

import json
import os
from typing import Tuple

import pandas as pd
from sqlalchemy import create_engine


def load_sources_config(config_path: str, root_dir: str) -> dict:
    """Load data sources configuration from JSON file."""
    path = config_path if os.path.isabs(config_path) else os.path.join(root_dir, config_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data sources config not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_data_from_source(
    source_config: dict, root_dir: str
) -> Tuple[pd.DataFrame, str]:
    """
    Load data from a source (csv or sqlite).

    Returns:
        Tuple of (DataFrame, rules_table) - rules_table is used for rule matching.
    """
    source_type = source_config.get("data_source", "csv").lower()
    rules_table = source_config.get("rules_table") or source_config.get(
        "source_id", "dataset"
    )

    if source_type == "csv":
        path = source_config.get("path")
        if not path:
            raise ValueError("CSV source must have 'path'")
        full_path = path if os.path.isabs(path) else os.path.join(root_dir, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        df = pd.read_csv(full_path)
        return df, rules_table

    if source_type == "sqlite":
        database = source_config.get("database")
        source_table = source_config.get("source_table")
        if not database or not source_table:
            raise ValueError("SQLite source must have 'database' and 'source_table'")
        db_path = database if os.path.isabs(database) else os.path.join(root_dir, database)
        conn_str = f"sqlite:///{os.path.normpath(db_path).replace(os.sep, '/')}"
        engine = create_engine(conn_str)
        df = pd.read_sql_table(source_table, engine)
        return df, rules_table

    raise ValueError(
        f"Unknown source type: {source_type}. Expected 'csv' or 'sqlite'."
    )
