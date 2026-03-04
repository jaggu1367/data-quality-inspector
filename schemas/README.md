# CSV Schema Definitions for PySpark

This folder contains schema definitions for CSV files used with the PySpark engine.
Schemas ensure consistent type inference and compatibility with Great Expectations
Spark type expectations (e.g., LongType, StringType instead of int64, str).

Each schema JSON maps to a `rules_table` from config/data_sources.json:
- `customers.json` -> rules_table: customers (sample_customers_100.csv)
- `orders.json` -> rules_table: orders (orders.csv)
- `products.json` -> rules_table: products (products.csv)

Schema format:
```json
{
  "fields": [
    {"name": "column_name", "type": "SparkType"}
  ]
}
```

Valid Spark types: StringType, IntegerType, LongType, DoubleType, FloatType, BooleanType, DateType, TimestampType
