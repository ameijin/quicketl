# ClickHouse Backend

ClickHouse is a column-oriented OLAP database designed for real-time analytics. ETLX supports ClickHouse for high-performance analytical workloads.

## Installation

```bash
pip install etlx[clickhouse]
# or
uv add etlx[clickhouse]
```

## When to Use ClickHouse

**Ideal for:**

- Real-time analytics on large datasets
- Time-series data
- Log and event analytics
- High-speed aggregations
- Append-heavy workloads

**Consider alternatives when:**

- ACID transactions needed (use PostgreSQL)
- Frequent updates/deletes
- Small datasets (use DuckDB)

## Configuration

### Connection Setup

```bash
export CLICKHOUSE_HOST=localhost
export CLICKHOUSE_PORT=8123
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
export CLICKHOUSE_DATABASE=analytics
```

### Using `.env`

```
CLICKHOUSE_HOST=clickhouse.example.com
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=etlx_user
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
CLICKHOUSE_DATABASE=analytics
```

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
    group_by: [event_type, toDate(event_time)]
    aggregations:
      event_count: count(*)
      unique_users: uniqExact(user_id)

sink:
  type: database
  connection: clickhouse
  table: event_summary
  mode: append
```

## Supported Features

### Transforms

| Transform | Support | ClickHouse SQL |
|-----------|---------|----------------|
| select | Full | `SELECT` |
| rename | Full | `AS alias` |
| filter | Full | `WHERE` / `PREWHERE` |
| derive_column | Full | Expressions |
| cast | Full | `CAST()` / `toType()` |
| fill_null | Full | `COALESCE()` / `ifNull()` |
| dedup | Full | `DISTINCT` |
| sort | Full | `ORDER BY` |
| join | Full | `JOIN` |
| aggregate | Full | `GROUP BY` |
| union | Full | `UNION ALL` |
| limit | Full | `LIMIT` |

### Data Types

| ETLX Type | ClickHouse Type |
|-----------|-----------------|
| string | String |
| int | Int64 |
| float | Float64 |
| bool | UInt8 |
| date | Date |
| timestamp | DateTime |
| decimal | Decimal |

## Reading Data

### From Tables

```yaml
source:
  type: database
  connection: clickhouse
  table: database.table_name
```

### From Queries

```yaml
source:
  type: database
  connection: clickhouse
  query: |
    SELECT
      toDate(event_time) as event_date,
      event_type,
      user_id,
      properties
    FROM events
    WHERE event_date >= today() - 7
```

## Writing Data

### Append Mode (Recommended)

ClickHouse is optimized for append-only writes:

```yaml
sink:
  type: database
  connection: clickhouse
  table: event_summary
  mode: append
```

### Replace Mode

Use with caution (drops and recreates):

```yaml
sink:
  type: database
  connection: clickhouse
  table: output_table
  mode: replace
```

## Performance Optimization

### 1. Use Appropriate Table Engines

**MergeTree** for most use cases:
```sql
CREATE TABLE events (
    event_date Date,
    event_time DateTime,
    user_id UInt64,
    event_type String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);
```

### 2. Leverage PREWHERE

Filter on indexed columns:

```yaml
transforms:
  - op: filter
    predicate: event_date >= '2025-01-01'  # Uses partition pruning
```

### 3. Use Materialized Views

For common aggregations:

```sql
CREATE MATERIALIZED VIEW event_counts
ENGINE = SummingMergeTree()
ORDER BY (event_date, event_type)
AS SELECT
    toDate(event_time) as event_date,
    event_type,
    count() as event_count
FROM events
GROUP BY event_date, event_type;
```

### 4. Batch Inserts

ClickHouse performs best with large batches:

```yaml
sink:
  type: database
  connection: clickhouse
  table: events
  options:
    batch_size: 100000
```

## Example: Real-Time Analytics

```yaml
name: realtime_dashboard
description: Compute metrics for real-time dashboard
engine: clickhouse

source:
  type: database
  connection: clickhouse
  query: |
    SELECT
      toStartOfMinute(event_time) as minute,
      event_type,
      countIf(event_type = 'pageview') as pageviews,
      countIf(event_type = 'click') as clicks,
      uniqExact(user_id) as unique_users
    FROM events
    WHERE event_time >= now() - INTERVAL 1 HOUR
    GROUP BY minute, event_type
    ORDER BY minute DESC

transforms:
  - op: derive_column
    name: click_rate
    expr: clicks / nullif(pageviews, 0)

checks:
  - check: not_null
    columns: [minute, event_type]

sink:
  type: database
  connection: clickhouse
  table: dashboard_metrics
  mode: append
```

## ClickHouse-Specific Functions

ETLX supports ClickHouse-specific functions in expressions:

```yaml
transforms:
  - op: derive_column
    name: hour
    expr: toHour(event_time)

  - op: derive_column
    name: day_of_week
    expr: toDayOfWeek(event_date)

  - op: aggregate
    group_by: [event_type]
    aggregations:
      approx_unique: uniq(user_id)
      exact_unique: uniqExact(user_id)
      percentile_95: quantile(0.95)(response_time)
```

## Limitations

1. **No Updates**: Designed for append-only (use ReplacingMergeTree for updates)
2. **No Transactions**: No ACID guarantees
3. **Join Performance**: Large joins can be slow
4. **Memory Usage**: Aggregations load data into memory

## Troubleshooting

### Connection Failed

```
clickhouse_driver.errors.NetworkError: Connection refused
```

**Solutions**:
1. Verify ClickHouse is running
2. Check HTTP port (default 8123) or native port (9000)
3. Verify network connectivity

### Memory Limit Exceeded

```
Memory limit exceeded
```

**Solutions**:
1. Add `LIMIT` to queries
2. Use approximate functions (`uniq` instead of `uniqExact`)
3. Increase memory limits:
```sql
SET max_memory_usage = 20000000000;
```

### Too Many Parts

```
Too many parts in table
```

**Solution**: Wait for merges or optimize:
```sql
OPTIMIZE TABLE events FINAL;
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Database Sources](../io/database-sources.md) - Database configuration
- [Performance Best Practices](../../best-practices/performance.md)
