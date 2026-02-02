# QuickETL

**Fast & Flexible Python ETL Framework with 20+ backend support via Ibis**

[![PyPI version](https://badge.fury.io/py/quicketl.svg)](https://pypi.org/project/quicketl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

QuickETL is a configuration-driven ETL framework that provides a simple, unified API for data processing across multiple compute backends including DuckDB, Polars, Spark, and pandas.

**[Documentation](https://quicketl.com)** | **[GitHub](https://github.com/ameijin/quicketl)**

## Features

- **20+ Backends**: DuckDB, Polars, Spark, pandas, Snowflake, BigQuery, PostgreSQL, and more via Ibis
- **Configuration-driven**: Define pipelines in YAML with variable substitution
- **18 Transforms**: filter, aggregate, join, union, derive_column, window, pivot, unpivot, hash_key, coalesce, cast, fill_null, dedup, sort, select, rename, limit, and more
- **6 Quality Checks**: not_null, unique, row_count, accepted_values, expression, and contract (Pandera)
- **Data Contracts**: Schema validation with Pandera, YAML-defined contracts, and a contract registry
- **Multi-Source Pipelines**: Join and union across multiple data sources in a single pipeline
- **Database Sink**: Write to databases with append, truncate, replace, and upsert modes
- **Partitioned Writes**: Write partitioned Parquet/CSV files by one or more columns
- **Workflows**: Multi-stage pipeline orchestration with parallel execution
- **AI/ML Transforms**: Text chunking and embedding generation for RAG pipelines
- **Secrets Management**: Pluggable providers for AWS Secrets Manager, Azure Key Vault, and env vars
- **Telemetry**: OpenTelemetry and OpenLineage integration for observability
- **CLI & Python API**: Use `quicketl run` or the Pipeline builder pattern
- **Cloud Storage**: S3, GCS, Azure via fsspec

## Installation

```bash
pip install quicketl
```

With optional extras:

```bash
# Specific backends
pip install quicketl[polars]
pip install quicketl[spark]

# AI/ML features
pip install quicketl[embeddings-openai]
pip install quicketl[chunking]

# Data contracts
pip install quicketl[contracts]

# All optional dependencies
pip install quicketl[all]
```

See [installation docs](https://quicketl.com/getting-started/installation/) for backend-specific extras.

## Quick Start

```bash
# Create a new project
quicketl init my_project
cd my_project

# Run the sample pipeline
quicketl run pipelines/sample.yml
```

Or use the Python API:

```python
from quicketl import Pipeline

# From YAML configuration
pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

# Or use the builder pattern
from quicketl.config.models import FileSource, FileSink
from quicketl.config.transforms import FilterTransform, AggregateTransform
from quicketl.config.checks import NotNullCheck

pipeline = (
    Pipeline("sales_summary", engine="duckdb")
    .source(FileSource(path="data/sales.parquet"))
    .transform(FilterTransform(predicate="amount > 0"))
    .transform(AggregateTransform(
        group_by=["region"],
        aggs={"total": "sum(amount)", "count": "count(*)"},
    ))
    .check(NotNullCheck(columns=["region"]))
    .sink(FileSink(path="output/summary.parquet"))
)
result = pipeline.run()
print(result.summary())
```

## Example Pipeline

```yaml
name: sales_etl
engine: duckdb

source:
  type: file
  path: data/sales.parquet

transforms:
  - op: filter
    predicate: amount > 0
  - op: derive_column
    name: revenue
    expr: quantity * unit_price
  - op: aggregate
    group_by: [region]
    aggs:
      total: sum(amount)
      order_count: count(*)

checks:
  - type: not_null
    columns: [region, total]
  - type: row_count
    min: 1

sink:
  type: file
  path: output/summary.parquet
```

## Multi-Source Join

```yaml
name: orders_with_customers
engine: duckdb

sources:
  orders:
    type: file
    path: data/orders.parquet
  customers:
    type: file
    path: data/customers.parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]
    how: left
  - op: select
    columns: [order_id, customer_name, amount]

sink:
  type: file
  path: output/enriched_orders.parquet
```

## Documentation

Full documentation, tutorials, and API reference at **[quicketl.com](https://quicketl.com)**

- [Getting Started](https://quicketl.com/getting-started/)
- [Pipeline Configuration](https://quicketl.com/guides/configuration/)
- [Supported Backends](https://quicketl.com/guides/backends/)
- [CLI Reference](https://quicketl.com/reference/cli/)

## License

MIT License - see [LICENSE](LICENSE) for details.
