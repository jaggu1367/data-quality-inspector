"""
Builds Great Expectations expectations from database rules.

Supports both pandas and PySpark DataFrames.
"""

import logging
from typing import Any, Dict, List, Union

import pandas as pd

from dq_framework.core.models import DataQualityRule

# Suppress redundant GE batch manager warning
logging.getLogger("great_expectations.core.batch_manager").setLevel(logging.ERROR)


def _is_spark_dataframe(obj) -> bool:
    """Check if the object is a PySpark DataFrame."""
    try:
        from pyspark.sql import DataFrame as SparkDataFrame
        return isinstance(obj, SparkDataFrame)
    except ImportError:
        return False


class PandasDataset:
    """
    Wrapper class that provides Great Expectations expectation methods on pandas DataFrames.
    Mimics the old PandasDataset API for compatibility with v1.11.3.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __getattr__(self, name):
        """Dynamically handle expectation method calls."""
        if name.startswith("expect_"):
            def expectation_wrapper(**kwargs):
                return self._execute_expectation(name, **kwargs)
            return expectation_wrapper
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _execute_expectation(self, expectation_type: str, **kwargs) -> Dict[str, Any]:
        """Execute an expectation using Great Expectations v1.11.3 API."""
        try:
            from great_expectations.expectations.registry import get_expectation_impl
            from great_expectations.validator.validator import ExpectationConfiguration
            from great_expectations.execution_engine import PandasExecutionEngine
            from great_expectations.validator.validator import Validator

            exp_impl = get_expectation_impl(expectation_type)
            config = ExpectationConfiguration(type=expectation_type, kwargs=kwargs)
            execution_engine = PandasExecutionEngine(batch_data_dict={"default": self.df})
            validator = Validator(execution_engine=execution_engine)
            result = validator.graph_validate(configurations=[config])[0]

            return {
                "success": result.success,
                "result": result.result if hasattr(result, "result") else {},
                "expectation_config": {
                    "expectation_type": expectation_type,
                    "kwargs": kwargs,
                },
                "exception_info": result.exception_info if hasattr(result, "exception_info") else None,
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "result": None,
                "expectation_config": {
                    "expectation_type": expectation_type,
                    "kwargs": kwargs,
                },
                "exception_info": f"{str(e)}\n{traceback.format_exc()}",
            }


class SparkDataset:
    """
    Wrapper class that provides Great Expectations expectation methods on PySpark DataFrames.
    Uses SparkDFExecutionEngine for distributed validation.
    """

    def __init__(self, df):  # pyspark.sql.DataFrame
        self.df = df

    def __getattr__(self, name):
        """Dynamically handle expectation method calls."""
        if name.startswith("expect_"):
            def expectation_wrapper(**kwargs):
                return self._execute_expectation(name, **kwargs)
            return expectation_wrapper
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _execute_expectation(self, expectation_type: str, **kwargs) -> Dict[str, Any]:
        """Execute an expectation using Great Expectations SparkDFExecutionEngine."""
        try:
            from great_expectations.expectations.registry import get_expectation_impl
            from great_expectations.validator.validator import ExpectationConfiguration
            from great_expectations.execution_engine import SparkDFExecutionEngine
            from great_expectations.validator.validator import Validator

            exp_impl = get_expectation_impl(expectation_type)
            config = ExpectationConfiguration(type=expectation_type, kwargs=kwargs)
            execution_engine = SparkDFExecutionEngine()
            execution_engine.load_batch_data(batch_id="default", batch_data=self.df)
            validator = Validator(execution_engine=execution_engine)
            result = validator.graph_validate(configurations=[config])[0]

            return {
                "success": result.success,
                "result": result.result if hasattr(result, "result") else {},
                "expectation_config": {
                    "expectation_type": expectation_type,
                    "kwargs": kwargs,
                },
                "exception_info": result.exception_info if hasattr(result, "exception_info") else None,
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "result": None,
                "expectation_config": {
                    "expectation_type": expectation_type,
                    "kwargs": kwargs,
                },
                "exception_info": f"{str(e)}\n{traceback.format_exc()}",
            }


class ExpectationBuilder:
    """Builds Great Expectations expectations from rule configurations."""

    def __init__(self):
        self.supported_expectations = self._get_supported_expectations()

    def _get_supported_expectations(self) -> Dict[str, str]:
        """Get mapping of expectation types to their methods."""
        return {
            "expect_column_to_exist": "expect_column_to_exist",
            "expect_column_values_to_be_in_type_list": "expect_column_values_to_be_in_type_list",
            "expect_column_values_to_be_of_type": "expect_column_values_to_be_of_type",
            "expect_column_values_to_not_be_null": "expect_column_values_to_not_be_null",
            "expect_column_values_to_be_null": "expect_column_values_to_be_null",
            "expect_column_values_to_be_unique": "expect_column_values_to_be_unique",
            "expect_column_values_to_be_unique_across_table": "expect_column_values_to_be_unique_across_table",
            "expect_column_values_to_be_in_set": "expect_column_values_to_be_in_set",
            "expect_column_values_to_not_be_in_set": "expect_column_values_to_not_be_in_set",
            "expect_column_values_to_be_between": "expect_column_values_to_be_between",
            "expect_column_values_to_be_in_numeric_range": "expect_column_values_to_be_in_numeric_range",
            "expect_column_min_to_be_between": "expect_column_min_to_be_between",
            "expect_column_max_to_be_between": "expect_column_max_to_be_between",
            "expect_column_mean_to_be_between": "expect_column_mean_to_be_between",
            "expect_column_median_to_be_between": "expect_column_median_to_be_between",
            "expect_column_stdev_to_be_between": "expect_column_stdev_to_be_between",
            "expect_column_quantile_values_to_be_between": "expect_column_quantile_values_to_be_between",
            "expect_column_values_to_match_regex": "expect_column_values_to_match_regex",
            "expect_column_values_to_not_match_regex": "expect_column_values_to_not_match_regex",
            "expect_column_values_to_match_regex_list": "expect_column_values_to_match_regex_list",
            "expect_column_values_to_not_match_regex_list": "expect_column_values_to_not_match_regex_list",
            "expect_column_values_to_match_like_pattern": "expect_column_values_to_match_like_pattern",
            "expect_column_values_to_not_match_like_pattern": "expect_column_values_to_not_match_like_pattern",
            "expect_column_values_to_match_strftime_format": "expect_column_values_to_match_strftime_format",
            "expect_column_values_to_be_dateutil_parseable": "expect_column_values_to_be_dateutil_parseable",
            "expect_column_values_to_be_json_parseable": "expect_column_values_to_be_json_parseable",
            "expect_column_value_lengths_to_be_between": "expect_column_value_lengths_to_be_between",
            "expect_column_value_lengths_to_equal": "expect_column_value_lengths_to_equal",
            "expect_column_values_to_be_increasing": "expect_column_values_to_be_increasing",
            "expect_column_values_to_be_decreasing": "expect_column_values_to_be_decreasing",
            "expect_table_row_count_to_be_between": "expect_table_row_count_to_be_between",
            "expect_table_row_count_to_equal": "expect_table_row_count_to_equal",
            "expect_table_column_count_to_be_between": "expect_table_column_count_to_be_between",
            "expect_table_column_count_to_equal": "expect_table_column_count_to_equal",
            "expect_table_columns_to_match_ordered_list": "expect_table_columns_to_match_ordered_list",
            "expect_table_columns_to_match_set": "expect_table_columns_to_match_set",
            "expect_compound_columns_to_be_unique": "expect_compound_columns_to_be_unique",
        }

    def build_expectation(
        self, rule: DataQualityRule, dataset: Union[PandasDataset, SparkDataset]
    ) -> Dict[str, Any]:
        """Build and execute an expectation based on a rule."""
        expectation_type = rule.expectation_type
        kwargs = rule.kwargs.copy()

        if rule.column_name and "column" not in kwargs:
            kwargs["column"] = rule.column_name

        method_name = self.supported_expectations.get(expectation_type, expectation_type)

        if not hasattr(dataset, method_name):
            raise AttributeError(
                f"Expectation method '{method_name}' not found on dataset. "
                f"Available methods starting with 'expect_': "
                f"{[m for m in dir(dataset) if m.startswith('expect_')]}"
            )

        expectation_method = getattr(dataset, method_name)

        try:
            result = expectation_method(**kwargs)
            return {
                "success": result.get("success", False),
                "result": result,
                "expectation_config": result.get("expectation_config", {}),
                "exception_info": None,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "expectation_config": {
                    "expectation_type": expectation_type,
                    "kwargs": kwargs,
                },
                "exception_info": str(e),
            }

    def validate_dataframe(
        self, df: Union[pd.DataFrame, Any], rules: List[DataQualityRule]
    ) -> Dict[str, Any]:
        """Validate a pandas or PySpark DataFrame against multiple rules."""
        if _is_spark_dataframe(df):
            ge_dataset = SparkDataset(df)
        else:
            ge_dataset = PandasDataset(df)
        results = {}
        for rule in rules:
            try:
                result = self.build_expectation(rule, ge_dataset)
                results[rule.rule_name] = result
            except Exception as e:
                results[rule.rule_name] = {
                    "success": False,
                    "result": None,
                    "expectation_config": {
                        "expectation_type": rule.expectation_type,
                        "kwargs": rule.kwargs,
                    },
                    "exception_info": str(e),
                }
        return results
