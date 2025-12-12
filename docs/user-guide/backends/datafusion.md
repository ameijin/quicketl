# DataFusion Backend

Apache DataFusion is a fast, extensible query engine written in Rust. QuickETL uses DataFusion via Ibis for efficient in-memory analytics.

## Installation

```bash
pip install quicketl[datafusion]
# or
uv add quicketl[datafusion]
```

## When to Use DataFusion

**Ideal for:**

- Rust-powered performance
- SQL-based analytics on files
- Lightweight embedded analytics
- When you need both SQL and DataFrame APIs

**Consider alternatives when:**

- Need database connectivity (use DuckDB)
- Distributed processing required (use Spark)
- Maximum ecosystem compatibility needed

## Configuration

### Basic Usage

```yaml
name: datafusion_pipeline
engine: datafusion

source:
  type: file
  path: data/events.parquet
  format: parquet

transforms:
  - op: filter
    predicate: event_date >= '2025-01-01'
  - op: aggregate
    group_by: [event_type]
    aggregations:
      count: count(*)

sink:
  type: file
  path: output/summary.parquet
  format: parquet
```

### CLI Override

```bash
quicketl run pipeline.yml --engine datafusion
```

## Performance Characteristics

| Metric | Performance |
|--------|-------------|
| Startup time | ~50ms |
| Memory efficiency | Excellent |
| Parallelism | Multi-threaded |
| SQL support | Full |

## Supported Features

### Transforms

| Transform | Support | Notes |
|-----------|---------|-------|
| select | Full | |
| rename | Full | |
| filter | Full | Predicate pushdown |
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

| QuickETL Type | DataFusion Type |
|-----------|-----------------|
| string | Utf8 |
| int | Int64 |
| float | Float64 |
| bool | Boolean |
| date | Date32 |
| timestamp | Timestamp |
| decimal | Decimal128 |

## File Format Support

DataFusion excels at processing various file formats:

### Parquet

```yaml
source:
  type: file
  path: data/*.parquet
  format: parquet
```

### CSV

```yaml
source:
  type: file
  path: data/input.csv
  format: csv
  options:
    has_header: true
    delimiter: ","
```

### JSON

```yaml
source:
  type: file
  path: data/records.json
  format: json
```

## Optimization Tips

### 1. Use Parquet Format

DataFusion is highly optimized for Parquet:

```yaml
source:
  type: file
  path: data/input.parquet
  format: parquet
```

### 2. Enable Predicate Pushdown

Filters are automatically pushed to file readers:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'  # Pushed to Parquet reader
```

### 3. Partition Your Data

Organize data by common filter columns:

```
data/
  year=2024/
    month=01/
      data.parquet
    month=02/
      data.parquet
  year=2025/
    month=01/
      data.parquet
```

```yaml
source:
  type: file
  path: data/year=2025/**/*.parquet
  format: parquet
```

## Example: Analytics Pipeline

```yaml
name: web_analytics
description: Process web analytics events
engine: datafusion

source:
  type: file
  path: data/events/*.parquet
  format: parquet

transforms:
  # Filter to relevant date range
  - op: filter
    predicate: event_date >= '2025-01-01'

  # Select needed columns
  - op: select
    columns: [user_id, event_type, page_url, event_time]

  # Extract page path
  - op: derive_column
    name: page_path
    expr: split_part(page_url, '?', 1)

  # Aggregate by page and event
  - op: aggregate
    group_by: [page_path, event_type]
    aggregations:
      pageviews: count(*)
      unique_users: count(distinct user_id)

  # Sort by pageviews
  - op: sort
    by:
      - column: pageviews
        order: desc

sink:
  type: file
  path: output/page_analytics.parquet
  format: parquet
```

## SQL Expressions

DataFusion supports standard SQL expressions:

```yaml
transforms:
  - op: derive_column
    name: full_name
    expr: concat(first_name, ' ', last_name)

  - op: derive_column
    name: year
    expr: extract(year from event_date)

  - op: filter
    predicate: |
      amount > 100
      AND status IN ('completed', 'shipped')
      AND created_at >= '2025-01-01'
```

## Comparison with Other Backends

| Feature | DataFusion | DuckDB | Polars |
|---------|------------|--------|--------|
| Language | Rust | C++ | Rust |
| SQL support | Full | Full | Via Ibis |
| DB connectivity | No | Yes | No |
| Memory efficiency | Excellent | Excellent | Excellent |
| Arrow native | Yes | Yes | Yes |

## Limitations

1. **No Database Connectivity**: File-based only
2. **Ecosystem**: Smaller than DuckDB
3. **Extensions**: Fewer built-in extensions

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'datafusion'
```

**Solution**:
```bash
pip install quicketl[datafusion]
```

### File Not Found

```
Error: No files found matching pattern
```

**Solution**: Verify file path and glob pattern:
```bash
ls data/*.parquet
```

### Memory Issues

For large datasets:
1. Use Parquet format
2. Filter early in pipeline
3. Select only needed columns

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [DuckDB](duckdb.md) - Alternative with DB support
- [Polars](polars.md) - Alternative Rust-based engine
