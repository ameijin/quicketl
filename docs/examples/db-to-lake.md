# Database to Data Lake Example

This example demonstrates extracting data from a relational database and loading it into a cloud data lake.

## Overview

**Scenario**: Extract transactional data from PostgreSQL and load to S3 data lake in Parquet format for analytics.

**Pattern**: Database → Transform → Data Lake (ELT)

## Architecture

```
PostgreSQL (OLTP)     S3 Data Lake
┌─────────────┐       ┌─────────────┐
│   orders    │       │ raw/        │
│   products  │  ───► │ processed/  │
│   customers │       │ analytics/  │
└─────────────┘       └─────────────┘
```

## Prerequisites

### PostgreSQL Connection

```bash
export POSTGRES_HOST=db.example.com
export POSTGRES_PORT=5432
export POSTGRES_USER=etl_reader
export POSTGRES_PASSWORD=secret
export POSTGRES_DATABASE=production
```

### AWS Credentials

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

## Pipeline Configurations

### Extract Orders

`pipelines/extract_orders.yml`:

```yaml
name: extract_orders_to_lake
description: Extract daily orders to S3 data lake
engine: duckdb

source:
  type: database
  connection: postgres
  query: |
    SELECT
      order_id,
      customer_id,
      order_date,
      status,
      total_amount,
      shipping_address,
      created_at,
      updated_at
    FROM orders
    WHERE order_date = '${DATE}'
      AND status != 'deleted'

transforms:
  # Add extraction metadata
  - op: derive_column
    name: extracted_at
    expr: current_timestamp

  - op: derive_column
    name: extract_date
    expr: date('${DATE}')

checks:
  - check: not_null
    columns: [order_id, customer_id, total_amount]

  - check: row_count
    min: 1

sink:
  type: file
  path: s3://data-lake/raw/orders/date=${DATE}/orders.parquet
  format: parquet
  mode: replace
```

### Extract Customers (Full Snapshot)

`pipelines/extract_customers.yml`:

```yaml
name: extract_customers_to_lake
description: Full snapshot of customers to S3
engine: duckdb

source:
  type: database
  connection: postgres
  query: |
    SELECT
      customer_id,
      email,
      first_name,
      last_name,
      phone,
      region,
      segment,
      lifetime_value,
      created_at,
      updated_at
    FROM customers
    WHERE status = 'active'

transforms:
  - op: derive_column
    name: extracted_at
    expr: current_timestamp

  # Hash PII for analytics
  - op: derive_column
    name: email_hash
    expr: md5(lower(email))

  # Remove raw PII for analytics layer
  - op: select
    columns:
      - customer_id
      - email_hash
      - first_name
      - region
      - segment
      - lifetime_value
      - created_at
      - extracted_at

checks:
  - check: not_null
    columns: [customer_id, region]

  - check: unique
    columns: [customer_id]

sink:
  type: file
  path: s3://data-lake/raw/customers/snapshot.parquet
  format: parquet
  mode: replace
```

### Incremental Extract with Change Data Capture

`pipelines/extract_incremental.yml`:

```yaml
name: incremental_orders
description: Extract only changed orders since last run
engine: duckdb

source:
  type: database
  connection: postgres
  query: |
    SELECT
      order_id,
      customer_id,
      order_date,
      status,
      total_amount,
      updated_at
    FROM orders
    WHERE updated_at >= '${LAST_EXTRACT}'
      AND updated_at < '${CURRENT_EXTRACT}'

transforms:
  - op: derive_column
    name: cdc_operation
    expr: |
      case
        when created_at >= '${LAST_EXTRACT}' then 'INSERT'
        else 'UPDATE'
      end

  - op: derive_column
    name: extracted_at
    expr: timestamp('${CURRENT_EXTRACT}')

checks:
  - check: not_null
    columns: [order_id, cdc_operation]

sink:
  type: file
  path: s3://data-lake/cdc/orders/${CURRENT_EXTRACT}/changes.parquet
  format: parquet
```

## Running the Pipelines

### Daily Full Extract

```bash
# Extract today's orders
quicketl run pipelines/extract_orders.yml --var DATE=$(date +%Y-%m-%d)

# Extract customer snapshot
quicketl run pipelines/extract_customers.yml
```

### Incremental Extract

```bash
# Get last extract timestamp from watermark table or file
LAST_EXTRACT=$(cat /var/quicketl/watermarks/orders.txt)
CURRENT_EXTRACT=$(date -u +%Y-%m-%dT%H:%M:%S)

# Run incremental
quicketl run pipelines/extract_incremental.yml \
  --var LAST_EXTRACT=$LAST_EXTRACT \
  --var CURRENT_EXTRACT=$CURRENT_EXTRACT

# Update watermark
echo $CURRENT_EXTRACT > /var/quicketl/watermarks/orders.txt
```

### Orchestration Script

```bash
#!/bin/bash
# extract_to_lake.sh

set -e

DATE=${1:-$(date +%Y-%m-%d)}
LOG_DIR=/var/log/quicketl

echo "$(date): Starting extraction for $DATE"

# Extract orders
if quicketl run pipelines/extract_orders.yml --var DATE=$DATE --json > $LOG_DIR/orders_$DATE.json; then
    echo "$(date): Orders extracted successfully"
else
    echo "$(date): Orders extraction failed"
    exit 1
fi

# Extract products
if quicketl run pipelines/extract_products.yml --json > $LOG_DIR/products_$DATE.json; then
    echo "$(date): Products extracted successfully"
else
    echo "$(date): Products extraction failed"
    exit 1
fi

# Extract customers
if quicketl run pipelines/extract_customers.yml --json > $LOG_DIR/customers_$DATE.json; then
    echo "$(date): Customers extracted successfully"
else
    echo "$(date): Customers extraction failed"
    exit 1
fi

echo "$(date): All extractions completed successfully"
```

## Data Lake Organization

```
s3://data-lake/
├── raw/                          # Raw extracts
│   ├── orders/
│   │   ├── date=2025-01-15/
│   │   │   └── orders.parquet
│   │   └── date=2025-01-16/
│   │       └── orders.parquet
│   ├── customers/
│   │   └── snapshot.parquet
│   └── products/
│       └── snapshot.parquet
├── cdc/                          # Change data capture
│   └── orders/
│       ├── 2025-01-15T00:00:00/
│       └── 2025-01-15T06:00:00/
└── processed/                    # Transformed data
    └── daily_metrics/
        └── date=2025-01-15/
```

## Partitioning Strategy

For large tables, partition by date:

```yaml
sink:
  type: file
  path: s3://data-lake/raw/events/
  format: parquet
  options:
    partition_by: [date, region]
```

Output structure:

```
s3://data-lake/raw/events/
├── date=2025-01-15/
│   ├── region=north/
│   │   └── part-0001.parquet
│   └── region=south/
│       └── part-0001.parquet
└── date=2025-01-16/
    └── ...
```

## Monitoring

### JSON Output for Metrics

```bash
RESULT=$(quicketl run pipelines/extract_orders.yml --var DATE=$DATE --json)

ROWS=$(echo $RESULT | jq -r '.rows_written')
DURATION=$(echo $RESULT | jq -r '.duration_ms')

# Log to CloudWatch
aws cloudwatch put-metric-data \
  --namespace "ETLX/DataLake" \
  --metric-name "RowsExtracted" \
  --value $ROWS \
  --dimensions Table=orders,Date=$DATE
```

## Next Steps

- [Cloud ETL Example](cloud-etl.md) - Full cloud pipeline
- [Airflow DAG Example](airflow-dag.md) - Orchestration
- [Production Best Practices](../best-practices/production.md)
