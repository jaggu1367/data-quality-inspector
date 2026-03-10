# Spark vs Pandas Validation Discrepancy: Investigation Report

**Document Version:** 1.0  
**Date:** March 2026  
**Scope:** products_sqlite validation with `--engine pandas` vs `--engine spark`

---

## 1. Executive Summary

Validations for `products_sqlite` pass with the **pandas** engine (28/28 rules) but fail with the **spark** engine (15/28 passed, 13 failed). This report documents the investigation from the beginning, all remediation attempts, and final findings.

**Conclusion:** The discrepancy is caused by a **Great Expectations (GE) bug** in its Spark execution path. The issue is **not** fixable by downgrading PySpark or changing Python versions. Use `--engine pandas` for SQLite sources until GE is updated.

---

## 2. Initial Problem Statement

When running data quality validations on `products_sqlite`:

- **Pandas engine:** All 28 rules pass
- **Spark engine:** 13 rules fail with exceptions

The same dataset and rules produce different outcomes depending on the execution engine.

---

## 3. Investigation Steps

### 3.1 Run Validations with Both Engines and Log Results

Commands executed:

```powershell
# Pandas
python scripts/run_expectations.py --source-id products_sqlite --engine pandas --log-results

# Spark
python scripts/run_expectations.py --source-id products_sqlite --engine spark --log-results
```

### 3.2 Results Comparison

| Engine | Overall | Passed | Failed |
|--------|---------|--------|--------|
| **Pandas** | PASSED | 28/28 | 0 |
| **Spark** | FAILED | 15/28 | 13 |

### 3.3 Version Information (Initial Environment)

| Component | Version |
|-----------|---------|
| Python | 3.13.7 |
| PySpark | 3.5.8 |
| Great Expectations | 1.11.3 |
| Pandas | 2.3.3 |

### 3.4 Rules That Fail (Spark Only)

All 13 failing rules use row-level "column map" expectations:

| Rule | Expectation Type |
|------|------------------|
| products_not_null_product_id | expect_column_values_to_not_be_null |
| products_not_null_product_name | expect_column_values_to_not_be_null |
| products_not_null_category | expect_column_values_to_not_be_null |
| products_unique_product_id | expect_column_values_to_be_unique |
| products_in_set_status | expect_column_values_to_be_in_set |
| products_not_in_set_status_bad | expect_column_values_to_not_be_in_set |
| products_between_price | expect_column_values_to_be_between |
| products_between_stock_quantity | expect_column_values_to_be_between |
| products_not_regex_status_no_digit | expect_column_values_to_not_match_regex |
| products_regex_list_status | expect_column_values_to_match_regex_list |
| products_length_between_product_name | expect_column_value_lengths_to_be_between |
| products_increasing_product_id | expect_column_values_to_be_increasing |
| products_compound_unique_product_id_name | expect_compound_columns_to_be_unique |

### 3.5 Rules That Pass (Both Engines)

Rules that pass use aggregate or table-level metrics:

- Column existence checks
- Type checks (expect_column_values_to_be_in_type_list, expect_column_values_to_be_of_type)
- expect_column_mean_to_be_between, expect_column_min_to_be_between
- expect_table_row_count_to_be_between, expect_table_column_count_to_be_between
- expect_table_columns_to_match_set

---

## 4. Root Cause Analysis

### 4.1 The Exception

All 13 failing rules raise the same underlying error:

```
py4j.Py4JException: Method drop([class org.apache.spark.sql.Column, class scala.collection.convert.Wrappers$JListWrapper]) does not exist
```

### 4.2 Location in Great Expectations

**File:** `great_expectations/expectations/metrics/map_metric_provider/column_map_condition_auxilliary_methods.py`  
**Line:** ~295  
**Function:** `_spark_column_map_condition_values`

**Problematic code:**
```python
filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
```

Great Expectations passes a **Column object** to `DataFrame.drop()`. The PySpark/Java bridge rejects this call pattern.

### 4.3 Full Exception Traceback (Excerpt)

```
Traceback (most recent call last):
  File ".../great_expectations/execution_engine/execution_engine.py", line 577, in _process_direct_and_bundled_metric_computation_configurations
    metric_computation_configuration.metric_fn(...)
  File ".../great_expectations/expectations/metrics/map_metric_provider/column_map_condition_auxilliary_methods.py", line 295, in _spark_column_map_condition_values
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
...
py4j.protocol.Py4JError: An error occurred while calling o74.drop. Trace:
py4j.Py4JException: Method drop([class org.apache.spark.sql.Column, class scala.collection.convert.Wrappers$JListWrapper]) does not exist
```

### 4.4 Data Path: Not the Cause

- **Pandas:** Reads SQLite directly via `pd.read_sql_table()`.
- **Spark:** PySpark has no native SQLite support. The loader:
  1. Reads via pandas: `pd.read_sql_table()`
  2. Exports to temp CSV: `data/spark_sqlite_products.csv`
  3. Loads CSV with Spark using schema from `schemas/products.json`

The data is equivalent. Failures occur during **metric computation** in GE's Spark execution engine, not during data loading.

---

## 5. Remediation Attempts

### Attempt 1: Downgrade PySpark to 3.4.x

**Hypothesis:** PySpark 3.5.8 may have changed the `drop()` API. Downgrading to 3.4.x might restore compatibility.

**Actions:**
1. Uninstalled PySpark 3.5.8
2. Updated `requirements.txt` to `pyspark>=3.4.0,<3.5`
3. Installed PySpark 3.4.4

**Result:** **Blocked**

PySpark 3.4.4 fails to import on Python 3.13:

```
ModuleNotFoundError: No module named 'typing.io'; 'typing' is not a package
```

**Reason:** The `typing.io` namespace was removed in Python 3.13. PySpark 3.4.x still uses `from typing.io import BinaryIO` in `pyspark/broadcast.py` and was never updated for Python 3.13.

**Reference:** [SPARK-43160](https://issues.apache.org/jira/browse/SPARK-43160) – Remove typing.io namespace references

---

### Attempt 2: Install Python 3.12 and Use PySpark 3.4.x

**Hypothesis:** Use Python 3.12 (which retains `typing.io`) with PySpark 3.4.x to avoid the `drop()` incompatibility.

**Actions:**
1. Installed Python 3.12.10 via winget: `winget install Python.Python.3.12`
2. Created virtual environment: `py -3.12 -m venv .venv312`
3. Installed dependencies: `pip install -r requirements-spark34.txt`
4. Ran validations with both engines

**Result:** **Did not fix the issue**

| Engine | Result | Passed | Failed |
|--------|--------|--------|--------|
| Pandas | PASSED | 28/28 | 0 |
| Spark | FAILED | 15/28 | 13 |

The same `drop()` exception occurs with **PySpark 3.4.4** on Python 3.12. The problem is therefore **not** specific to PySpark 3.5; it exists in GE's Spark map-metric code across PySpark 3.4 and 3.5.

---

### Attempt 3: Revert to PySpark 3.5.8

**Actions:** Reverted `requirements.txt` to `pyspark>=3.4.0,<4` and reinstalled PySpark 3.5.8 for the default Python 3.13 environment.

**Reason:** PySpark 3.4.x cannot run on Python 3.13, and downgrading PySpark did not resolve the Spark validation failures.

---

## 6. Final Findings

### 6.1 Root Cause

The discrepancy is caused by a **bug in Great Expectations 1.11.3** in the Spark execution path:

- GE uses `df.drop(F.col("__unexpected"))` in `_spark_column_map_condition_values`
- The PySpark/Java `drop` method does not accept this call pattern (Column + JListWrapper)
- The issue appears in both PySpark 3.4.4 and 3.5.8

### 6.2 What Is NOT the Cause

- Data quality or schema differences
- Null handling differences between pandas and Spark
- PySpark 3.5 vs 3.4 version difference
- Python 3.13 vs 3.12

### 6.3 Environment Summary

| Environment | Python | PySpark | Spark Validation |
|-------------|--------|---------|------------------|
| Default | 3.13.7 | 3.5.8 | FAILED (13 rules) |
| .venv312 | 3.12.10 | 3.4.4 | FAILED (13 rules) |

---

## 7. Recommendations

### 7.1 Immediate: Use Pandas for SQLite Sources

For SQLite-backed sources, use the pandas engine:

```powershell
python scripts/run_expectations.py --source-id products_sqlite --engine pandas
```

**Rationale:** SQLite is local; Spark adds overhead (temp CSV export) without distributed benefits. Pandas validation is correct and sufficient.

### 7.2 For Spark Workloads (Hive, Large CSV)

- Use `--engine spark` only for sources that require distributed processing (e.g., Hive tables, large CSV files)
- Expect row-level "column map" expectations to fail until GE is fixed
- Aggregate and table-level expectations should continue to work

### 7.3 Monitor Great Expectations Updates

- Check for GE releases that fix Spark `drop()` usage
- Relevant issues: [GE #10559](https://github.com/great-expectations/great_expectations/issues/10559), [GE PR #7626](https://github.com/great-expectations/great_expectations/pull/7626)

### 7.4 Python 3.12 Environment (Optional)

The `.venv312` environment with PySpark 3.4.4 is available for testing:

```powershell
.\.venv312\Scripts\Activate.ps1
python scripts/run_expectations.py --source-id products_sqlite --engine pandas  # works
python scripts/run_expectations.py --source-id products_sqlite --engine spark  # same 13 failures
```

---

## 8. Appendix: Files and Commands

### 8.1 Key Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Main dependencies (pyspark>=3.4.0,<4) |
| `requirements-spark34.txt` | PySpark 3.4.x for Python 3.11/3.12 |
| `SPARK_VS_PANDAS_ANALYSIS.md` | Technical analysis of the error |
| `SPARK_VS_PANDAS_INVESTIGATION_REPORT.md` | This document |

### 8.2 Commands Used During Investigation

```powershell
# Run with logging
python scripts/run_expectations.py --source-id products_sqlite --engine pandas --log-results
python scripts/run_expectations.py --source-id products_sqlite --engine spark --log-results

# PySpark downgrade (blocked on Python 3.13)
pip uninstall pyspark -y
pip install "pyspark>=3.4.0,<3.5"

# Python 3.12 setup
winget install Python.Python.3.12
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
pip install -r requirements-spark34.txt
```

---

## 9. Revision History

| Date | Change |
|------|--------|
| 2026-03 | Initial investigation and report |
