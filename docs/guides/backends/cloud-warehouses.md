# Cloud Data Warehouses

Cloud data warehouses provide serverless, scalable analytics. QuickETL pushes transformations directly to the warehouse for efficient in-warehouse processing.

## Quick Comparison

| Feature | Snowflake | BigQuery |
|---------|-----------|----------|
| **Provider** | Multi-cloud | Google Cloud |
| **Pricing** | Compute + Storage | Per TB scanned |
| **Scaling** | Manual warehouse sizing | Automatic |
| **Best For** | Enterprise, multi-cloud | GCP-native, pay-per-query |

---

## Snowflake {#snowflake}

Snowflake is a cloud-native data warehouse with separated compute and storage.

### Installation

```bash
pip install quicketl[snowflake]
```

### Configuration

Set environment variables:

```bash
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=quicketl_user
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_DATABASE=analytics
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_WAREHOUSE=compute_wh
export SNOWFLAKE_ROLE=analyst_role
```

### Basic Pipeline

```yaml
name: snowflake_etl
engine: snowflake

source:
  type: database
  connection: snowflake
  table: raw_sales

transforms:
  - op: filter
    predicate: sale_date >= '2025-01-01'
  - op: aggregate
    group_by: [region, product_category]
    aggs:
      total_revenue: sum(amount)
      order_count: count(*)

sink:
  type: database
  connection: snowflake
  table: sales_summary
  mode: replace
```

### Write Modes

```yaml
# Replace (TRUNCATE + INSERT)
sink:
  mode: replace

# Append (INSERT only)
sink:
  mode: append

# Merge (UPSERT)
sink:
  mode: merge
  merge_keys: [id]
```

### Key-Pair Authentication

For production:

```bash
export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/rsa_key.p8
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
```

### Cost Optimization

1. **Use appropriate warehouse size** (XS: 1 credit/hr, L: 8 credits/hr)
2. **Filter early** to reduce compute
3. **Use clustering keys** for large tables

```sql
ALTER TABLE sales CLUSTER BY (date, region);
```

### Troubleshooting

**Connection Failed**: Verify account format `account.region`

**Warehouse Suspended**: Auto-resumes, or `ALTER WAREHOUSE wh RESUME`

**Permission Denied**:
```sql
GRANT SELECT ON TABLE raw.sales TO ROLE quicketl_role;
GRANT INSERT ON TABLE analytics.summary TO ROLE quicketl_role;
```

---

## BigQuery {#bigquery}

Google BigQuery is a serverless data warehouse with a pay-per-query model.

### Installation

```bash
pip install quicketl[bigquery]
```

### Configuration

```bash
# Service Account (recommended)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export BIGQUERY_PROJECT=my-project-id

# Or Application Default Credentials
gcloud auth application-default login
```

Additional settings:

```bash
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
    aggs:
      total_revenue: sum(amount)

sink:
  type: database
  connection: bigquery
  table: analytics.sales_summary
  mode: replace
```

### Write Modes

```yaml
# Replace (WRITE_TRUNCATE)
sink:
  mode: replace

# Append (WRITE_APPEND)
sink:
  mode: append

# Partitioned tables
sink:
  options:
    partition_field: date
    partition_type: DAY
```

### Cost Optimization

BigQuery charges per TB scanned:

1. **Use partitioned tables**:
```yaml
source:
  query: |
    SELECT * FROM `project.dataset.events`
    WHERE _PARTITIONDATE BETWEEN '2025-01-01' AND '2025-01-31'
```

2. **Select only needed columns** (don't use SELECT *):
```yaml
transforms:
  - op: select
    columns: [id, amount, date]
```

3. **Use clustering**:
```sql
CREATE TABLE analytics.sales
PARTITION BY date
CLUSTER BY region, product_type
AS SELECT * FROM raw.sales;
```

### Required Permissions

The service account needs these IAM roles:

- `roles/bigquery.dataViewer` - Read tables
- `roles/bigquery.dataEditor` - Write tables
- `roles/bigquery.jobUser` - Run queries

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:quicketl@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### Troubleshooting

**Authentication Failed**: Set `GOOGLE_APPLICATION_CREDENTIALS` or run `gcloud auth application-default login`

**Dataset Not Found**: Verify with `bq ls project:dataset`

**Bytes Billed Too High**: Always filter by partition column, select only needed columns

---

## Choosing Between Snowflake and BigQuery

| Scenario | Recommendation |
|----------|----------------|
| Google Cloud data | BigQuery |
| Multi-cloud / AWS / Azure | Snowflake |
| Predictable compute costs | Snowflake |
| Pay-per-query model | BigQuery |
| Enterprise features | Snowflake |
| GCP ecosystem integration | BigQuery |

## Related

- [Local Backends](local.md) - For development
- [Distributed Backends](distributed.md) - For Spark
- [Databases](databases.md) - PostgreSQL, MySQL, ClickHouse
