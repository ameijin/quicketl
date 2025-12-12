# File Sources

Read data from CSV, Parquet, and JSON files.

## Basic Usage

```yaml
source:
  type: file
  path: data/sales.parquet
  format: parquet
```

## Configuration

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | Yes | - | Must be `file` |
| `path` | Yes | - | File path or cloud URI |
| `format` | No | `parquet` | File format: `csv`, `parquet`, `json` |
| `options` | No | `{}` | Format-specific options |

## Formats

### Parquet

Apache Parquet is the recommended format for performance:

```yaml
source:
  type: file
  path: data/sales.parquet
  format: parquet
```

Parquet benefits:

- Columnar storage (efficient for analytics)
- Built-in compression
- Schema preserved
- Fast reads with predicate pushdown

### CSV

Read CSV files with options:

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
  options:
    delimiter: ","
    header: true
```

#### CSV Options

| Option | Default | Description |
|--------|---------|-------------|
| `delimiter` | `,` | Field separator |
| `header` | `true` | First row contains column names |
| `skip_rows` | `0` | Number of rows to skip |
| `null_values` | `[""]` | Values to interpret as null |
| `quote_char` | `"` | Quote character |

#### CSV Examples

Tab-separated file:

```yaml
source:
  type: file
  path: data/sales.tsv
  format: csv
  options:
    delimiter: "\t"
```

No header row:

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
  options:
    header: false
```

Custom null values:

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
  options:
    null_values: ["", "NULL", "N/A", "-"]
```

### JSON

Read JSON Lines (newline-delimited JSON):

```yaml
source:
  type: file
  path: data/events.json
  format: json
```

!!! note "JSON Lines Format"
    QuickETL expects JSON Lines format where each line is a valid JSON object:
    ```json
    {"id": 1, "name": "Alice"}
    {"id": 2, "name": "Bob"}
    ```

## Path Patterns

### Local Files

```yaml
source:
  type: file
  path: data/sales.parquet
```

### Absolute Paths

```yaml
source:
  type: file
  path: /home/user/data/sales.parquet
```

### Cloud Storage

See [Cloud Storage](cloud-storage.md) for detailed setup.

```yaml
# S3
source:
  type: file
  path: s3://my-bucket/data/sales.parquet

# GCS
source:
  type: file
  path: gs://my-bucket/data/sales.parquet

# Azure
source:
  type: file
  path: abfs://container@account.dfs.core.windows.net/data/sales.parquet
```

### Variables in Paths

Use variable substitution for dynamic paths:

```yaml
source:
  type: file
  path: data/${DATE}/sales.parquet
```

```bash
quicketl run pipeline.yml --var DATE=2025-01-15
```

### Glob Patterns

!!! note "Coming in v0.2"
    Glob patterns for reading multiple files are planned for a future release.

## Python API

```python
from quicketl.config.models import FileSource

# Parquet
source = FileSource(path="data/sales.parquet")

# CSV with options
source = FileSource(
    path="data/sales.csv",
    format="csv",
    options={"delimiter": ";", "header": True}
)

# Cloud storage
source = FileSource(path="s3://bucket/data/sales.parquet")
```

## Performance Tips

### Use Parquet

Parquet is significantly faster than CSV for analytical workloads:

| Format | Read Time (1M rows) | File Size |
|--------|---------------------|-----------|
| CSV | ~2.5s | 100 MB |
| Parquet | ~0.3s | 25 MB |

### Column Selection

With Parquet, only required columns are read. Use `select` transform early:

```yaml
transforms:
  - op: select
    columns: [id, amount, date]  # Only reads these columns
```

### Compression

Parquet files are automatically compressed. For CSV, consider gzipping:

```yaml
source:
  type: file
  path: data/sales.csv.gz
  format: csv
```

## Troubleshooting

### File Not Found

```
Error: File not found: data/sales.parquet
```

- Check the file path is correct
- Use absolute paths if relative paths don't work
- Ensure cloud credentials are configured

### CSV Parsing Errors

```
Error: Could not parse CSV
```

- Check the delimiter matches your file
- Verify `header` setting is correct
- Look for inconsistent row lengths

### Encoding Issues

For files with non-UTF-8 encoding:

```yaml
source:
  type: file
  path: data/sales.csv
  format: csv
  options:
    encoding: "latin-1"
```

## Related

- [Cloud Storage](cloud-storage.md) - S3, GCS, Azure setup
- [File Sinks](file-sinks.md) - Writing files
- [Pipeline YAML](../configuration/pipeline-yaml.md) - Full configuration reference
