# Installation

This page shows how to install QuickETL. Use it to pick the right install for what you want to do.

## Which install do I need?

| I want to | Install | Approx. size |
|-----------|---------|--------------|
| Use the CLI to create and scaffold platforms, create projects, validate configs and export the JSON schema | `pip install quicketl` (core only) | 33 MB |
| Run pipelines and workflows with DuckDB and Polars | `pip install 'quicketl[pipelines]'` | 465 MB |
| Run pipelines on a specific backend or cloud (for example Snowflake or S3) | `pip install 'quicketl[snowflake]'` (a backend extra) | 465 MB plus the backend |
| Everything | `pip install 'quicketl[all]'` | Very large |

Sizes are measured on a real install of the site-packages folder. They change as dependencies change.

Backend extras (`spark`, `pandas`, `datafusion`, `aws`, `gcp`, `azure`, `snowflake`, `bigquery`, `trino`, `postgres`, `mysql`, `clickhouse`) already include `pipelines`. The AI and data contract extras do too. You do not need to install both.

The secrets (`secrets-aws`, `secrets-azure`), telemetry (`opentelemetry`, `openlineage`) and `docs` extras do not include `pipelines`.

!!! note "Quote extras in your shell"
    Shells such as zsh treat square brackets as a pattern. Write `pip install 'quicketl[pipelines]'` with quotes.

!!! info "Coming from 1.x?"
    From 2.0.0, a plain `pip install quicketl` no longer includes pipelines. See [Upgrading to 2.0](upgrading.md).

## Core Installation

The core install is small. It contains the CLI, `init`, `validate`, `schema` and the `platform` commands. `quicketl platform scaffold` and `update` also need `git` installed.

=== "pip"

    ```bash
    pip install quicketl
    ```

=== "uv"

    ```bash
    uv pip install quicketl
    ```

=== "pipx (CLI only)"

    ```bash
    pipx install quicketl
    ```

The core install has no pipeline engine. Commands that run pipelines print an error and exit with code 1:

```text
Error: Pipelines need the pipelines extra. Install it with: pip install 'quicketl[pipelines]'
```

## Install for Running Pipelines

Install the `pipelines` extra to run pipelines and workflows:

=== "pip"

    ```bash
    pip install 'quicketl[pipelines]'
    ```

=== "uv"

    ```bash
    uv pip install 'quicketl[pipelines]'
    ```

This gives you:

- DuckDB backend (default)
- Polars backend
- Ibis and fsspec
- `quicketl run`, `quicketl workflow` and `quicketl info --backends`
- The Python API (`from quicketl import Pipeline`)

## Verify Installation

Check that QuickETL is installed correctly:

```bash
quicketl --version
```

You should see your installed version, for example:

```
quicketl version 2.0.0
```

Check available backends (this needs the `pipelines` extra):

```bash
quicketl info --backends --check
```

## Optional Dependencies

QuickETL uses optional dependencies to keep the base installation lightweight. Install only what you need. Each extra below includes `pipelines`.

### Cloud Storage

For reading/writing to cloud storage:

=== "AWS S3"

    ```bash
    pip install 'quicketl[aws]'
    ```

    Includes `s3fs` and `boto3` for S3 access.

=== "Google Cloud Storage"

    ```bash
    pip install 'quicketl[gcp]'
    ```

    Includes `gcsfs` and `google-cloud-storage`.

=== "Azure ADLS"

    ```bash
    pip install 'quicketl[azure]'
    ```

    Includes `adlfs` and `azure-storage-blob`.

### Additional Compute Backends

For distributed or alternative compute engines:

=== "Apache Spark"

    ```bash
    pip install 'quicketl[spark]'
    ```

    Requires Java 8+ to be installed.

=== "DataFusion"

    ```bash
    pip install 'quicketl[datafusion]'
    ```

    Apache Arrow-native query engine.

=== "pandas"

    ```bash
    pip install 'quicketl[pandas]'
    ```

    For pandas-based processing.

### Cloud Data Warehouses

For connecting to cloud data warehouses:

```bash
# Snowflake
pip install 'quicketl[snowflake]'

# Google BigQuery
pip install 'quicketl[bigquery]'

# Trino
pip install 'quicketl[trino]'
```

### Databases

For connecting to relational databases:

```bash
# PostgreSQL
pip install 'quicketl[postgres]'

# MySQL
pip install 'quicketl[mysql]'

# ClickHouse
pip install 'quicketl[clickhouse]'
```

### Multiple Extras

Install multiple extras at once:

```bash
pip install 'quicketl[aws,spark,snowflake]'
```

### Everything

Install all optional dependencies:

```bash
pip install 'quicketl[all]'
```

!!! warning "Large Installation"
    The `[all]` extra installs many dependencies including Spark. Only use this if you need everything.

## Development Installation

For contributing to QuickETL:

```bash
# Clone the repository
git clone https://github.com/quicketl/quicketl.git
cd quicketl

# Create the environment and install the dev tools and the pipelines extra
uv sync --group dev --extra pipelines
```

## Troubleshooting

### Import Errors

If you get import errors for optional backends:

```python
ImportError: No module named 'ibis.backends.snowflake'
```

Install the required extra:

```bash
pip install 'quicketl[snowflake]'
```

### DuckDB Version Conflicts

If you have version conflicts with DuckDB:

```bash
pip install --upgrade 'quicketl[pipelines]'
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

Now that QuickETL is installed, continue to the [Quick Start](quickstart.md) to create your first pipeline.

Upgrading from 1.x? Read [Upgrading to 2.0](upgrading.md).
