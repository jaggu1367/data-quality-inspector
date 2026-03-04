"""
Load Spark schema definitions for CSV files.

Schema files live in schemas/<rules_table>.json and define column types
for PySpark to ensure compatibility with Great Expectations Spark type expectations.
"""

import json
import os
from typing import Any, Dict, List, Optional

# Spark type name -> pyspark.sql.types class
_SPARK_TYPE_MAP = {
    "StringType": None,  # Lazy load
    "IntegerType": None,
    "LongType": None,
    "DoubleType": None,
    "FloatType": None,
    "BooleanType": None,
    "DateType": None,
    "TimestampType": None,
    "ShortType": None,
    "ByteType": None,
}


def _get_spark_types_module():
    """Lazy import pyspark.sql.types."""
    from pyspark.sql import types as spark_types
    return spark_types


def load_schema_for_rules_table(rules_table: str, root_dir: str) -> Optional[Any]:
    """
    Load Spark StructType schema for a rules_table.

    Looks for schemas/<rules_table>.json relative to root_dir.
    Returns a pyspark.sql.types.StructType or None if not found.

    Args:
        rules_table: e.g. "customers", "orders", "products"
        root_dir: Project root directory

    Returns:
        StructType schema or None
    """
    schema_path = os.path.join(root_dir, "schemas", f"{rules_table}.json")
    if not os.path.isfile(schema_path):
        return None
    try:
        with open(schema_path, encoding="utf-8") as f:
            spec = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    fields = spec.get("fields", [])
    if not fields:
        return None

    spark_types = _get_spark_types_module()
    struct_fields = []
    for f in fields:
        type_name = f.get("type", "StringType")
        type_class = getattr(spark_types, type_name, None)
        if type_class is None:
            type_class = spark_types.StringType  # fallback
        struct_fields.append(
            spark_types.StructField(
                f.get("name", ""),
                type_class(),
                nullable=True,
            )
        )
    return spark_types.StructType(struct_fields)
