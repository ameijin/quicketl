# Backends

QuickETL supports multiple compute backends through Ibis. Choose the right backend for your workload.

## Available Backends

| Backend | Type | Install | Best For |
|---------|------|---------|----------|
| [DuckDB](local.md#duckdb) | Local | Default | Analytics, small-medium data |
| [Polars](local.md#polars) | Local | Default | Fast DataFrames |
| [DataFusion](local.md#datafusion) | Local | `quicketl[datafusion]` | Arrow-native queries |
| [Spark](distributed.md) | Distributed | `quicketl[spark]` | Large-scale processing |
| [pandas](local.md#pandas) | Local | `quicketl[pandas]` | Legacy compatibility |
| [Snowflake](cloud-warehouses.md#snowflake) | Cloud DW | `quicketl[snowflake]` | Enterprise analytics |
| [BigQuery](cloud-warehouses.md#bigquery) | Cloud DW | `quicketl[bigquery]` | Google Cloud |
| [PostgreSQL](databases.md#postgresql) | Database | `quicketl[postgres]` | Operational data |
| [MySQL](databases.md#mysql) | Database | `quicketl[mysql]` | Web applications |
| [ClickHouse](databases.md#clickhouse) | Database | `quicketl[clickhouse]` | Real-time analytics |

## Selecting a Backend

Specify the backend in your pipeline:

```yaml
engine: duckdb  # or polars, spark, snowflake, etc.
```

Or at runtime:

```bash
quicketl run pipeline.yml --engine polars
```

## Backend Comparison

### Local Backends

For data that fits on a single machine:

| Backend | Speed | Memory | SQL Support |
|---------|-------|--------|-------------|
| DuckDB | Fast | Efficient | Yes |
| Polars | Very Fast | Efficient | Limited |
| DataFusion | Fast | Arrow-native | Yes |
| pandas | Slower | Higher | No |

**Recommendation**: Start with **DuckDB** (default).

### Distributed Backends

For data too large for a single machine:

| Backend | Scale | Cost | Complexity |
|---------|-------|------|------------|
| Spark | Massive | Moderate | Higher |
| Snowflake | Large | Pay-per-query | Lower |
| BigQuery | Large | Pay-per-query | Lower |

**Recommendation**: Use **Spark** for on-premise, **Snowflake/BigQuery** for cloud.

## Backend Features

| Feature | DuckDB | Polars | Spark | Snowflake |
|---------|--------|--------|-------|-----------|
| Local files | Yes | Yes | Yes | No |
| Cloud storage | Yes | Yes | Yes | Yes |
| SQL support | Full | Partial | Full | Full |
| Memory efficiency | High | High | Medium | N/A |
| Parallelism | Multi-core | Multi-core | Distributed | Distributed |

## Checking Availability

List installed backends:

```bash
quicketl info --backends --check
```

Output:

```
Available Backends
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Backend    ┃ Name            ┃ Status         ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ duckdb     │ DuckDB          │ OK             │
│ polars     │ Polars          │ OK             │
│ spark      │ Apache Spark    │ Not installed  │
│ snowflake  │ Snowflake       │ Not installed  │
└────────────┴─────────────────┴────────────────┘
```

## Installation

Install additional backends:

```bash
# Individual backends
pip install quicketl[spark]
pip install quicketl[snowflake]
pip install quicketl[bigquery]

# Multiple backends
pip install quicketl[spark,snowflake,bigquery]

# All backends
pip install quicketl[all]
```

## Backend Parity

QuickETL aims for consistent behavior across backends. The same pipeline should produce identical results regardless of backend:

```yaml
# Works on any backend
transforms:
  - op: filter
    predicate: amount > 0
  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)
```

!!! note "Backend Differences"
    Some edge cases may differ (null handling, floating-point precision). Test important pipelines on your target backend.

## Python API

```python
from quicketl import QuickETLEngine

# DuckDB (default)
engine = QuickETLEngine(backend="duckdb")

# Polars
engine = QuickETLEngine(backend="polars")

# Snowflake
engine = QuickETLEngine(
    backend="snowflake",
    connection_string="snowflake://user:pass@account/db/schema"
)
```

## Choosing Your Backend

### Start with DuckDB

DuckDB is the default because it:

- Requires no setup
- Handles most workloads
- Has excellent SQL support
- Is very fast for analytics

### Consider Alternatives When

| Scenario | Consider |
|----------|----------|
| Need maximum speed on DataFrames | Polars |
| Data doesn't fit in memory | Spark |
| Already using Snowflake/BigQuery | Same warehouse |
| Need database connectivity | PostgreSQL/MySQL |
| Real-time analytics | ClickHouse |

## Next Steps

- [Local Backends](local.md) - DuckDB, Polars, DataFusion, pandas
- [Distributed (Spark)](distributed.md) - Large-scale processing
- [Cloud Warehouses](cloud-warehouses.md) - Snowflake, BigQuery
- [Databases](databases.md) - PostgreSQL, MySQL, ClickHouse
