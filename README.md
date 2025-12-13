# QuickETL

**Fast & Flexible Python ETL Framework with 20+ backend support via Ibis**

QuickETL is a configuration-driven ETL framework that provides a simple, unified API for data processing across multiple compute backends including DuckDB, Polars, Spark, and pandas.

## Features

- **Multi-backend Support**: Run the same pipeline on DuckDB, Polars, DataFusion, Spark, pandas, and more via Ibis
- **Configuration-driven**: Define pipelines in YAML with variable substitution
- **Quality Checks**: Built-in data quality validation (not_null, unique, row_count, accepted_values, expression)
- **12 Transform Operations**: select, rename, filter, derive_column, cast, fill_null, dedup, sort, join, aggregate, union, limit
- **CLI Interface**: `quicketl run`, `quicketl validate`, `quicketl init`, `quicketl info`
- **Airflow Integration**: `@quicketl_task` decorator for DAG tasks
- **Cloud Storage**: S3, GCS, Azure via fsspec

## Installation

```bash
# Basic installation (DuckDB + Polars)
pip install quicketl

# With additional backends
pip install quicketl[spark]
pip install quicketl[datafusion]

# With cloud storage
pip install quicketl[aws]
pip install quicketl[gcp]
pip install quicketl[azure]

# All backends and tools
pip install quicketl[all]
```

## Quick Start

### CLI Usage

```bash
# Initialize in existing project
quicketl init

# Or create a new project
quicketl init my_project
cd my_project

# Run a pipeline
quicketl run pipelines/sample.yml

# Validate configuration
quicketl validate pipelines/sample.yml

# Show available backends
quicketl info --backends
```

### Pipeline Configuration (YAML)

```yaml
name: sales_etl
description: Process daily sales data
engine: duckdb

source:
  type: file
  path: data/sales.parquet
  format: parquet

transforms:
  - op: filter
    predicate: amount > 0
  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1
  - op: aggregate
    group_by: [region]
    aggs:
      total_sales: sum(amount)
      order_count: count(*)

checks:
  - type: not_null
    columns: [region, total_sales]
  - type: row_count
    min: 1

sink:
  type: file
  path: data/output.parquet
  format: parquet
```

### Python API

```python
from quicketl import Pipeline, QuickETLEngine
from quicketl.config.models import FileSource, FileSink
from quicketl.config.transforms import FilterTransform, DeriveColumnTransform

# From YAML
pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

# Builder pattern
pipeline = (
    Pipeline("my_pipeline", engine="duckdb")
    .source(FileSource(path="data.parquet"))
    .transform(FilterTransform(predicate="amount > 0"))
    .transform(DeriveColumnTransform(name="tax", expr="amount * 0.1"))
    .sink(FileSink(path="output.parquet"))
)
result = pipeline.run()

# Direct engine usage
engine = QuickETLEngine(backend="duckdb")
table = engine.read_file("data.parquet", "parquet")
filtered = engine.filter(table, "amount > 100")
result = engine.to_polars(filtered)
```

### Airflow Integration

```python
from quicketl.integrations.airflow import quicketl_task

@quicketl_task(config_path="pipelines/daily_etl.yml")
def run_daily_etl(**context):
    return {"RUN_DATE": context["ds"]}
```

## Supported Backends

| Backend | Type | Installation |
|---------|------|--------------|
| DuckDB | Local/Embedded | Included by default |
| Polars | Local/Embedded | Included by default |
| DataFusion | Local/Embedded | `pip install quicketl[datafusion]` |
| Spark | Distributed | `pip install quicketl[spark]` |
| pandas | Local | `pip install quicketl[pandas]` |
| PostgreSQL | Database | `pip install quicketl[postgres]` |
| MySQL | Database | `pip install quicketl[mysql]` |
| ClickHouse | Database | `pip install quicketl[clickhouse]` |
| Snowflake | Cloud DW | `pip install quicketl[snowflake]` |
| BigQuery | Cloud DW | `pip install quicketl[bigquery]` |
| Trino | Distributed SQL | `pip install quicketl[trino]` |

## Development

```bash
# Clone and install dev dependencies
git clone https://github.com/ameijin/quicketl.git
cd quicketl
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
