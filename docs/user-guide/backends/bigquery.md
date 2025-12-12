# BigQuery Backend

Google BigQuery is a serverless, highly scalable data warehouse. ETLX pushes transformations to BigQuery for efficient in-warehouse processing.

## Installation

```bash
pip install quicketl[bigquery]
# or
uv add quicketl[bigquery]
```

## When to Use BigQuery

**Ideal for:**

- Data already in Google Cloud
- Serverless, pay-per-query model
- Petabyte-scale analytics
- Integration with GCP services

**Consider alternatives when:**

- Data is outside GCP (egress costs)
- Predictable compute costs needed
- Real-time processing required

## Configuration

### Authentication

#### Service Account (Recommended for Production)

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export BIGQUERY_PROJECT=my-project-id
```

#### Application Default Credentials (Development)

```bash
gcloud auth application-default login
export BIGQUERY_PROJECT=my-project-id
```

### Environment Variables

```bash
export BIGQUERY_PROJECT=my-project-id
export BIGQUERY_DATASET=analytics
export BIGQUERY_LOCATION=US
```

### Basic Pipeline

```yaml
name: bigquery_etl
engine: bigquery

source:
  type: database
  connection: bigquery
  table: raw_data.sales

transforms:
  - op: filter
    predicate: transaction_date >= '2025-01-01'
  - op: aggregate
    group_by: [region, product_type]
    aggregations:
      total_revenue: sum(amount)
      transaction_count: count(*)

sink:
  type: database
  connection: bigquery
  table: analytics.sales_summary
  mode: replace
```

## Supported Features

### Transforms

All transforms are pushed to BigQuery SQL:

| Transform | Support | BigQuery SQL |
|-----------|---------|--------------|
| select | Full | `SELECT` |
| rename | Full | `AS alias` |
| filter | Full | `WHERE` |
| derive_column | Full | Expressions |
| cast | Full | `CAST()` |
| fill_null | Full | `COALESCE()` / `IFNULL()` |
| dedup | Full | `QUALIFY ROW_NUMBER()` |
| sort | Full | `ORDER BY` |
| join | Full | `JOIN` |
| aggregate | Full | `GROUP BY` |
| union | Full | `UNION ALL` |
| limit | Full | `LIMIT` |

### Data Types

| ETLX Type | BigQuery Type |
|-----------|---------------|
| string | STRING |
| int | INT64 |
| float | FLOAT64 |
| bool | BOOL |
| date | DATE |
| timestamp | TIMESTAMP |
| decimal | NUMERIC |

## Reading Data

### From Tables

```yaml
source:
  type: database
  connection: bigquery
  table: project.dataset.table_name
```

### From Queries

```yaml
source:
  type: database
  connection: bigquery
  query: |
    SELECT *
    FROM `project.dataset.table`
    WHERE _PARTITIONDATE >= '2025-01-01'
```

### From External Tables (GCS)

```yaml
source:
  type: database
  connection: bigquery
  query: |
    SELECT * FROM EXTERNAL_QUERY(
      'us.my_connection',
      'SELECT * FROM external_table'
    )
```

## Writing Data

### Replace Mode

```yaml
sink:
  type: database
  connection: bigquery
  table: project.dataset.output
  mode: replace  # WRITE_TRUNCATE
```

### Append Mode

```yaml
sink:
  type: database
  connection: bigquery
  table: project.dataset.output
  mode: append  # WRITE_APPEND
```

### Partitioned Tables

```yaml
sink:
  type: database
  connection: bigquery
  table: project.dataset.output
  mode: replace
  options:
    partition_field: date
    partition_type: DAY
```

## Cost Optimization

### 1. Use Partitioned Tables

Partition by date to reduce bytes scanned:

```yaml
source:
  type: database
  connection: bigquery
  query: |
    SELECT * FROM `project.dataset.events`
    WHERE _PARTITIONDATE BETWEEN '2025-01-01' AND '2025-01-31'
```

### 2. Select Only Needed Columns

BigQuery charges by bytes scanned:

```yaml
transforms:
  - op: select
    columns: [id, amount, date]  # Don't SELECT *
```

### 3. Use Clustering

For frequently filtered columns:

```sql
CREATE TABLE analytics.sales
PARTITION BY date
CLUSTER BY region, product_type
AS SELECT * FROM raw.sales;
```

### 4. Materialize Intermediate Results

For complex pipelines, use temp tables:

```yaml
sink:
  type: database
  connection: bigquery
  table: project.dataset.temp_results
  mode: replace
  options:
    expiration_hours: 24
```

## Example: Analytics Pipeline

```yaml
name: daily_analytics
description: Compute daily KPIs from event data
engine: bigquery

source:
  type: database
  connection: bigquery
  query: |
    SELECT
      user_id,
      event_type,
      event_timestamp,
      JSON_EXTRACT_SCALAR(properties, '$.value') as value,
      JSON_EXTRACT_SCALAR(properties, '$.category') as category
    FROM `analytics.events`
    WHERE DATE(event_timestamp) = CURRENT_DATE() - 1

transforms:
  - op: cast
    columns:
      value: float

  - op: filter
    predicate: event_type IN ('purchase', 'signup', 'pageview')

  - op: aggregate
    group_by: [event_type, category]
    aggregations:
      total_value: sum(value)
      unique_users: count(distinct user_id)
      event_count: count(*)

checks:
  - check: not_null
    columns: [event_type, category]
  - check: row_count
    min: 1

sink:
  type: database
  connection: bigquery
  table: analytics.daily_kpis
  mode: append
```

## Streaming Inserts

For real-time data, use streaming:

```yaml
sink:
  type: database
  connection: bigquery
  table: project.dataset.stream_table
  mode: stream
```

!!! warning "Streaming Costs"
    Streaming inserts have additional costs. Use batch loading for large volumes.

## Limitations

1. **Query Costs**: Pay per TB scanned
2. **DML Quotas**: Limited UPDATE/DELETE operations per day
3. **Streaming Limits**: 100,000 rows/second per table
4. **Latency**: Query startup time ~2-5 seconds

## Troubleshooting

### Authentication Failed

```
google.auth.exceptions.DefaultCredentialsError
```

**Solutions**:
1. Set `GOOGLE_APPLICATION_CREDENTIALS`
2. Run `gcloud auth application-default login`
3. Verify service account has BigQuery permissions

### Dataset Not Found

```
NotFound: 404 Not found: Dataset project:dataset
```

**Solution**: Verify dataset exists and you have access:
```bash
bq ls project:dataset
```

### Query Quota Exceeded

```
Quota exceeded: Your project exceeded quota for concurrent queries
```

**Solution**: Wait and retry, or request quota increase.

### Bytes Billed Too High

**Prevention**:
1. Always filter by partition column
2. Select only needed columns
3. Use `--dry-run` to estimate costs:
```bash
bq query --dry_run "SELECT * FROM dataset.table"
```

## Permissions Required

The service account needs these IAM roles:

- `roles/bigquery.dataViewer` - Read tables
- `roles/bigquery.dataEditor` - Write tables
- `roles/bigquery.jobUser` - Run queries

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:etlx@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Cloud Storage](../io/cloud-storage.md) - GCS integration
- [Database Sources](../io/database-sources.md) - Database configuration
