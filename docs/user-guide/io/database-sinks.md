# Database Sinks

Write transformed data to relational databases.

## Basic Usage

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: sales_summary
```

## Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | Yes | - | Must be `database` |
| `connection` | Yes | - | Database connection string |
| `table` | Yes | - | Target table name |
| `mode` | No | `append` | Write mode: `append`, `truncate` |

## Write Modes

### Append (Default)

Add new rows to existing data:

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: sales_summary
  mode: append
```

### Truncate

Delete existing data before writing:

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: sales_summary
  mode: truncate
```

!!! warning "Truncate is Destructive"
    Truncate deletes all existing data in the table before inserting new data.

## Connection Strings

### PostgreSQL

```yaml
sink:
  type: database
  connection: postgresql://user:password@host:5432/database
  table: results
```

### MySQL

```yaml
sink:
  type: database
  connection: mysql://user:password@host:3306/database
  table: results
```

### Using Environment Variables

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: ${TARGET_TABLE}
```

```bash
export DATABASE_URL=postgresql://user:pass@localhost/db
export TARGET_TABLE=sales_summary
```

## Examples

### Daily Summary Table

```yaml
name: daily_sales_summary
engine: duckdb

source:
  type: file
  path: s3://data-lake/raw/sales/${DATE}/*.parquet

transforms:
  - op: aggregate
    group_by: [region, category]
    aggs:
      total_sales: sum(amount)
      order_count: count(*)

sink:
  type: database
  connection: ${POSTGRES_URL}
  table: daily_summaries
  mode: append
```

### Incremental Load

```yaml
name: incremental_load
engine: duckdb

source:
  type: database
  connection: ${SOURCE_DB}
  query: |
    SELECT * FROM orders
    WHERE updated_at > '${LAST_RUN}'

transforms:
  - op: select
    columns: [id, customer_id, amount, status, updated_at]

sink:
  type: database
  connection: ${TARGET_DB}
  table: orders_replica
  mode: append
```

### Full Refresh

```yaml
name: full_refresh
engine: duckdb

source:
  type: file
  path: data/products.csv
  format: csv

transforms:
  - op: filter
    predicate: active = true

sink:
  type: database
  connection: ${DATABASE_URL}
  table: active_products
  mode: truncate
```

## Table Requirements

### Table Must Exist

ETLX does not create tables automatically. Create the table first:

```sql
CREATE TABLE sales_summary (
    region VARCHAR(50),
    category VARCHAR(50),
    total_sales DECIMAL(12,2),
    order_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Column Matching

Output columns must match table columns:

```yaml
transforms:
  # Ensure output matches table schema
  - op: select
    columns: [region, category, total_sales, order_count]
```

### Data Types

ETLX attempts to convert types automatically. For best results:

- Use compatible types
- Cast explicitly if needed:

```yaml
transforms:
  - op: cast
    columns:
      total_sales: float64
      order_count: int64
```

## Python API

```python
from etlx.config.models import DatabaseSink

# Basic
sink = DatabaseSink(
    connection="postgresql://localhost/db",
    table="results"
)

# With truncate
sink = DatabaseSink(
    connection="${DATABASE_URL}",
    table="sales_summary",
    mode="truncate"
)
```

## Performance Tips

### Batch Size

For large datasets, writes are batched automatically. Performance varies by database.

### Indexes

Disable indexes before large inserts, re-enable after:

```sql
-- Before pipeline
ALTER INDEX idx_sales_date DISABLE;

-- After pipeline
ALTER INDEX idx_sales_date REBUILD;
```

### Truncate vs Delete

`truncate` is faster than deleting all rows:

```yaml
mode: truncate  # Fast - drops and recreates
```

### Connection Pooling

For high-frequency pipelines, consider connection pooling at the database level.

## Troubleshooting

### Table Not Found

```
Error: Table 'results' does not exist
```

Create the table before running the pipeline.

### Column Mismatch

```
Error: Column 'extra_col' does not exist in table
```

Ensure your output columns match the table schema:

```yaml
transforms:
  - op: select
    columns: [col1, col2, col3]  # Only columns in target table
```

### Type Mismatch

```
Error: Cannot convert 'abc' to integer
```

Cast columns to correct types:

```yaml
transforms:
  - op: cast
    columns:
      amount: float64
```

### Permission Denied

```
Error: Permission denied for table 'results'
```

Verify the database user has INSERT (and TRUNCATE if using truncate mode) permissions.

## Limitations

### No Upsert (Yet)

Upsert/merge operations are planned for a future release. Currently, use:

- `append` for incremental loads
- `truncate` for full refreshes

### No Schema Management

ETLX does not create or modify table schemas. Manage schemas separately.

## Related

- [Database Sources](database-sources.md) - Reading from databases
- [File Sinks](file-sinks.md) - Alternative: write to files
- [Backends](../backends/index.md) - Database backend details
