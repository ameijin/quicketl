# Sources & Sinks

QuickETL reads data from **sources** and writes data to **sinks**. This section covers all supported source and sink types.

## Overview

<div class="grid cards" markdown>

-   :material-file-import:{ .lg .middle } **File Sources**

    ---

    Read CSV, Parquet, and JSON files.

    [:octicons-arrow-right-24: File Sources](file-sources.md)

-   :material-database:{ .lg .middle } **Database Sources**

    ---

    Read from PostgreSQL, MySQL, and other databases.

    [:octicons-arrow-right-24: Database Sources](database-sources.md)

-   :material-cloud:{ .lg .middle } **Cloud Storage**

    ---

    Read from S3, GCS, and Azure.

    [:octicons-arrow-right-24: Cloud Storage](cloud-storage.md)

-   :material-file-export:{ .lg .middle } **File Sinks**

    ---

    Write Parquet and CSV files.

    [:octicons-arrow-right-24: File Sinks](file-sinks.md)

-   :material-database-export:{ .lg .middle } **Database Sinks**

    ---

    Write to databases.

    [:octicons-arrow-right-24: Database Sinks](database-sinks.md)

</div>

## Source Types

| Type | Description | Formats |
|------|-------------|---------|
| `file` | Local or cloud files | CSV, Parquet, JSON |
| `database` | Relational databases | SQL query or table |

## Sink Types

| Type | Description | Formats |
|------|-------------|---------|
| `file` | Local or cloud files | Parquet, CSV |
| `database` | Relational databases | Table writes |

## Quick Reference

### File Source

```yaml
source:
  type: file
  path: data/sales.parquet
  format: parquet
```

### Database Source

```yaml
source:
  type: database
  connection: postgresql://localhost/db
  table: sales
```

### File Sink

```yaml
sink:
  type: file
  path: output/results.parquet
  format: parquet
```

### Database Sink

```yaml
sink:
  type: database
  connection: ${DATABASE_URL}
  table: results
  mode: truncate
```

## Cloud Storage

All file sources and sinks support cloud URIs:

| Provider | URI Format |
|----------|------------|
| AWS S3 | `s3://bucket/path/file.parquet` |
| Google Cloud | `gs://bucket/path/file.parquet` |
| Azure ADLS | `abfs://container@account.dfs.core.windows.net/path/file.parquet` |

See [Cloud Storage](cloud-storage.md) for authentication setup.
