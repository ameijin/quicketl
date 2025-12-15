# Examples

This section contains complete, runnable examples demonstrating common QuickETL patterns and use cases. Each example includes:

- Complete YAML configuration
- Sample data
- Expected output
- Step-by-step explanation

## Getting Started Examples

### [Basic Pipeline](basic-pipeline.md)

A minimal pipeline that reads a CSV, applies filters, and writes to Parquet. Perfect for understanding QuickETL fundamentals.

```yaml
name: basic_example
source:
  type: file
  path: data/input.csv
  format: csv
transforms:
  - op: filter
    predicate: amount > 0
sink:
  type: file
  path: output/results.parquet
  format: parquet
```

## Data Processing Examples

### [Multi-Source Join](multi-source-join.md)

Combine data from multiple sources (orders + customers + products) into a single enriched dataset.

```yaml
transforms:
  - op: join
    right:
      type: file
      path: data/customers.csv
      format: csv
    on: [customer_id]
    how: left
```

### [Aggregation Pipeline](aggregation.md)

Compute metrics, summaries, and roll-ups from transactional data.

```yaml
transforms:
  - op: aggregate
    group_by: [region, category]
    aggregations:
      total_revenue: sum(amount)
      order_count: count(*)
      avg_order_value: avg(amount)
```

## Workflow Examples

### [Medallion Workflow](medallion-workflow.md)

Complete Bronze → Silver → Gold medallion architecture with multi-stage workflow orchestration.

```yaml
stages:
  - name: bronze
    parallel: true
    pipelines:
      - path: pipelines/bronze/ingest_users.yml
      - path: pipelines/bronze/ingest_events.yml

  - name: silver
    depends_on: [bronze]
    pipelines:
      - path: pipelines/silver/clean_users.yml
```

## Cloud & Production Examples

### [Cloud ETL](cloud-etl.md)

End-to-end pipeline reading from S3, transforming with Spark, and loading to a data warehouse.

```yaml
engine: spark
source:
  type: file
  path: s3://bucket/raw/*.parquet
  format: parquet
sink:
  type: database
  connection: snowflake
  table: analytics.fact_sales
```

### [Airflow DAG](airflow-dag.md)

Complete Airflow DAG with QuickETL tasks, error handling, and monitoring.

```python
@quicketl_task(config="pipelines/daily.yml")
def process_daily(**context):
    return {"DATE": context["ds"]}
```

## Example Categories

| Category | Examples | Description |
|----------|----------|-------------|
| **Basic** | [Basic Pipeline](basic-pipeline.md) | Core concepts |
| **Joins** | [Multi-Source Join](multi-source-join.md) | Combining data |
| **Analytics** | [Aggregation](aggregation.md) | Metrics and summaries |
| **Workflows** | [Medallion Workflow](medallion-workflow.md) | Multi-pipeline orchestration |
| **Cloud** | [Cloud ETL](cloud-etl.md) | Production cloud pipelines |
| **Orchestration** | [Airflow DAG](airflow-dag.md) | Airflow integration |

## Running Examples

### Setup

```bash
# Clone or create project
quicketl init examples
cd examples

# Install dependencies
pip install quicketl[duckdb]
```

### Run Any Example

```bash
# Validate first
quicketl validate pipelines/example.yml

# Run
quicketl run pipelines/example.yml
```

### With Variables

```bash
quicketl run pipelines/example.yml --var DATE=2025-01-15
```

## Sample Data

All examples use sample data available in the `docs/assets/data/` directory:

| File | Description | Rows |
|------|-------------|------|
| `sales.csv` | Transaction records | 12 |
| `customers.csv` | Customer master data | 5 |
| `products.csv` | Product catalog | 10 |

## Contributing Examples

Have a useful pattern? Contribute an example:

1. Create a new markdown file in `docs/examples/`
2. Include complete, runnable YAML
3. Add sample input/output data
4. Document each step

See [Contributing Guide](https://github.com/ameijin/quicketl/blob/mahttps://github.com/ameijin/quicketl/blob/main/CONTRIBUTING.md) for details.

## Related

- [Getting Started](../getting-started/quickstart.md) - First steps with QuickETL
- [User Guide](../guides/configuration/pipeline-yaml.md) - Complete reference
- [Best Practices](../best-practices/pipeline-design.md) - Design patterns
