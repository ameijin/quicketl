# Performance Best Practices

Optimize QuickETL pipeline execution for speed and efficiency.

## Backend Selection

Choose the right backend for your workload:

| Scenario | Recommended Backend |
|----------|---------------------|
| Local files < 1GB | DuckDB |
| Local files 1-10GB | DuckDB or Polars |
| Local files > 10GB | Polars (streaming) |
| Distributed processing | Spark |
| Data in warehouse | Snowflake/BigQuery |
| Quick prototyping | DuckDB |

### Quick Comparison

```bash
# Test different backends
time quicketl run pipeline.yml --engine duckdb
time quicketl run pipeline.yml --engine polars
```

## File Format Optimization

### Use Parquet

Parquet is significantly faster than CSV:

```yaml
# Slow: CSV
source:
  type: file
  path: data/input.csv
  format: csv

# Fast: Parquet
source:
  type: file
  path: data/input.parquet
  format: parquet
```

**Why Parquet is faster:**

- Columnar storage (read only needed columns)
- Built-in compression
- Type preservation (no parsing)
- Predicate pushdown

### Convert CSV to Parquet

One-time conversion:

```yaml
name: convert_to_parquet
source:
  type: file
  path: data/large_file.csv
  format: csv
sink:
  type: file
  path: data/large_file.parquet
  format: parquet
```

## Transform Optimization

### 1. Filter Early

Reduce data volume before expensive operations:

```yaml
transforms:
  # Good: Filter first
  - op: filter
    predicate: date >= '2025-01-01' AND status = 'active'

  - op: join  # Joins fewer rows
    right: ...

  - op: aggregate  # Aggregates fewer rows
    group_by: ...
```

**Impact**: Can reduce processing time by 10-100x.

### 2. Select Early

Only keep columns you need:

```yaml
transforms:
  # Good: Select needed columns early
  - op: select
    columns: [id, date, amount, category]

  # Now operations work with less data
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

### 3. Avoid Unnecessary Operations

```yaml
# Bad: Unnecessary sort before aggregate
transforms:
  - op: sort
    by: [{column: date, order: asc}]
  - op: aggregate  # Aggregate doesn't need sorted input
    group_by: [category]

# Good: Remove unnecessary sort
transforms:
  - op: aggregate
    group_by: [category]
```

### 4. Combine Filters

```yaml
# Less efficient: Multiple filter operations
transforms:
  - op: filter
    predicate: status = 'active'
  - op: filter
    predicate: date >= '2025-01-01'
  - op: filter
    predicate: amount > 0

# More efficient: Single filter
transforms:
  - op: filter
    predicate: |
      status = 'active'
      AND date >= '2025-01-01'
      AND amount > 0
```

## Join Optimization

### 1. Filter Before Joining

```yaml
transforms:
  # Filter main table first
  - op: filter
    predicate: date >= '2025-01-01'

  # Then join (fewer rows to match)
  - op: join
    right:
      type: file
      path: data/dimension.parquet
      format: parquet
    on: [id]
    how: left
```

### 2. Join Smaller Tables

Put the larger table on the left:

```yaml
# Source is large (1M rows)
source:
  type: file
  path: data/transactions.parquet  # 1M rows

transforms:
  # Join with smaller dimension table (10K rows)
  - op: join
    right:
      type: file
      path: data/products.parquet  # 10K rows
      format: parquet
    on: [product_id]
    how: left
```

### 3. Use Appropriate Join Type

```yaml
# inner: Only matching rows (smallest result)
- op: join
  how: inner

# left: All left rows (may include NULLs)
- op: join
  how: left
```

## Memory Management

### 1. Process in Chunks

For very large files, use streaming-capable backends:

```yaml
engine: polars  # Supports streaming

source:
  type: file
  path: data/huge_file.parquet
  format: parquet
```

### 2. Reduce Column Count

```yaml
transforms:
  - op: select
    columns: [id, amount, date]  # Only what's needed
```

### 3. Use Appropriate Data Types

```yaml
transforms:
  - op: cast
    columns:
      id: int32      # Instead of int64
      amount: float32  # Instead of float64
```

## Parallel Execution

### Multiple Independent Pipelines

Run independent pipelines in parallel:

```bash
# Sequential (slow)
quicketl run pipeline1.yml
quicketl run pipeline2.yml
quicketl run pipeline3.yml

# Parallel (fast)
quicketl run pipeline1.yml &
quicketl run pipeline2.yml &
quicketl run pipeline3.yml &
wait
```

### Spark Parallelism

For Spark backend:

```bash
export SPARK_EXECUTOR_INSTANCES=10
export SPARK_EXECUTOR_CORES=4
export SPARK_EXECUTOR_MEMORY=8g

quicketl run pipeline.yml --engine spark
```

## I/O Optimization

### 1. Use Local Storage

Local SSD is faster than network storage:

```yaml
# Fast: Local SSD
source:
  type: file
  path: /local/ssd/data.parquet

# Slower: Network mount
source:
  type: file
  path: /mnt/network/data.parquet
```

### 2. Minimize Network Calls

For cloud storage, batch reads:

```yaml
# Efficient: Read all matching files at once
source:
  type: file
  path: s3://bucket/data/*.parquet  # Single glob
  format: parquet
```

### 3. Compress Output

```yaml
sink:
  type: file
  path: output/results.parquet
  format: parquet
  options:
    compression: snappy  # Fast compression
```

## Benchmarking

### Measure Execution Time

```bash
time quicketl run pipeline.yml
```

### JSON Metrics

```bash
quicketl run pipeline.yml --json | jq '.duration_ms'
```

### Compare Backends

```python
import time
from quicketl import Pipeline

backends = ["duckdb", "polars", "pandas"]

for backend in backends:
    pipeline = Pipeline.from_yaml("pipeline.yml")
    start = time.time()
    pipeline.run(engine=backend)
    duration = time.time() - start
    print(f"{backend}: {duration:.2f}s")
```

## Profiling

### Verbose Output

```bash
quicketl run pipeline.yml --verbose
```

Shows timing for each step.

### Python Profiling

```python
import cProfile
from quicketl import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
cProfile.run("pipeline.run()", sort="cumtime")
```

## Common Bottlenecks

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Slow start | Large CSV parsing | Use Parquet |
| Memory error | Too much data | Filter early, use Polars |
| Slow joins | Large tables | Filter before join |
| Slow writes | Many small files | Batch writes |
| Network timeout | Cloud storage | Use local cache |

## Performance Checklist

- [ ] Using Parquet instead of CSV?
- [ ] Filtering early in pipeline?
- [ ] Selecting only needed columns?
- [ ] Using appropriate backend for data size?
- [ ] Joins ordered correctly (large left, small right)?
- [ ] No unnecessary transforms?
- [ ] Output compressed?

## Related

- [Backend Selection](../guides/backends/index.md) - Choose the right backend
- [DuckDB](../guides/backends/local.md#duckdb) - Optimize for DuckDB
- [Polars](../guides/backends/local.md#polars) - Optimize for Polars
