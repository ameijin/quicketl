# File Sinks

Write data to Parquet and CSV files.

## Basic Usage

```yaml
sink:
  type: file
  path: output/results.parquet
  format: parquet
```

## Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | Yes | - | Must be `file` |
| `path` | Yes | - | Output path or cloud URI |
| `format` | No | `parquet` | Output format: `parquet`, `csv` |
| `partition_by` | No | `[]` | Columns to partition by |
| `mode` | No | `overwrite` | Write mode: `overwrite`, `append` |

## Formats

### Parquet (Recommended)

```yaml
sink:
  type: file
  path: output/sales.parquet
  format: parquet
```

Parquet advantages:

- Efficient columnar storage
- Built-in compression (snappy by default)
- Schema preservation
- Fast analytical queries

### CSV

```yaml
sink:
  type: file
  path: output/sales.csv
  format: csv
```

## Write Modes

### Overwrite (Default)

Replace existing data:

```yaml
sink:
  type: file
  path: output/sales.parquet
  mode: overwrite
```

### Append

Add to existing data:

```yaml
sink:
  type: file
  path: output/sales.parquet
  mode: append
```

!!! warning "Append with Parquet"
    Appending creates additional files in the output directory. Consider using partitioning for incremental writes.

## Partitioning

Partition output by column values:

```yaml
sink:
  type: file
  path: output/sales/
  format: parquet
  partition_by: [year, month]
```

This creates a directory structure:

```
output/sales/
├── year=2025/
│   ├── month=01/
│   │   └── data.parquet
│   └── month=02/
│       └── data.parquet
└── year=2024/
    └── month=12/
        └── data.parquet
```

### Common Partitioning Patterns

#### By Date

```yaml
# First, derive date parts
transforms:
  - op: derive_column
    name: year
    expr: extract(year from date)
  - op: derive_column
    name: month
    expr: extract(month from date)

sink:
  type: file
  path: output/data/
  partition_by: [year, month]
```

#### By Region

```yaml
sink:
  type: file
  path: output/sales/
  partition_by: [region]
```

#### Multiple Levels

```yaml
sink:
  type: file
  path: output/sales/
  partition_by: [region, category, year]
```

### Partitioning Benefits

- **Query performance**: Only read relevant partitions
- **Incremental updates**: Update specific partitions
- **Parallel processing**: Process partitions independently
- **Data management**: Delete old partitions easily

## Cloud Storage

Write to cloud storage:

```yaml
# S3
sink:
  type: file
  path: s3://my-bucket/output/sales.parquet

# GCS
sink:
  type: file
  path: gs://my-bucket/output/sales.parquet

# Azure
sink:
  type: file
  path: abfs://container@account.dfs.core.windows.net/output/sales.parquet
```

With partitioning:

```yaml
sink:
  type: file
  path: s3://data-lake/processed/sales/
  format: parquet
  partition_by: [date]
```

## Variables in Paths

Use runtime variables:

```yaml
sink:
  type: file
  path: output/${DATE}/sales.parquet
```

```bash
quicketl run pipeline.yml --var DATE=2025-01-15
```

For daily outputs:

```yaml
sink:
  type: file
  path: s3://bucket/output/date=${RUN_DATE}/
```

## Python API

```python
from quicketl.config.models import FileSink

# Basic
sink = FileSink(path="output/sales.parquet")

# With partitioning
sink = FileSink(
    path="output/sales/",
    format="parquet",
    partition_by=["year", "month"]
)

# CSV
sink = FileSink(
    path="output/sales.csv",
    format="csv"
)
```

## Best Practices

### Use Parquet for Analytics

Parquet is significantly better for analytical workloads:

| Aspect | Parquet | CSV |
|--------|---------|-----|
| File size | ~4x smaller | Larger |
| Read speed | ~10x faster | Slower |
| Schema | Preserved | Lost |
| Types | Full support | String only |

### Partition Large Datasets

For datasets over 1 million rows, use partitioning:

```yaml
sink:
  type: file
  path: output/large_dataset/
  partition_by: [date]
```

### Use Descriptive Paths

```yaml
# Good
path: output/sales_summary/date=${DATE}/

# Bad
path: output/data/
```

### Include Metadata

Consider including run metadata:

```yaml
# Add run date to filename
sink:
  type: file
  path: output/sales_${RUN_DATE}_${RUN_ID}.parquet
```

## Troubleshooting

### Permission Denied

```
Error: Permission denied
```

- Check write permissions on the output directory
- For cloud storage, verify credentials have write access
- Ensure the output path is writable

### Path Not Found

```
Error: Directory not found
```

QuickETL creates directories automatically. If this error occurs:

- Check the parent path is valid
- Verify cloud bucket exists

### Disk Full

```
Error: No space left on device
```

- Check available disk space
- Use cloud storage for large outputs
- Enable compression (automatic with Parquet)

## Related

- [File Sources](file-sources.md) - Reading files
- [Cloud Storage](cloud-storage.md) - Cloud provider setup
- [Performance](../../best-practices/performance.md) - Optimization tips
