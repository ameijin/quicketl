# Polars Backend

Polars is a blazing fast DataFrame library written in Rust. ETLX uses Polars via Ibis for excellent single-machine performance.

## Installation

```bash
pip install etlx[polars]
# or
uv add etlx[polars]
```

## When to Use Polars

**Ideal for:**

- Large files that don't fit in memory (streaming support)
- CPU-intensive transformations
- When you need Rust-level performance
- Single-machine workloads with millions of rows

**Consider alternatives when:**

- You need SQL features like window functions (use DuckDB)
- Distributed processing is required (use Spark)
- Working with databases directly (use DuckDB)

## Configuration

### Basic Usage

```yaml
name: polars_pipeline
engine: polars

source:
  type: file
  path: data/large_dataset.parquet
  format: parquet

transforms:
  - op: filter
    predicate: amount > 100
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)

sink:
  type: file
  path: output/results.parquet
  format: parquet
```

### CLI Override

```bash
etlx run pipeline.yml --engine polars
```

## Performance Characteristics

| Metric | Performance |
|--------|-------------|
| Startup time | ~100ms |
| Memory efficiency | Excellent (lazy evaluation) |
| Parallelism | Multi-threaded |
| Streaming | Supported |

## Supported Features

### Transforms

| Transform | Support | Notes |
|-----------|---------|-------|
| select | Full | |
| rename | Full | |
| filter | Full | |
| derive_column | Full | |
| cast | Full | |
| fill_null | Full | |
| dedup | Full | |
| sort | Full | |
| join | Full | |
| aggregate | Full | |
| union | Full | |
| limit | Full | |

### Data Types

| ETLX Type | Polars Type |
|-----------|-------------|
| string | Utf8 |
| int | Int64 |
| float | Float64 |
| bool | Boolean |
| date | Date |
| timestamp | Datetime |
| decimal | Decimal |

## Optimization Tips

### 1. Use Parquet Format

Polars is highly optimized for Parquet:

```yaml
source:
  type: file
  path: data/input.parquet
  format: parquet

sink:
  type: file
  path: output/results.parquet
  format: parquet
```

### 2. Filter Early

Push filters as early as possible in your pipeline:

```yaml
transforms:
  # Filter first to reduce data volume
  - op: filter
    predicate: date >= '2025-01-01'

  # Then do expensive operations
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

### 3. Select Only Needed Columns

```yaml
transforms:
  - op: select
    columns: [id, name, amount]  # Reduces memory usage
```

## Streaming Large Files

Polars can process files larger than memory using streaming:

```yaml
name: stream_large_file
engine: polars

source:
  type: file
  path: data/huge_file.csv
  format: csv

transforms:
  - op: filter
    predicate: status = 'active'
  - op: aggregate
    group_by: [region]
    aggregations:
      count: count(*)

sink:
  type: file
  path: output/summary.parquet
  format: parquet
```

## Limitations

1. **SQL Functions**: Some advanced SQL functions may not be available
2. **Database Connections**: Less efficient than DuckDB for direct DB queries
3. **Window Functions**: Limited compared to SQL-based backends

## Comparison with DuckDB

| Feature | Polars | DuckDB |
|---------|--------|--------|
| In-memory performance | Excellent | Excellent |
| SQL support | Via Ibis | Native |
| Streaming | Built-in | Limited |
| Database connectivity | Via connectors | Native |
| Memory efficiency | Excellent | Good |

## Example: High-Performance Analytics

```yaml
name: analytics_pipeline
description: Process large analytics dataset
engine: polars

source:
  type: file
  path: data/events.parquet
  format: parquet

transforms:
  # Filter to relevant date range
  - op: filter
    predicate: event_date >= '2025-01-01'

  # Select needed columns
  - op: select
    columns: [user_id, event_type, value, event_date]

  # Aggregate by user and event type
  - op: aggregate
    group_by: [user_id, event_type]
    aggregations:
      total_value: sum(value)
      event_count: count(*)

  # Filter significant users
  - op: filter
    predicate: event_count >= 10

sink:
  type: file
  path: output/user_analytics.parquet
  format: parquet
```

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'polars'
```

**Solution**: Install Polars extra:
```bash
pip install etlx[polars]
```

### Memory Issues

If you encounter memory errors with large files:

1. Use Parquet format (columnar, efficient)
2. Filter early in the pipeline
3. Select only needed columns
4. Consider using streaming mode

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [DuckDB](duckdb.md) - Alternative for SQL-heavy workloads
- [Performance Best Practices](../../best-practices/performance.md)
