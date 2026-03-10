# Spark vs Pandas Validation Analysis: products_sqlite

> **See also:** [SPARK_VS_PANDAS_INVESTIGATION_REPORT.md](SPARK_VS_PANDAS_INVESTIGATION_REPORT.md) for the full investigation, remediation attempts, and final recommendations.

## Summary

| Engine | Result | Passed | Failed |
|-------|--------|--------|--------|
| **Pandas** | PASSED | 28/28 | 0 |
| **Spark** | FAILED | 15/28 | 13 |

## Root Cause: Great Expectations + PySpark 3.5 API Incompatibility

The Spark failures are **not** due to data differences. They are caused by a **version incompatibility** between Great Expectations 1.11.3 and PySpark 3.5.8.

### The Error

All 13 failing rules raise the same underlying exception:

```
py4j.Py4JException: Method drop([class org.apache.spark.sql.Column, class scala.collection.convert.Wrappers$JListWrapper]) does not exist
```

**Location:** `great_expectations/expectations/metrics/map_metric_provider/column_map_condition_auxilliary_methods.py`, line 295, in `_spark_column_map_condition_values`:

```python
filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
```

Great Expectations calls `df.drop(F.col("__unexpected"))` — passing a **Column object** to `drop()`. PySpark 3.5's Java bridge no longer accepts this signature; the Scala/Java `drop` method signature has changed.

### Which Rules Fail (All Share the Same Code Path)

All failing rules use the "column map" metric pattern (row-level validation):

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

### Which Rules Pass (Different Code Paths)

Rules that pass use **aggregate** or **table-level** metrics (no column map condition):

- Column existence, type checks
- `expect_column_mean_to_be_between`, `expect_column_min_to_be_between`
- `expect_table_row_count_to_be_between`, `expect_table_column_count_to_be_between`, `expect_table_columns_to_match_set`

---

## Version Information

| Component | Version |
|-----------|---------|
| Python | 3.13.7 |
| PySpark | 3.5.8 |
| Great Expectations | 1.11.3 |
| Pandas | 2.3.3 |

## Data Path Difference (Not the Cause)

- **Pandas:** Reads SQLite directly via `pd.read_sql_table()` — native support.
- **Spark:** PySpark has no native SQLite support. The loader:
  1. Reads via pandas: `pd.read_sql_table()`
  2. Exports to temp CSV: `data/spark_sqlite_products.csv`
  3. Loads CSV with Spark using schema from `schemas/products.json`

The data itself is equivalent. The failures occur during **metric computation** in GE's Spark execution engine, not during data loading.

---

## Recommendations

### 1. ~~Downgrade PySpark~~ (Attempted — Does Not Fix)

Downgrading to PySpark 3.4.x was attempted with Python 3.12. The same `drop()` error persists. The issue is in Great Expectations, not PySpark version. See [SPARK_VS_PANDAS_INVESTIGATION_REPORT.md](SPARK_VS_PANDAS_INVESTIGATION_REPORT.md).

### 2. Upgrade Great Expectations

Check if a newer GE release (e.g. 1.x or 2.x) fixes the Spark `drop()` compatibility. The GE codebase has had Spark-related fixes (e.g. PR #7626 for map condition memory issues).

### 3. Use Pandas for SQLite Sources

For SQLite-backed sources, use the pandas engine. Spark adds overhead (temp CSV export) and does not provide distributed benefits for small local datasets:

```bash
python scripts/run_expectations.py --source-id products_sqlite --engine pandas
```

### 4. Monitor GE + PySpark Compatibility

Track:
- [GE Issue #10559](https://github.com/great-expectations/great_expectations/issues/10559) – Spark column resolution
- [GE PR #7626](https://github.com/great-expectations/great_expectations/pull/7626) – Map condition Spark fixes
- [Spark PR #37335](https://github.com/apache/spark/pull/37335) – `drop(Column*)` support

---

## Conclusion

The Spark vs Pandas discrepancy is **not** due to:
- Data quality differences
- Schema mismatches
- Null handling differences

It **is** due to:
- **Great Expectations 1.11.3** using `df.drop(Column)` in its Spark map-metric code
- The PySpark/Java `drop` method rejecting this call pattern (confirmed in both PySpark 3.4.4 and 3.5.8)

**Recommended action:** Use `--engine pandas` for SQLite sources until Great Expectations fixes the Spark `drop()` usage in its map-metric code.
