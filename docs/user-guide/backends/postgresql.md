# PostgreSQL Backend

PostgreSQL is a powerful open-source relational database. QuickETL can execute transformations directly in PostgreSQL or use it as a source/sink.

## Installation

```bash
pip install quicketl[postgres]
# or
uv add quicketl[postgres]
```

## When to Use PostgreSQL

**Ideal for:**

- Data already in PostgreSQL
- ACID-compliant transactions needed
- Complex SQL with CTEs, window functions
- Integration with existing PostgreSQL infrastructure

**Consider alternatives when:**

- Analytics on large datasets (use DuckDB or columnar DBs)
- File-based processing
- No existing PostgreSQL infrastructure

## Configuration

### Connection Setup

Set environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=quicketl_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_DATABASE=analytics
```

Or use a connection URL:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/analytics
```

### Using `.env`

```
POSTGRES_HOST=db.example.com
POSTGRES_PORT=5432
POSTGRES_USER=quicketl_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DATABASE=analytics
POSTGRES_SSLMODE=require
```

### Basic Pipeline

```yaml
name: postgres_etl
engine: postgres

source:
  type: database
  connection: postgres
  table: raw_orders

transforms:
  - op: filter
    predicate: order_date >= '2025-01-01'
  - op: derive_column
    name: order_total
    expr: quantity * unit_price

sink:
  type: database
  connection: postgres
  table: processed_orders
  mode: replace
```

## Connection Options

### SSL Configuration

```bash
export POSTGRES_SSLMODE=require
export POSTGRES_SSLROOTCERT=/path/to/ca.crt
export POSTGRES_SSLCERT=/path/to/client.crt
export POSTGRES_SSLKEY=/path/to/client.key
```

### Connection Pooling

For production, use connection pooling:

```bash
# With PgBouncer
export POSTGRES_HOST=pgbouncer.example.com
export POSTGRES_PORT=6432
```

## Supported Features

### Transforms

| Transform | Support | PostgreSQL SQL |
|-----------|---------|----------------|
| select | Full | `SELECT` |
| rename | Full | `AS alias` |
| filter | Full | `WHERE` |
| derive_column | Full | Expressions |
| cast | Full | `CAST()` / `::` |
| fill_null | Full | `COALESCE()` |
| dedup | Full | `DISTINCT ON` |
| sort | Full | `ORDER BY` |
| join | Full | `JOIN` |
| aggregate | Full | `GROUP BY` |
| union | Full | `UNION ALL` |
| limit | Full | `LIMIT` |

### Data Types

| QuickETL Type | PostgreSQL Type |
|-----------|-----------------|
| string | TEXT / VARCHAR |
| int | INTEGER / BIGINT |
| float | DOUBLE PRECISION |
| bool | BOOLEAN |
| date | DATE |
| timestamp | TIMESTAMP |
| decimal | NUMERIC |

## Reading Data

### From Tables

```yaml
source:
  type: database
  connection: postgres
  table: schema.table_name
```

### From Queries

```yaml
source:
  type: database
  connection: postgres
  query: |
    SELECT o.*, c.name as customer_name
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE o.created_at >= NOW() - INTERVAL '30 days'
```

### With CTEs

```yaml
source:
  type: database
  connection: postgres
  query: |
    WITH recent_orders AS (
      SELECT * FROM orders
      WHERE created_at >= NOW() - INTERVAL '7 days'
    ),
    order_totals AS (
      SELECT customer_id, SUM(amount) as total
      FROM recent_orders
      GROUP BY customer_id
    )
    SELECT * FROM order_totals
```

## Writing Data

### Replace Mode

```yaml
sink:
  type: database
  connection: postgres
  table: output_table
  mode: replace  # TRUNCATE + INSERT
```

### Append Mode

```yaml
sink:
  type: database
  connection: postgres
  table: output_table
  mode: append  # INSERT only
```

### Upsert Mode

```yaml
sink:
  type: database
  connection: postgres
  table: output_table
  mode: upsert
  upsert_keys: [id]
```

Uses `INSERT ... ON CONFLICT DO UPDATE`.

## Performance Optimization

### 1. Index Your Tables

```sql
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
```

### 2. Use EXPLAIN ANALYZE

Test your queries:

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE order_date >= '2025-01-01';
```

### 3. Partition Large Tables

```sql
CREATE TABLE orders (
  id SERIAL,
  order_date DATE,
  amount NUMERIC
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2025_q1 PARTITION OF orders
  FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

### 4. Batch Inserts

For large writes, data is batched automatically. Configure batch size:

```yaml
sink:
  type: database
  connection: postgres
  table: output_table
  options:
    batch_size: 10000
```

## Example: Data Warehouse Load

```yaml
name: warehouse_load
description: Load transformed data into warehouse
engine: postgres

source:
  type: database
  connection: postgres
  query: |
    SELECT
      o.id,
      o.customer_id,
      c.name as customer_name,
      c.region,
      o.order_date,
      o.amount,
      o.status
    FROM staging.orders o
    JOIN staging.customers c ON o.customer_id = c.id
    WHERE o.processed = false

transforms:
  - op: filter
    predicate: status = 'completed'

  - op: derive_column
    name: order_month
    expr: date_trunc('month', order_date)

  - op: derive_column
    name: amount_with_tax
    expr: amount * 1.1

checks:
  - check: not_null
    columns: [id, customer_id, amount]
  - check: unique
    columns: [id]

sink:
  type: database
  connection: postgres
  table: warehouse.fact_orders
  mode: append
```

## Using PostgreSQL Extensions

### PostGIS (Spatial)

```yaml
source:
  type: database
  connection: postgres
  query: |
    SELECT id, name, ST_AsText(location) as location_wkt
    FROM stores
    WHERE ST_DWithin(location, ST_MakePoint(-122.4, 37.8), 10000)
```

### TimescaleDB (Time Series)

```yaml
source:
  type: database
  connection: postgres
  query: |
    SELECT time_bucket('1 hour', timestamp) as hour,
           avg(temperature) as avg_temp
    FROM sensor_data
    WHERE timestamp >= NOW() - INTERVAL '24 hours'
    GROUP BY hour
```

## Limitations

1. **Performance**: Row-based storage less efficient for analytics
2. **Scale**: Single-node limits
3. **Concurrent Writes**: Lock contention on heavy writes

## Troubleshooting

### Connection Refused

```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:
1. Verify PostgreSQL is running
2. Check host and port
3. Verify firewall rules
4. Check `pg_hba.conf` allows connections

### Permission Denied

```
permission denied for table orders
```

**Solution**:
```sql
GRANT SELECT ON orders TO quicketl_user;
GRANT INSERT, UPDATE ON processed_orders TO quicketl_user;
```

### SSL Required

```
FATAL: no pg_hba.conf entry for host
```

**Solution**:
```bash
export POSTGRES_SSLMODE=require
```

### Timeout

```
canceling statement due to statement timeout
```

**Solution**: Increase timeout:
```sql
SET statement_timeout = '300s';
```

Or configure in connection:
```bash
export POSTGRES_OPTIONS="-c statement_timeout=300s"
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Database Sources](../io/database-sources.md) - Database configuration
- [Database Sinks](../io/database-sinks.md) - Writing to databases
