# Database Backends

QuickETL supports traditional databases as both sources and sinks. Use these backends when your data lives in operational databases.

## Quick Comparison

| Database | Type | Best For |
|----------|------|----------|
| **PostgreSQL** | OLTP | General purpose, complex SQL |
| **MySQL** | OLTP | Web applications, compatibility |
| **ClickHouse** | OLAP | Real-time analytics, time-series |

---

## PostgreSQL {#postgresql}

PostgreSQL is a powerful open-source relational database with excellent SQL support.

### Installation

```bash
pip install quicketl[postgres]
```

### Configuration

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=quicketl_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_DATABASE=analytics
```

Or connection URL:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/analytics
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

### Write Modes

```yaml
# Replace (TRUNCATE + INSERT)
sink:
  mode: replace

# Append
sink:
  mode: append

# Upsert (INSERT ... ON CONFLICT DO UPDATE)
sink:
  mode: upsert
  upsert_keys: [id]
```

### Reading with CTEs

```yaml
source:
  type: database
  connection: postgres
  query: |
    WITH recent_orders AS (
      SELECT * FROM orders
      WHERE created_at >= NOW() - INTERVAL '7 days'
    )
    SELECT * FROM recent_orders
```

### Features

- **Full SQL**: CTEs, window functions, JSON operators
- **Extensions**: PostGIS (spatial), TimescaleDB (time-series)
- **Transactions**: Full ACID compliance

### Troubleshooting

**Connection Refused**: Verify PostgreSQL is running, check `pg_hba.conf`

**Permission Denied**:
```sql
GRANT SELECT ON orders TO quicketl_user;
GRANT INSERT, UPDATE ON processed_orders TO quicketl_user;
```

**SSL Required**:
```bash
export POSTGRES_SSLMODE=require
```

---

## MySQL {#mysql}

MySQL is a widely-used database, common in web applications.

### Installation

```bash
pip install quicketl[mysql]
```

### Configuration

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=quicketl_user
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=analytics
```

### Basic Pipeline

```yaml
name: mysql_etl
engine: mysql

source:
  type: database
  connection: mysql
  table: raw_transactions

transforms:
  - op: filter
    predicate: transaction_date >= '2025-01-01'
  - op: aggregate
    group_by: [customer_id]
    aggs:
      total_amount: sum(amount)

sink:
  type: database
  connection: mysql
  table: customer_totals
  mode: replace
```

### Write Modes

```yaml
# Replace
sink:
  mode: replace

# Append
sink:
  mode: append

# Upsert (INSERT ... ON DUPLICATE KEY UPDATE)
sink:
  mode: upsert
  upsert_keys: [id]
```

### Limitations

- Window functions: Limited compared to PostgreSQL
- CTEs: Supported in MySQL 8.0+ only

### Troubleshooting

**Access Denied**:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON database.* TO 'quicketl_user'@'%';
FLUSH PRIVILEGES;
```

**Character Set Issues**:
```bash
export MYSQL_CHARSET=utf8mb4
```

---

## ClickHouse {#clickhouse}

ClickHouse is a column-oriented OLAP database designed for real-time analytics.

### Installation

```bash
pip install quicketl[clickhouse]
```

### Configuration

```bash
export CLICKHOUSE_HOST=localhost
export CLICKHOUSE_PORT=8123
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
export CLICKHOUSE_DATABASE=analytics
```

### When to Use ClickHouse

- Real-time analytics on large datasets
- Time-series data
- Log and event analytics
- High-speed aggregations
- Append-heavy workloads

### Basic Pipeline

```yaml
name: clickhouse_analytics
engine: clickhouse

source:
  type: database
  connection: clickhouse
  table: events

transforms:
  - op: filter
    predicate: event_date >= '2025-01-01'
  - op: aggregate
    group_by: [event_type]
    aggs:
      event_count: count(*)
      unique_users: uniqExact(user_id)

sink:
  type: database
  connection: clickhouse
  table: event_summary
  mode: append
```

### Write Modes

ClickHouse is optimized for append-only writes:

```yaml
# Append (recommended)
sink:
  mode: append
  options:
    batch_size: 100000  # Large batches are efficient
```

### ClickHouse-Specific Functions

```yaml
transforms:
  - op: derive_column
    name: hour
    expr: toHour(event_time)

  - op: aggregate
    group_by: [event_type]
    aggs:
      approx_unique: uniq(user_id)  # Approximate, fast
      exact_unique: uniqExact(user_id)  # Exact, slower
      p95_response: quantile(0.95)(response_time)
```

### Performance Tips

1. **Use MergeTree engine** with appropriate partitioning
2. **Filter on indexed columns** (PREWHERE optimization)
3. **Batch inserts** - ClickHouse performs best with large batches
4. **Use materialized views** for common aggregations

### Limitations

- **No Updates**: Designed for append-only (use ReplacingMergeTree for updates)
- **No Transactions**: No ACID guarantees
- **Join Performance**: Large joins can be slow

### Troubleshooting

**Memory Limit Exceeded**: Add `LIMIT`, use approximate functions, or increase limits:
```sql
SET max_memory_usage = 20000000000;
```

**Too Many Parts**:
```sql
OPTIMIZE TABLE events FINAL;
```

---

## Choosing a Database Backend

| Scenario | Recommendation |
|----------|----------------|
| General purpose OLTP | PostgreSQL |
| Web application database | MySQL |
| Real-time analytics | ClickHouse |
| Complex SQL (CTEs, window functions) | PostgreSQL |
| Time-series data | ClickHouse or TimescaleDB |
| High-speed aggregations | ClickHouse |

## Related

- [Local Backends](local.md) - DuckDB, Polars for files
- [Cloud Warehouses](cloud-warehouses.md) - Snowflake, BigQuery
