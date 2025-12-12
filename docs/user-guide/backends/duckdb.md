# DuckDB

DuckDB is the default backend in QuickETL. It's a fast, embedded analytical database that requires no setup.

## Overview

- **Type**: Embedded analytical database
- **Installation**: Included by default
- **Best For**: Analytics, small-to-medium datasets, local development

## Configuration

```yaml
engine: duckdb
```

No additional configuration required for local files.

## Features

| Feature | Supported |
|---------|-----------|
| Local files | Yes |
| Cloud storage | Yes (S3, GCS, Azure) |
| SQL support | Full |
| Parallel execution | Yes |
| Memory efficiency | High |

## File Support

DuckDB can read/write:

- Parquet (fastest)
- CSV
- JSON

```yaml
source:
  type: file
  path: data.parquet
  format: parquet
```

## Cloud Storage

DuckDB supports cloud storage directly:

```yaml
source:
  type: file
  path: s3://bucket/data.parquet

sink:
  type: file
  path: s3://bucket/output/
```

## Performance Tips

### Use Parquet

Parquet is significantly faster than CSV:

```yaml
# Fast
format: parquet

# Slower
format: csv
```

### Filter Early

DuckDB can push filters down:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'
  # Further transforms run on filtered data
```

### Select Columns

With Parquet, only selected columns are read:

```yaml
transforms:
  - op: select
    columns: [id, amount]
```

## Memory Management

DuckDB is memory-efficient but for very large files:

```python
# Configure memory limit
engine = QuickETLEngine(
    backend="duckdb",
    memory_limit="4GB"
)
```

## Python API

```python
from quicketl import QuickETLEngine

engine = QuickETLEngine(backend="duckdb")

# Read and process
table = engine.read_file("data.parquet", "parquet")
filtered = engine.filter(table, "amount > 100")
result = engine.to_pandas(filtered)
```

## When to Use

**Good for:**

- Local development
- Small-to-medium datasets (up to ~100GB)
- Analytics and reporting
- Quick data exploration

**Consider alternatives for:**

- Very large datasets → Spark
- Existing cloud warehouse → Snowflake/BigQuery
- Real-time streaming → ClickHouse

## Related

- [Backends Overview](index.md)
- [Polars](polars.md) - Alternative local backend
- [Spark](spark.md) - For larger datasets
