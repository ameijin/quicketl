# Pipeline YAML Reference

Complete reference for YAML pipeline configuration.

## Full Schema

```yaml
# Pipeline metadata
name: string                    # Required: Pipeline identifier
description: string             # Optional: Human-readable description
engine: string                  # Optional: Compute backend (default: "duckdb")
                               # Options: duckdb, polars, datafusion, spark, pandas

# Data source
source:
  type: file | database         # Required: Source type

  # For type: file
  path: string                  # Required: File path or cloud URI
  format: csv | parquet | json  # Optional: File format (default: parquet)
  options: object               # Optional: Format-specific options

  # For type: database
  connection: string            # Required: Connection string
  query: string                 # Optional: SQL query (mutually exclusive with table)
  table: string                 # Optional: Table name (mutually exclusive with query)

# Transformations (applied in order)
transforms:
  - op: select | rename | filter | derive_column | cast | fill_null |
        dedup | sort | join | aggregate | union | limit
    # ... operation-specific fields

# Quality checks (run after transforms)
checks:
  - type: not_null | unique | row_count | accepted_values | expression
    # ... check-specific fields

# Data sink
sink:
  type: file | database         # Required: Sink type

  # For type: file
  path: string                  # Required: Output path
  format: parquet | csv         # Optional: Output format (default: parquet)
  partition_by: [string]        # Optional: Partition columns
  mode: overwrite | append      # Optional: Write mode (default: overwrite)

  # For type: database
  connection: string            # Required: Connection string
  table: string                 # Required: Target table
  mode: append | truncate       # Optional: Write mode (default: append)
```

## Source Configuration

### File Source

Read from local files or cloud storage:

```yaml
source:
  type: file
  path: data/sales.parquet
  format: parquet
```

#### CSV Options

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
  options:
    delimiter: ","              # Field delimiter
    header: true                # First row is header
    skip_rows: 0                # Rows to skip
    null_values: ["", "NULL"]   # Values to treat as null
```

#### Cloud Storage Paths

```yaml
# Amazon S3
source:
  type: file
  path: s3://my-bucket/data/sales.parquet

# Google Cloud Storage
source:
  type: file
  path: gs://my-bucket/data/sales.parquet

# Azure ADLS
source:
  type: file
  path: abfs://container@account.dfs.core.windows.net/data/sales.parquet
```

### Database Source

Read from databases:

```yaml
# Using a query
source:
  type: database
  connection: postgresql://user:pass@localhost:5432/db
  query: SELECT * FROM sales WHERE date > '2025-01-01'

# Using a table
source:
  type: database
  connection: ${DATABASE_URL}
  table: sales
```

## Transform Configuration

Each transform has an `op` field that determines its type:

### select

```yaml
- op: select
  columns: [id, name, amount]   # Columns to keep (in order)
```

### rename

```yaml
- op: rename
  mapping:                      # Old name -> new name
    old_column: new_column
    another_old: another_new
```

### filter

```yaml
- op: filter
  predicate: amount > 100 AND status = 'active'
```

### derive_column

```yaml
- op: derive_column
  name: total_with_tax          # New column name
  expr: amount * 1.1            # Expression
```

### cast

```yaml
- op: cast
  columns:
    id: string
    amount: float64
    created_at: datetime
```

### fill_null

```yaml
- op: fill_null
  columns:
    amount: 0
    status: "unknown"
```

### dedup

```yaml
- op: dedup
  columns: [customer_id, order_id]  # Optional: specific columns
                                    # If omitted, uses all columns
```

### sort

```yaml
- op: sort
  by: [amount, created_at]
  descending: true              # Optional: default false
```

### join

```yaml
- op: join
  right: other_dataset          # Reference to another dataset
  on: [customer_id]             # Join columns
  how: left                     # Optional: inner, left, right, outer
```

### aggregate

```yaml
- op: aggregate
  group_by: [category, region]
  aggs:
    total_sales: sum(amount)
    avg_order: avg(amount)
    order_count: count(*)
```

### union

```yaml
- op: union
  sources: [dataset1, dataset2]  # References to datasets
```

### limit

```yaml
- op: limit
  n: 1000                       # Maximum rows
```

## Check Configuration

### not_null

```yaml
- type: not_null
  columns: [id, name, amount]
```

### unique

```yaml
- type: unique
  columns: [id]                 # Single column
  # OR
  columns: [customer_id, order_id]  # Composite unique
```

### row_count

```yaml
- type: row_count
  min: 1                        # Optional: minimum rows
  max: 1000000                  # Optional: maximum rows
```

### accepted_values

```yaml
- type: accepted_values
  column: status
  values: [pending, active, completed, cancelled]
```

### expression

```yaml
- type: expression
  expr: amount >= 0             # Must be true for all rows
```

## Sink Configuration

### File Sink

```yaml
sink:
  type: file
  path: output/sales.parquet
  format: parquet
  mode: overwrite
```

#### Partitioned Output

```yaml
sink:
  type: file
  path: output/sales/
  format: parquet
  partition_by: [year, month]
```

### Database Sink

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: sales_summary
  mode: truncate
```

## Complete Example

```yaml
name: daily_sales_etl
description: Daily sales aggregation pipeline
engine: duckdb

source:
  type: file
  path: s3://data-lake/raw/sales/${DATE}/*.parquet
  format: parquet

transforms:
  # Clean data
  - op: filter
    predicate: amount > 0 AND status != 'cancelled'

  # Standardize columns
  - op: rename
    mapping:
      order_total: amount
      cust_id: customer_id

  # Add metrics
  - op: derive_column
    name: net_amount
    expr: amount - COALESCE(discount, 0)

  # Aggregate by region
  - op: aggregate
    group_by: [region, category]
    aggs:
      total_sales: sum(net_amount)
      order_count: count(*)
      avg_order: avg(net_amount)

  # Sort for reporting
  - op: sort
    by: [total_sales]
    descending: true

checks:
  - type: not_null
    columns: [region, category, total_sales]
  - type: row_count
    min: 1
  - type: expression
    expr: total_sales >= 0

sink:
  type: file
  path: s3://data-lake/processed/sales_summary/${DATE}/
  format: parquet
  partition_by: [region]
```

## Related

- [Variable Substitution](variables.md) - Use `${VAR}` syntax
- [JSON Schema](json-schema.md) - IDE support
- [Transforms Reference](../transforms/index.md) - Detailed transform docs
