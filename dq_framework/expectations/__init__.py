"""
Expectations module: Great Expectations integration.
"""

# Ensure distutils available for Python 3.12+ (PySpark toPandas uses it for compound-column expectations)
import setuptools  # noqa: F401

# Apply GE Spark drop() fix before any GE validation (required for Spark engine)
from dq_framework.ge_spark_patch import apply_ge_spark_patch

apply_ge_spark_patch()

from dq_framework.expectations.expectation_builder import (
    ExpectationBuilder,
    PandasDataset,
    SparkDataset,
)

__all__ = ["ExpectationBuilder", "PandasDataset", "SparkDataset"]
