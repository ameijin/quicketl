# Medallion Architecture Workflow

A complete example of orchestrating a Bronze → Silver → Gold medallion architecture using QuickETL workflows.

## Overview

The medallion architecture is a common data lakehouse pattern with three layers:

- **Bronze**: Raw data ingestion (unchanged from source)
- **Silver**: Cleaned, deduplicated, and enriched data
- **Gold**: Business-ready aggregates and reporting tables

This example shows how to orchestrate all three layers with a single workflow.

## Project Structure

```
my_project/
├── workflows/
│   └── medallion.yml           # Workflow definition
├── pipelines/
│   ├── bronze/
│   │   ├── ingest_users.yml
│   │   ├── ingest_events.yml
│   │   └── ingest_payments.yml
│   ├── silver/
│   │   ├── clean_users.yml
│   │   ├── clean_events.yml
│   │   └── agg_revenue.yml
│   └── gold/
│       └── load_reporting.yml
└── data/
    ├── raw/                    # Source files
    ├── bronze/                 # Bronze parquet
    ├── silver/                 # Silver parquet
    └── gold/                   # Gold parquet or DB
```

## Workflow Definition

```yaml
# workflows/medallion.yml
name: medallion_etl
description: Complete Bronze -> Silver -> Gold data pipeline

variables:
  DATA_DIR: ./data
  RUN_DATE: "${RUN_DATE:-today}"

stages:
  # ==========================================================================
  # Bronze Layer - Raw Data Ingestion
  # ==========================================================================
  - name: bronze
    description: Ingest raw source files to bronze parquet
    parallel: true  # All ingestions run concurrently
    pipelines:
      - path: ../pipelines/bronze/ingest_users.yml
      - path: ../pipelines/bronze/ingest_events.yml
      - path: ../pipelines/bronze/ingest_payments.yml

  # ==========================================================================
  # Silver Layer - Cleaning & Transformation
  # ==========================================================================
  - name: silver_clean
    description: Clean and deduplicate bronze data
    depends_on: [bronze]
    parallel: true
    pipelines:
      - path: ../pipelines/silver/clean_users.yml
      - path: ../pipelines/silver/clean_events.yml

  - name: silver_agg
    description: Create aggregations from cleaned data
    depends_on: [silver_clean]
    parallel: false
    pipelines:
      - path: ../pipelines/silver/agg_revenue.yml

  # ==========================================================================
  # Gold Layer - Reporting
  # ==========================================================================
  - name: gold
    description: Load aggregates to reporting layer
    depends_on: [silver_agg]
    pipelines:
      - path: ../pipelines/gold/load_reporting.yml
```

## Bronze Layer Pipelines

### Ingest Users

```yaml
# pipelines/bronze/ingest_users.yml
name: ingest_users
description: Ingest raw user data to bronze
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/raw/users.csv
  format: csv

transforms:
  - op: cast
    columns:
      user_id: int64
      created_at: timestamp
      balance: float64

checks:
  - type: not_null
    columns: [user_id, email]
  - type: row_count
    min: 1

sink:
  type: file
  path: ${DATA_DIR}/bronze/users.parquet
  format: parquet
```

### Ingest Events

```yaml
# pipelines/bronze/ingest_events.yml
name: ingest_events
description: Ingest raw event data to bronze
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/raw/events.jsonl
  format: json

transforms:
  - op: cast
    columns:
      event_id: string
      user_id: int64
      timestamp: timestamp
      duration_ms: int64

  - op: derive_column
    name: ingested_at
    expression: "current_timestamp"

checks:
  - type: not_null
    columns: [event_id, user_id]

sink:
  type: file
  path: ${DATA_DIR}/bronze/events.parquet
  format: parquet
```

### Ingest Payments

```yaml
# pipelines/bronze/ingest_payments.yml
name: ingest_payments
description: Ingest raw payment data to bronze
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/raw/payments.csv
  format: csv

transforms:
  - op: cast
    columns:
      payment_id: string
      user_id: int64
      amount: float64
      currency: string
      created_at: timestamp

checks:
  - type: not_null
    columns: [payment_id, user_id, amount]
  - type: accepted_values
    column: currency
    values: [USD, EUR, GBP]

sink:
  type: file
  path: ${DATA_DIR}/bronze/payments.parquet
  format: parquet
```

## Silver Layer Pipelines

### Clean Users

```yaml
# pipelines/silver/clean_users.yml
name: clean_users
description: Clean and deduplicate user data
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/bronze/users.parquet

transforms:
  # Remove invalid records
  - op: filter
    predicate: "user_id IS NOT NULL AND email IS NOT NULL"

  # Deduplicate by user_id (keep latest)
  - op: dedup
    columns: [user_id]
    keep: last
    order_by: [created_at]

  # Add derived columns
  - op: derive_column
    name: account_age_days
    expression: "date_diff('day', created_at, current_date)"

  - op: sort
    columns:
      - column: user_id
        ascending: true

checks:
  - type: unique
    columns: [user_id]
  - type: expression
    expression: "balance >= 0"
    description: Balance must be non-negative

sink:
  type: file
  path: ${DATA_DIR}/silver/users.parquet
  format: parquet
```

### Clean Events

```yaml
# pipelines/silver/clean_events.yml
name: clean_events
description: Clean and enrich event data
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/bronze/events.parquet

transforms:
  # Filter valid events
  - op: filter
    predicate: "event_id IS NOT NULL AND duration_ms >= 0"

  # Deduplicate
  - op: dedup
    columns: [event_id]

  # Derive date for partitioning
  - op: derive_column
    name: event_date
    expression: "date_trunc('day', timestamp)"

  - op: sort
    columns:
      - column: timestamp
        ascending: false

checks:
  - type: not_null
    columns: [event_id, user_id, timestamp]
  - type: expression
    expression: "duration_ms >= 0"

sink:
  type: file
  path: ${DATA_DIR}/silver/events.parquet
  format: parquet
```

### Aggregate Revenue

```yaml
# pipelines/silver/agg_revenue.yml
name: agg_revenue
description: Aggregate daily revenue by currency
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/bronze/payments.parquet

transforms:
  # Filter completed payments only
  - op: filter
    predicate: "status = 'completed'"

  # Aggregate by date and currency
  - op: aggregate
    group_by: [payment_date, currency]
    aggregations:
      - column: amount
        function: sum
        alias: total_revenue
      - column: payment_id
        function: count
        alias: transaction_count
      - column: amount
        function: avg
        alias: avg_transaction

  - op: sort
    columns:
      - column: payment_date
        ascending: false

checks:
  - type: not_null
    columns: [payment_date, currency, total_revenue]
  - type: expression
    expression: "total_revenue >= 0"

sink:
  type: file
  path: ${DATA_DIR}/silver/revenue_daily.parquet
  format: parquet
```

## Gold Layer Pipeline

### Load Reporting

```yaml
# pipelines/gold/load_reporting.yml
name: load_reporting
description: Load revenue aggregates to reporting database
engine: duckdb

source:
  type: file
  path: ${DATA_DIR}/silver/revenue_daily.parquet

transforms:
  - op: rename
    columns:
      payment_date: report_date

  - op: select
    columns:
      - report_date
      - currency
      - total_revenue
      - transaction_count
      - avg_transaction

checks:
  - type: not_null
    columns: [report_date, currency, total_revenue]
  - type: unique
    columns: [report_date, currency]

sink:
  type: database
  connection: ${DATABASE_URL}
  table: gold.revenue_summary
  mode: upsert
  key_columns: [report_date, currency]
```

## Running the Workflow

### Local Development

```bash
# Validate configuration
quicketl workflow validate workflows/medallion.yml --verbose

# View execution order
quicketl workflow info workflows/medallion.yml

# Run complete workflow
quicketl workflow run workflows/medallion.yml

# Run with custom date
quicketl workflow run workflows/medallion.yml --var RUN_DATE=2025-01-15

# Dry run (no writes)
quicketl workflow run workflows/medallion.yml --dry-run
```

### Generate Airflow DAG

```bash
quicketl workflow generate workflows/medallion.yml \
  --target airflow \
  --schedule "0 6 * * *" \
  -o dags/medallion_dag.py
```

### Generate Prefect Flow

```bash
quicketl workflow generate workflows/medallion.yml \
  --target prefect \
  -o flows/medallion_flow.py
```

## Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Stage: bronze                             │
│                        (parallel: true)                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │ ingest_users  │ │ ingest_events │ │ingest_payments│          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Stage: silver_clean                          │
│                      (parallel: true)                            │
│        ┌───────────────┐     ┌───────────────┐                  │
│        │  clean_users  │     │ clean_events  │                  │
│        └───────────────┘     └───────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Stage: silver_agg                           │
│                      (parallel: false)                           │
│              ┌─────────────────────────┐                        │
│              │      agg_revenue        │                        │
│              └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage: gold                               │
│                      (parallel: false)                           │
│              ┌─────────────────────────┐                        │
│              │    load_reporting       │                        │
│              └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Use parallel: true** for independent pipelines within a stage
2. **Define clear dependencies** with `depends_on` to ensure correct ordering
3. **Add quality checks** at each layer to catch issues early
4. **Use variables** for environment-specific paths and dates
5. **Validate before running** with `workflow validate --verbose`
6. **Generate DAGs** from the same workflow used for local development

## Related

- [Workflow Configuration](../guides/workflows/workflow-yaml.md) - Complete YAML reference
- [DAG Generation](../guides/workflows/dag-generation.md) - Generate Airflow/Prefect code
- [Airflow Integration](../integrations/airflow.md) - Advanced Airflow patterns
