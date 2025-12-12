# Cloud ETL Example

This example demonstrates a production-ready pipeline that reads from cloud storage (S3), processes with a distributed engine (Spark), and writes to a data warehouse (Snowflake).

## Overview

**Scenario**: Daily ETL pipeline that:

1. Reads raw event data from S3
2. Joins with dimension tables from S3
3. Aggregates metrics
4. Loads to Snowflake data warehouse

## Prerequisites

### AWS Configuration

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### Snowflake Configuration

```bash
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=etl_user
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_DATABASE=analytics
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_WAREHOUSE=etl_warehouse
```

## Data Architecture

```
S3 Raw Layer                    Snowflake
├── events/                     ├── raw.events
│   └── date=2025-01-15/       ├── dim.products
│       └── *.parquet          ├── dim.customers
├── products/                   └── analytics.daily_metrics
│   └── products.parquet
└── customers/
    └── customers.parquet
```

## Pipeline Configuration

Create `pipelines/cloud_etl.yml`:

```yaml
name: daily_cloud_etl
description: Process daily events from S3 to Snowflake
engine: spark

# Environment variables for dates
# Run with: quicketl run pipeline.yml --var DATE=2025-01-15

source:
  type: file
  path: s3://data-lake/raw/events/date=${DATE}/*.parquet
  format: parquet

transforms:
  # Filter valid events
  - op: filter
    predicate: |
      event_type IN ('purchase', 'view', 'click')
      AND user_id IS NOT NULL

  # Join with product dimension
  - op: join
    right:
      type: file
      path: s3://data-lake/dim/products/products.parquet
      format: parquet
    on: [product_id]
    how: left

  # Join with customer dimension
  - op: join
    right:
      type: file
      path: s3://data-lake/dim/customers/customers.parquet
      format: parquet
    on: [user_id]
    how: left

  # Rename joined columns
  - op: rename
    columns:
      name: product_name
      name_1: customer_name
      category: product_category
      segment: customer_segment

  # Calculate derived metrics
  - op: derive_column
    name: event_date
    expr: date(event_timestamp)

  - op: derive_column
    name: event_hour
    expr: hour(event_timestamp)

  - op: derive_column
    name: revenue
    expr: |
      case
        when event_type = 'purchase' then quantity * unit_price
        else 0
      end

  # Aggregate daily metrics
  - op: aggregate
    group_by:
      - event_date
      - event_hour
      - product_category
      - customer_segment
      - event_type
    aggregations:
      event_count: count(*)
      unique_users: count(distinct user_id)
      total_revenue: sum(revenue)
      total_quantity: sum(quantity)

# Data quality checks
checks:
  - check: not_null
    columns: [event_date, event_type, event_count]

  - check: row_count
    min: 1

  - check: expression
    expr: total_revenue >= 0

  - check: accepted_values
    column: event_type
    values: [purchase, view, click]

# Write to Snowflake
sink:
  type: database
  connection: snowflake
  table: analytics.daily_metrics
  mode: merge
  merge_keys: [event_date, event_hour, product_category, customer_segment, event_type]
```

## Running the Pipeline

### Daily Execution

```bash
# Today's date
quicketl run pipelines/cloud_etl.yml --var DATE=$(date +%Y-%m-%d)

# Specific date
quicketl run pipelines/cloud_etl.yml --var DATE=2025-01-15
```

### With JSON Output (for monitoring)

```bash
quicketl run pipelines/cloud_etl.yml --var DATE=2025-01-15 --json
```

Output:

```json
{
  "pipeline_name": "daily_cloud_etl",
  "status": "SUCCESS",
  "duration_ms": 45230.5,
  "rows_processed": 1250000,
  "rows_written": 8640,
  "checks_passed": 4,
  "checks_failed": 0
}
```

## Incremental Loading Variant

For incremental loads, use merge mode with date filtering:

```yaml
name: incremental_cloud_etl
description: Incremental load with watermark

source:
  type: database
  connection: snowflake
  query: |
    SELECT MAX(event_timestamp) as watermark
    FROM analytics.events

# Store watermark for use in main source
# This example shows the pattern - actual implementation varies
```

## Multi-Region Pipeline

Process data from multiple regions in parallel:

```yaml
name: multi_region_etl
description: Process all regions

source:
  type: file
  path: s3://data-lake/raw/events/region=${REGION}/date=${DATE}/*.parquet
  format: parquet

# ... transforms ...

sink:
  type: database
  connection: snowflake
  table: analytics.regional_metrics_${REGION}
  mode: replace
```

Run for each region:

```bash
for region in us-east us-west eu-west ap-south; do
  quicketl run pipelines/multi_region.yml \
    --var DATE=2025-01-15 \
    --var REGION=$region &
done
wait
```

## Cost Optimization

### 1. Use Appropriate Spark Configuration

```bash
# For small jobs
export SPARK_EXECUTOR_INSTANCES=2
export SPARK_EXECUTOR_MEMORY=4g

# For large jobs
export SPARK_EXECUTOR_INSTANCES=10
export SPARK_EXECUTOR_MEMORY=16g
```

### 2. Partition Output Data

```yaml
sink:
  type: file
  path: s3://data-lake/processed/metrics/
  format: parquet
  options:
    partition_by: [event_date, product_category]
```

### 3. Use Columnar Formats

Always use Parquet for cloud storage:

```yaml
source:
  type: file
  path: s3://bucket/data/*.parquet
  format: parquet  # Not CSV!
```

## Error Handling

### Retry Logic

Wrap in a shell script with retries:

```bash
#!/bin/bash
MAX_RETRIES=3
RETRY_DELAY=300

for i in $(seq 1 $MAX_RETRIES); do
  if quicketl run pipelines/cloud_etl.yml --var DATE=$1; then
    echo "Success on attempt $i"
    exit 0
  fi
  echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."
  sleep $RETRY_DELAY
done

echo "Failed after $MAX_RETRIES attempts"
exit 1
```

### Dead Letter Queue

For failed records:

```yaml
# Main pipeline writes successes
sink:
  type: database
  connection: snowflake
  table: analytics.metrics

# Separate pipeline for failures
# (would be implemented via quality check failure handling)
```

## Monitoring

### CloudWatch Integration

Send metrics to CloudWatch:

```bash
#!/bin/bash
RESULT=$(quicketl run pipelines/cloud_etl.yml --var DATE=$1 --json)

# Extract metrics
DURATION=$(echo $RESULT | jq -r '.duration_ms')
ROWS=$(echo $RESULT | jq -r '.rows_written')
STATUS=$(echo $RESULT | jq -r '.status')

# Send to CloudWatch
aws cloudwatch put-metric-data \
  --namespace "QuickETL/Pipelines" \
  --metric-name "Duration" \
  --value $DURATION \
  --unit Milliseconds \
  --dimensions Pipeline=daily_cloud_etl

aws cloudwatch put-metric-data \
  --namespace "QuickETL/Pipelines" \
  --metric-name "RowsWritten" \
  --value $ROWS \
  --dimensions Pipeline=daily_cloud_etl
```

## BigQuery Variant

For Google Cloud:

```yaml
name: gcs_to_bigquery
engine: bigquery

source:
  type: file
  path: gs://data-lake/raw/events/date=${DATE}/*.parquet
  format: parquet

transforms:
  # Same transforms...

sink:
  type: database
  connection: bigquery
  table: analytics.daily_metrics
  mode: replace
  options:
    partition_field: event_date
    clustering_fields: [product_category, customer_segment]
```

## Next Steps

- [Airflow DAG Example](airflow-dag.md) - Orchestrate cloud pipelines
- [Spark Backend](../guides/backends/distributed.md) - Spark configuration
- [Snowflake Backend](../guides/backends/cloud-warehouses.md#snowflake) - Snowflake setup
- [Production Best Practices](../best-practices/production.md)
