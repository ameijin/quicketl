# User Guide

This guide covers all aspects of building pipelines with QuickETL.

## Core Concepts

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } **Configuration**

    ---

    Learn YAML configuration, variable substitution, and IDE integration.

    [:octicons-arrow-right-24: Configuration](configuration/index.md)

-   :material-database-import:{ .lg .middle } **Sources & Sinks**

    ---

    Read from and write to files, databases, and cloud storage.

    [:octicons-arrow-right-24: Sources & Sinks](io/index.md)

-   :material-swap-horizontal:{ .lg .middle } **Transforms**

    ---

    All 12 data transformation operations.

    [:octicons-arrow-right-24: Transforms](transforms/index.md)

-   :material-check-circle:{ .lg .middle } **Quality Checks**

    ---

    Validate data quality with built-in checks.

    [:octicons-arrow-right-24: Quality Checks](quality/index.md)

-   :material-server:{ .lg .middle } **Backends**

    ---

    Choose the right compute engine for your workload.

    [:octicons-arrow-right-24: Backends](backends/index.md)

-   :material-sitemap:{ .lg .middle } **Workflows**

    ---

    Orchestrate multiple pipelines with dependencies, parallel execution, and DAG generation.

    [:octicons-arrow-right-24: Workflows](workflows/index.md)

</div>

## How QuickETL Works

QuickETL pipelines follow a simple flow:

```mermaid
graph LR
    A[Source] --> B[Transforms]
    B --> C[Quality Checks]
    C --> D[Sink]
```

1. **Source** - Read data from files, databases, or cloud storage
2. **Transforms** - Apply transformations in sequence
3. **Quality Checks** - Validate the transformed data
4. **Sink** - Write to the destination

## Configuration Methods

### YAML Configuration

Define pipelines declaratively:

```yaml
name: my_pipeline
engine: duckdb

source:
  type: file
  path: input.parquet

transforms:
  - op: filter
    predicate: amount > 0

sink:
  type: file
  path: output.parquet
```

### Python API

Build pipelines programmatically:

```python
from quicketl import Pipeline
from quicketl.config.models import FileSource, FileSink
from quicketl.config.transforms import FilterTransform

pipeline = (
    Pipeline("my_pipeline", engine="duckdb")
    .source(FileSource(path="input.parquet"))
    .transform(FilterTransform(predicate="amount > 0"))
    .sink(FileSink(path="output.parquet"))
)

result = pipeline.run()
```

## Quick Reference

### Transform Operations

| Transform | Purpose |
|-----------|---------|
| [`select`](transforms/operations.md#select) | Choose columns |
| [`rename`](transforms/operations.md#rename) | Rename columns |
| [`filter`](transforms/operations.md#filter) | Filter rows |
| [`derive_column`](transforms/operations.md#derive_column) | Add computed columns |
| [`cast`](transforms/operations.md#cast) | Convert types |
| [`fill_null`](transforms/operations.md#fill_null) | Replace nulls |
| [`dedup`](transforms/operations.md#dedup) | Remove duplicates |
| [`sort`](transforms/operations.md#sort) | Order rows |
| [`join`](transforms/operations.md#join) | Join datasets |
| [`aggregate`](transforms/operations.md#aggregate) | Group and aggregate |
| [`union`](transforms/operations.md#union) | Combine datasets |
| [`limit`](transforms/operations.md#limit) | Limit rows |

### Quality Checks

| Check | Purpose |
|-------|---------|
| [`not_null`](quality/checks.md#not_null) | No null values |
| [`unique`](quality/checks.md#unique) | Uniqueness constraint |
| [`row_count`](quality/checks.md#row_count) | Row count bounds |
| [`accepted_values`](quality/checks.md#accepted_values) | Value whitelist |
| [`expression`](quality/checks.md#expression) | Custom validation |

### Supported Backends

| Backend | Type | Default |
|---------|------|---------|
| [DuckDB](backends/local.md#duckdb) | Local | Yes |
| [Polars](backends/local.md#polars) | Local | Yes |
| [Spark](backends/distributed.md) | Distributed | No |
| [Snowflake](backends/cloud-warehouses.md#snowflake) | Cloud DW | No |
| [BigQuery](backends/cloud-warehouses.md#bigquery) | Cloud DW | No |

## Next Steps

Start with [Configuration](configuration/index.md) to understand how pipelines are structured, then explore [Transforms](transforms/index.md) to learn the available operations.
