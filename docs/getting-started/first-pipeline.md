# Your First Pipeline

This tutorial walks you through building a complete pipeline from scratch, explaining each component in detail.

## The Scenario

You have sales data in CSV format and need to:

1. Filter out invalid records
2. Calculate additional metrics
3. Aggregate by category
4. Validate the output quality
5. Save as Parquet for analysis

## Step 1: Create a New Pipeline File

Create a new file `pipelines/sales_report.yml`:

```yaml
name: sales_report
description: Generate sales summary report by category
engine: duckdb
```

### Pipeline Metadata

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier for the pipeline |
| `description` | No | Human-readable description |
| `engine` | No | Compute backend (default: `duckdb`) |

## Step 2: Define the Source

Add a source to read the sales data:

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
```

### Source Options

For file sources:

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Source type: `file`, `database` |
| `path` | Yes | File path (local or cloud) |
| `format` | No | File format: `csv`, `parquet`, `json` (default: `parquet`) |

!!! tip "Cloud Paths"
    Use cloud URIs for remote data:

    - S3: `s3://bucket/path/data.parquet`
    - GCS: `gs://bucket/path/data.parquet`
    - Azure: `abfs://container@account.dfs.core.windows.net/path/data.parquet`

## Step 3: Add Transforms

Transforms are applied in order. Each transform takes the output of the previous step.

### Filter Invalid Records

Remove records with non-positive amounts:

```yaml
transforms:
  - op: filter
    predicate: amount > 0
```

The `predicate` uses SQL-like syntax. Supported operators:

- Comparison: `>`, `<`, `>=`, `<=`, `=`, `!=`
- Logical: `AND`, `OR`, `NOT`
- Null checks: `IS NULL`, `IS NOT NULL`

### Calculate Metrics

Add computed columns:

```yaml
  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1

  - op: derive_column
    name: profit_margin
    expr: (amount - cost) / amount
```

### Aggregate by Category

Group and summarize:

```yaml
  - op: aggregate
    group_by: [category]
    aggs:
      total_revenue: sum(amount)
      total_with_tax: sum(total_with_tax)
      avg_order_value: avg(amount)
      order_count: count(*)
```

Supported aggregation functions:

| Function | Description |
|----------|-------------|
| `sum(col)` | Sum of values |
| `avg(col)` | Average/mean |
| `min(col)` | Minimum value |
| `max(col)` | Maximum value |
| `count(*)` | Count all rows |
| `count(col)` | Count non-null values |

### Sort the Results

Order by total revenue descending:

```yaml
  - op: sort
    by: [total_revenue]
    descending: true
```

## Step 4: Add Quality Checks

Quality checks validate your output data:

```yaml
checks:
  # Ensure key columns have no nulls
  - type: not_null
    columns: [category, total_revenue]

  # Ensure we have at least one category
  - type: row_count
    min: 1

  # Ensure revenue is positive
  - type: expression
    expr: total_revenue > 0
```

### Available Check Types

| Check | Description |
|-------|-------------|
| `not_null` | Verify columns have no null values |
| `unique` | Verify uniqueness |
| `row_count` | Validate row count bounds |
| `accepted_values` | Check against whitelist |
| `expression` | Custom SQL predicate |

## Step 5: Define the Sink

Specify where to write the output:

```yaml
sink:
  type: file
  path: data/output/sales_report.parquet
  format: parquet
```

### Sink Options

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Sink type: `file`, `database` |
| `path` | Yes | Output path |
| `format` | No | Output format (default: `parquet`) |
| `partition_by` | No | Columns to partition by |
| `mode` | No | `overwrite` or `append` (default: `overwrite`) |

## Complete Pipeline

Here's the complete pipeline:

```yaml title="pipelines/sales_report.yml"
name: sales_report
description: Generate sales summary report by category
engine: duckdb

source:
  type: file
  path: data/sales.csv
  format: csv

transforms:
  # Clean data
  - op: filter
    predicate: amount > 0

  # Calculate metrics
  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1

  # Aggregate by category
  - op: aggregate
    group_by: [category]
    aggs:
      total_revenue: sum(amount)
      total_with_tax: sum(total_with_tax)
      avg_order_value: avg(amount)
      order_count: count(*)

  # Sort by revenue
  - op: sort
    by: [total_revenue]
    descending: true

checks:
  - type: not_null
    columns: [category, total_revenue]
  - type: row_count
    min: 1
  - type: expression
    expr: total_revenue > 0

sink:
  type: file
  path: data/output/sales_report.parquet
  format: parquet
```

## Run the Pipeline

### Validate First

Check the configuration:

```bash
quicketl validate pipelines/sales_report.yml
```

### Dry Run

Execute without writing output:

```bash
quicketl run pipelines/sales_report.yml --dry-run
```

### Full Run

Execute the complete pipeline:

```bash
quicketl run pipelines/sales_report.yml
```

### Verbose Output

See detailed logs:

```bash
quicketl run pipelines/sales_report.yml --verbose
```

## Using Python Instead

The same pipeline in Python:

```python
from quicketl import Pipeline
from quicketl.config.models import FileSource, FileSink
from quicketl.config.transforms import (
    FilterTransform,
    DeriveColumnTransform,
    AggregateTransform,
    SortTransform,
)
from quicketl.config.checks import NotNullCheck, RowCountCheck, ExpressionCheck

pipeline = (
    Pipeline("sales_report", description="Generate sales summary", engine="duckdb")
    .source(FileSource(path="data/sales.csv", format="csv"))
    .transform(FilterTransform(predicate="amount > 0"))
    .transform(DeriveColumnTransform(name="total_with_tax", expr="amount * 1.1"))
    .transform(AggregateTransform(
        group_by=["category"],
        aggs={
            "total_revenue": "sum(amount)",
            "total_with_tax": "sum(total_with_tax)",
            "avg_order_value": "avg(amount)",
            "order_count": "count(*)",
        }
    ))
    .transform(SortTransform(by=["total_revenue"], descending=True))
    .check(NotNullCheck(columns=["category", "total_revenue"]))
    .check(RowCountCheck(min=1))
    .check(ExpressionCheck(expr="total_revenue > 0"))
    .sink(FileSink(path="data/output/sales_report.parquet"))
)

result = pipeline.run()
print(f"Pipeline {'succeeded' if result.succeeded else 'failed'}")
print(f"Processed {result.rows_processed} rows in {result.duration_ms:.1f}ms")
```

## Next Steps

Now that you understand pipeline basics:

- [Project Structure](project-structure.md) - Organize larger projects
- [Transforms](../user-guide/transforms/index.md) - Learn all 12 transforms
- [Quality Checks](../user-guide/quality/index.md) - Advanced validation
- [Examples](../examples/index.md) - Real-world patterns
