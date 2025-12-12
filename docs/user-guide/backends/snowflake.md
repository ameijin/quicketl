# Snowflake Backend

Snowflake is a cloud-native data warehouse. ETLX can push transformations directly to Snowflake for efficient in-warehouse processing.

## Installation

```bash
pip install quicketl[snowflake]
# or
uv add quicketl[snowflake]
```

## When to Use Snowflake

**Ideal for:**

- Data already in Snowflake
- Complex SQL transformations
- Scalable compute without infrastructure management
- Enterprise data warehouse workloads

**Consider alternatives when:**

- Data is local files (use DuckDB)
- Cost is a primary concern
- Real-time processing needed

## Configuration

### Connection Setup

Set environment variables:

```bash
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=etlx_user
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_DATABASE=analytics
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_WAREHOUSE=compute_wh
```

Or use `.env`:

```
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=etlx_user
SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
SNOWFLAKE_DATABASE=analytics
SNOWFLAKE_SCHEMA=public
SNOWFLAKE_WAREHOUSE=compute_wh
SNOWFLAKE_ROLE=analyst_role
```

### Basic Pipeline

```yaml
name: snowflake_etl
engine: snowflake

source:
  type: database
  connection: snowflake
  table: raw_sales

transforms:
  - op: filter
    predicate: sale_date >= '2025-01-01'
  - op: aggregate
    group_by: [region, product_category]
    aggregations:
      total_revenue: sum(amount)
      order_count: count(*)

sink:
  type: database
  connection: snowflake
  table: sales_summary
  mode: replace
```

### Key-Pair Authentication

For production, use key-pair authentication:

```bash
export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/rsa_key.p8
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
```

```yaml
source:
  type: database
  connection: snowflake
  auth: key_pair
  table: source_table
```

## Warehouse Configuration

### Specify Warehouse Size

Use warehouse parameters for compute scaling:

```bash
# Use larger warehouse for heavy transformations
export SNOWFLAKE_WAREHOUSE=compute_xl
```

### Auto-Suspend

Configure warehouse to auto-suspend:

```sql
ALTER WAREHOUSE compute_wh SET AUTO_SUSPEND = 60;
```

## Supported Features

### Transforms

All transforms are pushed to Snowflake SQL:

| Transform | Support | Snowflake SQL |
|-----------|---------|---------------|
| select | Full | `SELECT columns` |
| rename | Full | `AS alias` |
| filter | Full | `WHERE` |
| derive_column | Full | Expressions |
| cast | Full | `CAST()` / `::` |
| fill_null | Full | `COALESCE()` / `IFNULL()` |
| dedup | Full | `QUALIFY ROW_NUMBER()` |
| sort | Full | `ORDER BY` |
| join | Full | `JOIN` |
| aggregate | Full | `GROUP BY` |
| union | Full | `UNION ALL` |
| limit | Full | `LIMIT` |

### Data Types

| ETLX Type | Snowflake Type |
|-----------|----------------|
| string | VARCHAR |
| int | INTEGER |
| float | FLOAT |
| bool | BOOLEAN |
| date | DATE |
| timestamp | TIMESTAMP_NTZ |
| decimal | NUMBER(38,9) |

## Reading from Stages

Load data from Snowflake stages:

```yaml
source:
  type: database
  connection: snowflake
  query: |
    SELECT * FROM @my_stage/data/
    (FILE_FORMAT => 'my_csv_format')
```

## Writing to Tables

### Replace Mode

```yaml
sink:
  type: database
  connection: snowflake
  table: output_table
  mode: replace  # TRUNCATE + INSERT
```

### Append Mode

```yaml
sink:
  type: database
  connection: snowflake
  table: output_table
  mode: append  # INSERT only
```

### Merge Mode

```yaml
sink:
  type: database
  connection: snowflake
  table: output_table
  mode: merge
  merge_keys: [id]
```

## Cost Optimization

### 1. Use Appropriate Warehouse Size

```yaml
# Small warehouse for light transformations
# XS: 1 credit/hour
# S:  2 credits/hour
# M:  4 credits/hour
# L:  8 credits/hour
```

### 2. Filter Early

Reduce data scanned:

```yaml
transforms:
  # Filter first to reduce compute
  - op: filter
    predicate: date >= '2025-01-01'

  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

### 3. Use Clustering Keys

For large tables, define clustering:

```sql
ALTER TABLE sales CLUSTER BY (date, region);
```

## Example: Data Warehouse ETL

```yaml
name: warehouse_etl
description: Transform raw data into analytics tables
engine: snowflake

source:
  type: database
  connection: snowflake
  query: |
    SELECT
      o.order_id,
      o.customer_id,
      o.order_date,
      oi.product_id,
      oi.quantity,
      oi.unit_price,
      p.category,
      c.region
    FROM raw.orders o
    JOIN raw.order_items oi ON o.order_id = oi.order_id
    JOIN raw.products p ON oi.product_id = p.product_id
    JOIN raw.customers c ON o.customer_id = c.customer_id
    WHERE o.order_date >= DATEADD(day, -30, CURRENT_DATE())

transforms:
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  - op: aggregate
    group_by: [region, category, order_date]
    aggregations:
      total_revenue: sum(line_total)
      total_orders: count(distinct order_id)
      total_items: sum(quantity)

checks:
  - check: not_null
    columns: [region, category, total_revenue]
  - check: row_count
    min: 1

sink:
  type: database
  connection: snowflake
  table: analytics.daily_sales
  mode: merge
  merge_keys: [region, category, order_date]
```

## Limitations

1. **Cost**: Pay per compute second
2. **Latency**: Connection overhead (~1-2s)
3. **Local Data**: Must stage local files first
4. **Concurrent Queries**: Subject to warehouse queueing

## Troubleshooting

### Connection Failed

```
snowflake.connector.errors.DatabaseError: Connection failed
```

**Solutions**:
1. Verify account identifier format: `account.region`
2. Check network connectivity
3. Verify credentials

### Warehouse Suspended

```
Warehouse 'COMPUTE_WH' is suspended
```

**Solution**: Warehouse auto-resumes, or manually:
```sql
ALTER WAREHOUSE compute_wh RESUME;
```

### Permission Denied

```
SQL access control error
```

**Solution**: Grant necessary permissions:
```sql
GRANT USAGE ON WAREHOUSE compute_wh TO ROLE etlx_role;
GRANT SELECT ON TABLE raw.sales TO ROLE etlx_role;
GRANT INSERT ON TABLE analytics.summary TO ROLE etlx_role;
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Database Sources](../io/database-sources.md) - Database configuration
- [Database Sinks](../io/database-sinks.md) - Writing to databases
