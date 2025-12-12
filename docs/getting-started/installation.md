# Installation

This guide covers how to install ETLX and its optional dependencies.

## Basic Installation

Install ETLX with the default backends (DuckDB and Polars):

=== "pip"

    ```bash
    pip install etlx
    ```

=== "uv"

    ```bash
    uv pip install etlx
    ```

=== "pipx (CLI only)"

    ```bash
    pipx install etlx
    ```

This gives you:

- DuckDB backend (default)
- Polars backend
- CLI tools (`etlx run`, `etlx init`, etc.)
- Python API

## Verify Installation

Check that ETLX is installed correctly:

```bash
quicketl --version
```

You should see output like:

```
etlx version 0.1.0
```

Check available backends:

```bash
quicketl info --backends --check
```

## Optional Dependencies

ETLX uses optional dependencies to keep the base installation lightweight. Install only what you need.

### Cloud Storage

For reading/writing to cloud storage:

=== "AWS S3"

    ```bash
    pip install etlx[aws]
    ```

    Includes `s3fs` and `boto3` for S3 access.

=== "Google Cloud Storage"

    ```bash
    pip install etlx[gcp]
    ```

    Includes `gcsfs` and `google-cloud-storage`.

=== "Azure ADLS"

    ```bash
    pip install etlx[azure]
    ```

    Includes `adlfs` and `azure-storage-blob`.

### Additional Compute Backends

For distributed or alternative compute engines:

=== "Apache Spark"

    ```bash
    pip install etlx[spark]
    ```

    Requires Java 8+ to be installed.

=== "DataFusion"

    ```bash
    pip install etlx[datafusion]
    ```

    Apache Arrow-native query engine.

=== "pandas"

    ```bash
    pip install etlx[pandas]
    ```

    For pandas-based processing.

### Cloud Data Warehouses

For connecting to cloud data warehouses:

```bash
# Snowflake
pip install quicketl[snowflake]

# Google BigQuery
pip install quicketl[bigquery]

# Trino
pip install quicketl[trino]
```

### Databases

For connecting to relational databases:

```bash
# PostgreSQL
pip install quicketl[postgres]

# MySQL
pip install quicketl[mysql]

# ClickHouse
pip install quicketl[clickhouse]
```

### Multiple Extras

Install multiple extras at once:

```bash
pip install quicketl[aws,spark,snowflake]
```

### Everything

Install all optional dependencies:

```bash
pip install quicketl[all]
```

!!! warning "Large Installation"
    The `[all]` extra installs many dependencies including Spark. Only use this if you need everything.

## Development Installation

For contributing to ETLX:

```bash
# Clone the repository
git clone https://github.com/etlx/etlx.git
cd quicketl

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev,docs]"
```

## Troubleshooting

### Import Errors

If you get import errors for optional backends:

```python
ImportError: No module named 'ibis.backends.snowflake'
```

Install the required extra:

```bash
pip install quicketl[snowflake]
```

### DuckDB Version Conflicts

If you have version conflicts with DuckDB:

```bash
pip install quicketl --upgrade
```

### Spark Java Requirements

Spark requires Java 8 or later. Check your Java version:

```bash
java -version
```

Set `JAVA_HOME` if needed:

```bash
export JAVA_HOME=/path/to/java
```

## Next Steps

Now that ETLX is installed, continue to the [Quick Start](quickstart.md) to create your first pipeline.
