"""
Data source configuration and loading for CSV, SQLite, and Hive.

Supports both pandas (default) and PySpark engines.
"""

import json
import os
from typing import TYPE_CHECKING, Tuple, Union

import pandas as pd

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame
from sqlalchemy import create_engine


def load_sources_config(config_path: str, root_dir: str) -> dict:
    """Load data sources configuration from JSON file."""
    path = config_path if os.path.isabs(config_path) else os.path.join(root_dir, config_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data sources config not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_spark_session():
    """Get or create a SparkSession for PySpark operations."""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark is None:
            spark = (
                SparkSession.builder
                .appName("dq-framework")
                .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
                .getOrCreate()
            )
        return spark
    except ImportError as e:
        raise ImportError(
            "PySpark is required for engine='spark'. Install with: pip install pyspark"
        ) from e


def load_data_from_source(
    source_config: dict,
    root_dir: str,
    engine: str = "pandas",
) -> Tuple[Union[pd.DataFrame, "SparkDataFrame"], str]:
    """
    Load data from a source (csv, sqlite, or hive).

    Args:
        source_config: Source configuration dict (path, database, source_table, etc.)
        root_dir: Root directory for resolving relative paths
        engine: "pandas" (default) or "spark" - which engine to use for loading

    Returns:
        Tuple of (DataFrame, rules_table) - rules_table is used for rule matching.
    """
    source_type = source_config.get("data_source", "csv").lower()
    rules_table = source_config.get("rules_table") or source_config.get(
        "source_id", "dataset"
    )

    if engine.lower() == "spark":
        return _load_spark(source_config, root_dir, source_type, rules_table)
    return _load_pandas(source_config, root_dir, source_type, rules_table)


def _load_pandas(
    source_config: dict, root_dir: str, source_type: str, rules_table: str
) -> Tuple[pd.DataFrame, str]:
    """Load data using pandas."""
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

    if source_type == "hive":
        raise ValueError(
            "Hive sources require engine='spark'. Use load_data_from_source(..., engine='spark')"
        )

    raise ValueError(
        f"Unknown source type: {source_type}. Expected 'csv', 'sqlite', or 'hive'."
    )


def _load_spark(
    source_config: dict, root_dir: str, source_type: str, rules_table: str
) -> Tuple["SparkDataFrame", str]:
    """Load data using PySpark."""
    spark = _get_spark_session()

    if source_type == "csv":
        path = source_config.get("path")
        if not path:
            raise ValueError("CSV source must have 'path'")
        full_path = path if os.path.isabs(path) else os.path.join(root_dir, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        header = source_config.get("header", True)
        infer_schema = source_config.get("infer_schema", True)
        df = (
            spark.read
            .option("header", str(header).lower())
            .option("inferSchema", str(infer_schema).lower())
            .csv(full_path)
        )
        return df, rules_table

    if source_type == "sqlite":
        database = source_config.get("database")
        source_table = source_config.get("source_table")
        if not database or not source_table:
            raise ValueError("SQLite source must have 'database' and 'source_table'")
        db_path = database if os.path.isabs(database) else os.path.join(root_dir, database)
        # PySpark does not natively support SQLite; use pandas + convert with explicit schema
        # to avoid legacyInferArrayTypeFromFirstElement issues (PySpark/Java version mismatch)
        import pandas as pd
        from pyspark.sql.types import (
            StructType,
            StructField,
            StringType,
            LongType,
            DoubleType,
            BooleanType,
            TimestampType,
        )

        conn_str = f"sqlite:///{os.path.normpath(db_path).replace(os.sep, '/')}"
        engine = create_engine(conn_str)
        pdf = pd.read_sql_table(source_table, engine)
        # Build explicit schema from pandas dtypes to avoid schema inference
        type_map = {
            "int8": LongType(),
            "int16": LongType(),
            "int32": LongType(),
            "int64": LongType(),
            "uint8": LongType(),
            "uint16": LongType(),
            "uint32": LongType(),
            "float32": DoubleType(),
            "float64": DoubleType(),
            "bool": BooleanType(),
            "datetime64[ns]": TimestampType(),
        }
        fields = []
        for col_name, dtype in pdf.dtypes.items():
            spark_type = type_map.get(str(dtype), StringType())
            fields.append(StructField(col_name, spark_type, nullable=True))
        schema = StructType(fields)
        df = spark.createDataFrame(pdf, schema=schema)
        return df, rules_table

    if source_type == "hive":
        table_name = source_config.get("table") or source_config.get("source_table")
        query = source_config.get("query")
        if table_name:
            df = spark.table(table_name)
        elif query:
            df = spark.sql(query)
        else:
            raise ValueError(
                "Hive source must have 'table' (or 'source_table') or 'query'"
            )
        return df, rules_table

    raise ValueError(
        f"Unknown source type: {source_type}. Expected 'csv', 'sqlite', or 'hive'."
    )
