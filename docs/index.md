# ETLX

<div class="hero" markdown>

**Configuration-driven ETL for Python**

Build data pipelines in YAML or Python with support for 20+ compute backends.

[Get Started](getting-started/index.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/etlx/etlx){ .md-button }

</div>

---

## Why ETLX?

ETLX provides a **unified API** for data transformation across multiple compute engines. Write your pipeline once, run it anywhere - from local DuckDB to distributed Spark to cloud warehouses like Snowflake and BigQuery.

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } **Configuration-Driven**

    ---

    Define pipelines in YAML with variable substitution. No code required for common ETL patterns.

-   :material-swap-horizontal:{ .lg .middle } **Multi-Backend**

    ---

    Run the same pipeline on DuckDB, Polars, Spark, Snowflake, BigQuery, and more via Ibis.

-   :material-check-circle:{ .lg .middle } **Quality Checks**

    ---

    Built-in data quality validation with not_null, unique, row_count, and custom expressions.

-   :material-console:{ .lg .middle } **CLI & API**

    ---

    Use the `etlx` CLI for quick runs or the Python API for programmatic control.

</div>

---

## Quick Example

=== "YAML"

    ```yaml title="pipeline.yml"
    name: sales_summary
    engine: duckdb

    source:
      type: file
      path: data/sales.csv
      format: csv

    transforms:
      - op: filter
        predicate: amount > 0
      - op: aggregate
        group_by: [region]
        aggs:
          total_sales: sum(amount)
          order_count: count(*)

    checks:
      - type: not_null
        columns: [region, total_sales]

    sink:
      type: file
      path: output/sales_by_region.parquet
      format: parquet
    ```

    ```bash
    etlx run pipeline.yml
    ```

=== "Python"

    ```python
    from etlx import Pipeline
    from etlx.config.models import FileSource, FileSink
    from etlx.config.transforms import FilterTransform, AggregateTransform

    pipeline = (
        Pipeline("sales_summary", engine="duckdb")
        .source(FileSource(path="data/sales.csv", format="csv"))
        .transform(FilterTransform(predicate="amount > 0"))
        .transform(AggregateTransform(
            group_by=["region"],
            aggs={"total_sales": "sum(amount)", "order_count": "count(*)"}
        ))
        .sink(FileSink(path="output/sales_by_region.parquet"))
    )

    result = pipeline.run()
    print(f"Processed {result.rows_processed} rows")
    ```

---

## Installation

```bash
# Basic installation (includes DuckDB + Polars)
pip install quicketl

# With cloud storage support
pip install quicketl[aws]      # S3
pip install quicketl[gcp]      # GCS + BigQuery
pip install quicketl[azure]    # Azure ADLS

# With additional backends
pip install quicketl[spark]
pip install quicketl[snowflake]
```

---

## Features

### 12 Transform Operations

| Transform | Description |
|-----------|-------------|
| `select` | Choose and reorder columns |
| `rename` | Rename columns |
| `filter` | Filter rows with SQL predicates |
| `derive_column` | Create computed columns |
| `cast` | Convert column types |
| `fill_null` | Replace null values |
| `dedup` | Remove duplicates |
| `sort` | Order rows |
| `join` | Join datasets |
| `aggregate` | Group and aggregate |
| `union` | Combine datasets vertically |
| `limit` | Limit row count |

### 5 Quality Checks

| Check | Description |
|-------|-------------|
| `not_null` | Ensure columns have no null values |
| `unique` | Verify uniqueness constraints |
| `row_count` | Validate row count bounds |
| `accepted_values` | Check values against whitelist |
| `expression` | Custom SQL predicate validation |

### Supported Backends

| Backend | Type | Included |
|---------|------|----------|
| DuckDB | Local | Yes |
| Polars | Local | Yes |
| DataFusion | Local | Optional |
| Spark | Distributed | Optional |
| Snowflake | Cloud DW | Optional |
| BigQuery | Cloud DW | Optional |
| PostgreSQL | Database | Optional |
| MySQL | Database | Optional |

---

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---

    Install ETLX and run your first pipeline in 5 minutes.

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **User Guide**

    ---

    Learn about transforms, quality checks, and configuration.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   :material-code-tags:{ .lg .middle } **API Reference**

    ---

    Explore the Python API for programmatic pipeline building.

    [:octicons-arrow-right-24: Python API](api/index.md)

-   :material-lightbulb:{ .lg .middle } **Examples**

    ---

    See complete examples for common ETL patterns.

    [:octicons-arrow-right-24: Examples](examples/index.md)

</div>
