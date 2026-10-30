# Database Sinks

Write transformed data to a database table. Use this when the results of a pipeline should land in a database instead of files.

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
| `mode` | No | `append` | Write mode: `append`, `truncate`, `replace`, `upsert` |
| `upsert_keys` | For `upsert` | - | Columns that identify a row, such as `[id]` |

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
    The delete and insert run in one transaction, so if the insert fails, the old rows stay.

### Upsert

Update rows that already exist and add the rest. Rows are matched on `upsert_keys`:

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: customers
  mode: upsert
  upsert_keys: [customer_id]
```

QuickETL picks one of two ways to do this, based on your database and your keys:

| Situation | What happens |
|-----------|--------------|
| DuckDB, Snowflake or BigQuery, with **one** key column | One native `MERGE` statement updates matching rows and inserts the rest |
| Any other database, or **more than one** key column | Matching rows are deleted and all incoming rows are inserted, in one transaction |

Both ways give the same result. The `MERGE` path is a single statement, so it succeeds or fails as a whole. QuickETL never switches to the other way after an error. If a `MERGE` fails, you see that error and the table keeps its original rows.

!!! note "MERGE Needs Unique Keys in the New Data"
    A `MERGE` can fail if two incoming rows have the same key. The delete-then-insert way would keep both. Remove duplicate keys before the sink if this matters to you.

### Replace

Drop and recreate the table with new data:

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: sales_summary
  mode: replace
```

!!! warning "Replace Drops the Table"
    Replace will drop the existing table and create a new one. This means any indexes, constraints, or grants on the table will be lost.

## How Writes Stay Safe

A failed write never leaves the table half written:

- **`truncate`**, and **`upsert` without `MERGE`**, copy the new rows into a temporary staging table, then delete and insert inside one transaction. If any step fails, the transaction is rolled back, the table keeps its original rows, and you see the real database error.
- **`upsert` with `MERGE`** (see [Upsert](#upsert)) runs as a single statement. If it fails, nothing changes and you see the real database error.
- **`append`** inserts in a single statement. If it fails, you see the real database error.
- **`replace`** builds the new table before swapping it in.

`truncate`, and `upsert` without `MERGE`, need a database that supports transactions (`BEGIN`, `COMMIT`, `ROLLBACK`). On a database without them, QuickETL stops with an error instead of risking data loss.

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

### Table Creation

- **`append`, `truncate` and `upsert` modes**: If the table does not exist yet, QuickETL creates it from the data.
- **`replace` mode**: The table is always recreated from the data.

For `append` mode with an existing table:

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

QuickETL attempts to convert types automatically. For best results:

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
from quicketl.config.models import DatabaseSink

# Basic (append mode)
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

# With replace (drops and recreates table)
sink = DatabaseSink(
    connection="${DATABASE_URL}",
    table="sales_summary",
    mode="replace"
)

# With upsert (match rows on customer_id)
sink = DatabaseSink(
    connection="${DATABASE_URL}",
    table="customers",
    mode="upsert",
    upsert_keys=["customer_id"]
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

### Truncate vs Replace

`truncate` deletes rows and keeps the table, so indexes, constraints and grants stay. `replace` rebuilds the table, which can be faster for a full refresh but loses those settings.

### Connection Pooling

For high-frequency pipelines, consider connection pooling at the database level.

## Troubleshooting

### Transaction Not Supported

```
RuntimeError: Write mode needs transaction support to avoid losing rows, and the '<backend>' backend could not start a transaction
```

`truncate` and `upsert` need transactions. Use `replace` for a full refresh, or `append` for new rows only.

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

Verify the database user has INSERT and CREATE TABLE permissions, plus DELETE for `truncate` and `upsert` mode. CREATE TABLE is needed for the staging table.

## Limitations

### Upsert With `MERGE` Is Limited

Native `MERGE` is used only on DuckDB, Snowflake and BigQuery, and only with a single key column. Other databases and multi-column keys use delete then insert inside a transaction. PostgreSQL also uses the transaction path, because `MERGE` needs PostgreSQL 15 or newer and the transaction path works on every version. Only the DuckDB `MERGE` path and the transaction path are covered by QuickETL's automated tests.

### Limited Schema Management

- `replace` mode creates tables automatically from the data schema
- `append` and `truncate` modes will create tables if they don't exist
- QuickETL does not modify existing table schemas (add/remove columns)

## Related

- [Database Sources](database-sources.md) - Reading from databases
- [File Sinks](file-sinks.md) - Alternative: write to files
- [Backends](../backends/index.md) - Database backend details
