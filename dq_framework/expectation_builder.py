"""
Builds Great Expectations expectations from database rules
"""
from typing import Dict, Any, Optional
import great_expectations as ge
import pandas as pd

from dq_framework.database import DataQualityRule


class PandasDataset:
    """
    Wrapper class that provides Great Expectations expectation methods on pandas DataFrames.
    This mimics the old PandasDataset API for compatibility with v1.11.3.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._setup_expectation_methods()
    
    def _setup_expectation_methods(self):
        """Dynamically add expectation methods to this instance"""
        # Get all expectation classes from Great Expectations
        try:
            from great_expectations.expectations.registry import get_expectation_impl
            # For each expectation type, create a method that calls it
            expectation_types = [
                'expect_column_to_exist',
                'expect_column_values_to_not_be_null',
                'expect_column_values_to_be_null',
                'expect_column_values_to_be_unique',
                'expect_column_values_to_be_in_set',
                'expect_column_values_to_not_be_in_set',
                'expect_column_values_to_be_between',
                'expect_column_values_to_be_in_type_list',
                'expect_column_mean_to_be_between',
                'expect_column_median_to_be_between',
                'expect_column_stdev_to_be_between',
                'expect_column_min_to_be_between',
                'expect_column_max_to_be_between',
                'expect_column_values_to_match_regex',
                'expect_column_values_to_not_match_regex',
                'expect_column_values_to_match_regex_list',
                'expect_column_values_to_not_match_regex_list',
                'expect_column_values_to_match_strftime_format',
                'expect_column_value_lengths_to_be_between',
                'expect_column_value_lengths_to_equal',
                'expect_column_values_to_be_of_type',
                'expect_column_values_to_be_increasing',
                'expect_column_values_to_be_decreasing',
                'expect_column_values_to_be_dateutil_parseable',
                'expect_column_values_to_be_json_parseable',
                'expect_column_values_to_match_like_pattern',
                'expect_column_values_to_not_match_like_pattern',
                'expect_column_quantile_values_to_be_between',
                'expect_column_values_to_be_in_numeric_range',
                'expect_column_values_to_be_unique_across_table',
                'expect_table_row_count_to_be_between',
                'expect_table_row_count_to_equal',
                'expect_table_column_count_to_be_between',
                'expect_table_column_count_to_equal',
                'expect_table_columns_to_match_ordered_list',
                'expect_table_columns_to_match_set',
                'expect_compound_columns_to_be_unique',
            ]
            
            # Methods will be handled by __getattr__ and _execute_expectation
            pass
        except Exception as e:
            # Fallback: use a simpler approach with direct method calls
            pass
    
    def __getattr__(self, name):
        """Dynamically handle expectation method calls"""
        if name.startswith('expect_'):
            def expectation_wrapper(**kwargs):
                return self._execute_expectation(name, **kwargs)
            return expectation_wrapper
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def _execute_expectation(self, expectation_type: str, **kwargs) -> Dict[str, Any]:
        """Execute an expectation using Great Expectations v1.11.3 API"""
        try:
            from great_expectations.expectations.registry import get_expectation_impl
            from great_expectations.validator.validator import ExpectationConfiguration
            from great_expectations.execution_engine import PandasExecutionEngine
            from great_expectations.validator.validator import Validator
            
            # Get expectation implementation
            exp_impl = get_expectation_impl(expectation_type)
            
            # Create expectation configuration
            config = ExpectationConfiguration(
                type=expectation_type,
                kwargs=kwargs
            )
            
            # Create execution engine and validator
            execution_engine = PandasExecutionEngine(batch_data_dict={"default": self.df})
            validator = Validator(execution_engine=execution_engine)
            
            # Execute expectation
            result = validator.graph_validate(configurations=[config])[0]
            
            # Format result to match expected structure
            return {
                'success': result.success,
                'result': result.result if hasattr(result, 'result') else {},
                'expectation_config': {
                    'expectation_type': expectation_type,
                    'kwargs': kwargs
                },
                'exception_info': result.exception_info if hasattr(result, 'exception_info') else None
            }
        except Exception as e:
            import traceback
            return {
                'success': False,
                'result': None,
                'expectation_config': {
                    'expectation_type': expectation_type,
                    'kwargs': kwargs
                },
                'exception_info': f"{str(e)}\n{traceback.format_exc()}"
            }


class ExpectationBuilder:
    """Builds Great Expectations expectations from rule configurations"""
    
    def __init__(self):
        self.supported_expectations = self._get_supported_expectations()
    
    def _get_supported_expectations(self) -> Dict[str, Any]:
        """Get mapping of expectation types to their methods"""
        # Common expectation types in Great Expectations v1.11.3
        # Note: This framework dynamically supports all GE expectation types
        # The dictionary maps expectation type names to method names
        return {
            # Column existence and type expectations
            "expect_column_to_exist": "expect_column_to_exist",
            "expect_column_values_to_be_in_type_list": "expect_column_values_to_be_in_type_list",
            "expect_column_values_to_be_of_type": "expect_column_values_to_be_of_type",
            
            # Null value expectations
            "expect_column_values_to_not_be_null": "expect_column_values_to_not_be_null",
            "expect_column_values_to_be_null": "expect_column_values_to_be_null",
            
            # Uniqueness expectations
            "expect_column_values_to_be_unique": "expect_column_values_to_be_unique",
            "expect_column_values_to_be_unique_across_table": "expect_column_values_to_be_unique_across_table",
            
            # Set membership expectations
            "expect_column_values_to_be_in_set": "expect_column_values_to_be_in_set",
            "expect_column_values_to_not_be_in_set": "expect_column_values_to_not_be_in_set",
            
            # Range and comparison expectations
            "expect_column_values_to_be_between": "expect_column_values_to_be_between",
            "expect_column_values_to_be_in_numeric_range": "expect_column_values_to_be_in_numeric_range",
            "expect_column_min_to_be_between": "expect_column_min_to_be_between",
            "expect_column_max_to_be_between": "expect_column_max_to_be_between",
            
            # Statistical expectations
            "expect_column_mean_to_be_between": "expect_column_mean_to_be_between",
            "expect_column_median_to_be_between": "expect_column_median_to_be_between",
            "expect_column_stdev_to_be_between": "expect_column_stdev_to_be_between",
            "expect_column_quantile_values_to_be_between": "expect_column_quantile_values_to_be_between",
            
            # Pattern matching expectations
            "expect_column_values_to_match_regex": "expect_column_values_to_match_regex",
            "expect_column_values_to_not_match_regex": "expect_column_values_to_not_match_regex",
            "expect_column_values_to_match_regex_list": "expect_column_values_to_match_regex_list",
            "expect_column_values_to_not_match_regex_list": "expect_column_values_to_not_match_regex_list",
            "expect_column_values_to_match_like_pattern": "expect_column_values_to_match_like_pattern",
            "expect_column_values_to_not_match_like_pattern": "expect_column_values_to_not_match_like_pattern",
            
            # Format expectations
            "expect_column_values_to_match_strftime_format": "expect_column_values_to_match_strftime_format",
            "expect_column_values_to_be_dateutil_parseable": "expect_column_values_to_be_dateutil_parseable",
            "expect_column_values_to_be_json_parseable": "expect_column_values_to_be_json_parseable",
            
            # Length expectations
            "expect_column_value_lengths_to_be_between": "expect_column_value_lengths_to_be_between",
            "expect_column_value_lengths_to_equal": "expect_column_value_lengths_to_equal",
            
            # Order expectations
            "expect_column_values_to_be_increasing": "expect_column_values_to_be_increasing",
            "expect_column_values_to_be_decreasing": "expect_column_values_to_be_decreasing",
            
            # Table-level expectations
            "expect_table_row_count_to_be_between": "expect_table_row_count_to_be_between",
            "expect_table_row_count_to_equal": "expect_table_row_count_to_equal",
            "expect_table_column_count_to_be_between": "expect_table_column_count_to_be_between",
            "expect_table_column_count_to_equal": "expect_table_column_count_to_equal",
            "expect_table_columns_to_match_ordered_list": "expect_table_columns_to_match_ordered_list",
            "expect_table_columns_to_match_set": "expect_table_columns_to_match_set",
            "expect_compound_columns_to_be_unique": "expect_compound_columns_to_be_unique",
        }
    
    def build_expectation(self, rule: DataQualityRule, dataset: PandasDataset) -> Dict[str, Any]:
        """
        Build and add an expectation to a dataset based on a rule
        
        Args:
            rule: DataQualityRule instance
            dataset: Great Expectations PandasDataset
            
        Returns:
            Dictionary containing expectation configuration and result
        """
        expectation_type = rule.expectation_type
        kwargs = rule.kwargs.copy()
        
        # Ensure column_name is in kwargs if rule has column_name
        if rule.column_name and 'column' not in kwargs:
            kwargs['column'] = rule.column_name
        
        # Get the expectation method name
        # First check our supported list, then try dynamic discovery
        if expectation_type in self.supported_expectations:
            method_name = self.supported_expectations[expectation_type]
        else:
            # Try dynamic discovery - Great Expectations uses the same name for type and method
            method_name = expectation_type
        
        # Get the expectation method from the dataset
        if not hasattr(dataset, method_name):
            raise AttributeError(
                f"Expectation method '{method_name}' not found on dataset. "
                f"Available methods starting with 'expect_': {[m for m in dir(dataset) if m.startswith('expect_')]}"
            )
        
        expectation_method = getattr(dataset, method_name)
        
        # Call the expectation method with kwargs
        try:
            result = expectation_method(**kwargs)
            return {
                'success': result.get('success', False),
                'result': result,
                'expectation_config': result.get('expectation_config', {}),
                'exception_info': None
            }
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'expectation_config': {
                    'expectation_type': expectation_type,
                    'kwargs': kwargs
                },
                'exception_info': str(e)
            }
    
    def validate_dataframe(self, df: pd.DataFrame, rules: list[DataQualityRule]) -> Dict[str, Any]:
        """
        Validate a pandas DataFrame against multiple rules
        
        Args:
            df: pandas DataFrame to validate
            rules: List of DataQualityRule instances
            
        Returns:
            Dictionary containing validation results for each rule
        """
        # Convert DataFrame to Great Expectations dataset wrapper
        ge_dataset = PandasDataset(df)
        
        results = {}
        for rule in rules:
            try:
                result = self.build_expectation(rule, ge_dataset)
                results[rule.rule_name] = result
            except Exception as e:
                results[rule.rule_name] = {
                    'success': False,
                    'result': None,
                    'expectation_config': {
                        'expectation_type': rule.expectation_type,
                        'kwargs': rule.kwargs
                    },
                    'exception_info': str(e)
                }
        
        return results
