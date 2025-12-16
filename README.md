# QuickETL

**Fast & Flexible Python ETL Framework with 20+ backend support via Ibis**

[![PyPI version](https://badge.fury.io/py/quicketl.svg)](https://pypi.org/project/quicketl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

QuickETL is a configuration-driven ETL framework that provides a simple, unified API for data processing across multiple compute backends including DuckDB, Polars, Spark, and pandas.

**[Documentation](https://quicketl.com)** | **[GitHub](https://github.com/ameijin/quicketl)**

## Features

- **20+ Backends**: DuckDB, Polars, Spark, pandas, Snowflake, BigQuery, and more via Ibis
- **Configuration-driven**: Define pipelines in YAML with variable substitution
- **Quality Checks**: Built-in validation (not_null, unique, row_count, accepted_values)
- **12 Transforms**: filter, aggregate, join, derive_column, and more
- **CLI & Python API**: Use `quicketl run` or the Pipeline builder
- **Cloud Storage**: S3, GCS, Azure via fsspec

## Installation

```bash
pip install quicketl
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

Or use Python:

```python
from quicketl import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()
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
  - op: aggregate
    group_by: [region]
    aggs:
      total: sum(amount)

sink:
  type: file
  path: output.parquet
```

## Documentation

Full documentation, tutorials, and API reference at **[quicketl.com](https://quicketl.com)**

- [Getting Started](https://quicketl.com/getting-started/)
- [Pipeline Configuration](https://quicketl.com/configuration/)
- [Supported Backends](https://quicketl.com/backends/)
- [CLI Reference](https://quicketl.com/cli/)

## License

MIT License - see [LICENSE](LICENSE) for details.
