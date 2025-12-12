# Apache Spark Backend

Apache Spark is a distributed computing framework for big data processing. Use Spark for datasets that exceed single-machine capacity.

## Installation

```bash
pip install etlx[spark]
# or
uv add etlx[spark]
```

!!! warning "Java Required"
    Spark requires Java 8, 11, or 17. Verify with `java -version`.

## When to Use Spark

**Ideal for:**

- Datasets that don't fit on a single machine
- Distributed cluster environments (YARN, Kubernetes, EMR)
- Integration with Hadoop ecosystem
- Production data lake pipelines

**Consider alternatives when:**

- Data fits in memory (use DuckDB or Polars)
- Low latency is critical (Spark has startup overhead)
- Simple transformations (Spark is overkill)

## Configuration

### Basic Usage

```yaml
name: spark_pipeline
engine: spark

source:
  type: file
  path: s3://bucket/data/*.parquet
  format: parquet

transforms:
  - op: filter
    predicate: date >= '2025-01-01'
  - op: aggregate
    group_by: [region, category]
    aggregations:
      revenue: sum(amount)

sink:
  type: file
  path: s3://bucket/output/
  format: parquet
```

### Spark Configuration

Configure Spark session via environment variables:

```bash
export SPARK_MASTER=spark://master:7077
export SPARK_EXECUTOR_MEMORY=4g
export SPARK_EXECUTOR_CORES=2
```

Or in `.env`:

```
SPARK_MASTER=local[*]
SPARK_EXECUTOR_MEMORY=8g
SPARK_DRIVER_MEMORY=4g
```

## Deployment Modes

### Local Mode

For development and testing:

```bash
export SPARK_MASTER=local[*]
etlx run pipeline.yml --engine spark
```

### Standalone Cluster

```bash
export SPARK_MASTER=spark://master:7077
etlx run pipeline.yml --engine spark
```

### YARN

```bash
export SPARK_MASTER=yarn
export HADOOP_CONF_DIR=/etc/hadoop/conf
etlx run pipeline.yml --engine spark
```

### Kubernetes

```bash
export SPARK_MASTER=k8s://https://kubernetes:443
export SPARK_KUBERNETES_CONTAINER_IMAGE=spark:3.5.0
etlx run pipeline.yml --engine spark
```

## Supported Features

### Transforms

| Transform | Support | Notes |
|-----------|---------|-------|
| select | Full | |
| rename | Full | |
| filter | Full | |
| derive_column | Full | |
| cast | Full | |
| fill_null | Full | |
| dedup | Full | Uses `dropDuplicates` |
| sort | Full | Distributed sort |
| join | Full | Broadcast/shuffle join |
| aggregate | Full | |
| union | Full | |
| limit | Full | |

### Data Sources

Spark excels at reading from distributed storage:

```yaml
# S3
source:
  type: file
  path: s3a://bucket/data/*.parquet
  format: parquet

# HDFS
source:
  type: file
  path: hdfs://namenode/data/*.parquet
  format: parquet

# Delta Lake
source:
  type: file
  path: s3://bucket/delta-table/
  format: delta
```

## Performance Optimization

### 1. Partition Data

For large datasets, ensure data is partitioned:

```yaml
sink:
  type: file
  path: s3://bucket/output/
  format: parquet
  options:
    partition_by: [date, region]
```

### 2. Use Appropriate File Formats

- **Parquet**: Best for analytics (columnar, compressed)
- **Delta**: ACID transactions, time travel
- **ORC**: Hive compatibility

### 3. Broadcast Small Tables

For joins with small dimension tables:

```yaml
transforms:
  - op: join
    right:
      type: file
      path: s3://bucket/dim_products.parquet  # Small table
      format: parquet
    on: [product_id]
    how: left
```

### 4. Filter Early

Push predicates as early as possible:

```yaml
transforms:
  # Filter first - reduces shuffle
  - op: filter
    predicate: date >= '2025-01-01'

  # Then aggregate
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

## Cloud Integration

### AWS EMR

```bash
# Submit to EMR
export SPARK_MASTER=yarn
export AWS_REGION=us-east-1

etlx run pipeline.yml --engine spark
```

### Databricks

Use Databricks-specific configuration:

```bash
export SPARK_MASTER=databricks
export DATABRICKS_HOST=https://xxx.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...
```

### Google Dataproc

```bash
export SPARK_MASTER=yarn
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

## Example: Large-Scale ETL

```yaml
name: daily_sales_etl
description: Process daily sales across all regions
engine: spark

source:
  type: file
  path: s3://data-lake/raw/sales/date=${DATE}/*.parquet
  format: parquet

transforms:
  # Filter valid records
  - op: filter
    predicate: amount > 0 AND status = 'completed'

  # Enrich with product data
  - op: join
    right:
      type: file
      path: s3://data-lake/dim/products/
      format: parquet
    on: [product_id]
    how: left

  # Aggregate by region and category
  - op: aggregate
    group_by: [region, category, date]
    aggregations:
      total_revenue: sum(amount)
      order_count: count(*)
      avg_order: avg(amount)

sink:
  type: file
  path: s3://data-lake/processed/sales_summary/
  format: parquet
  options:
    partition_by: [date, region]
    mode: overwrite
```

## Limitations

1. **Startup Overhead**: 5-30 seconds for session initialization
2. **Small Data**: Inefficient for datasets under 1GB
3. **Complexity**: Requires cluster management
4. **Cost**: Cloud clusters can be expensive

## Troubleshooting

### Java Not Found

```
JAVA_HOME is not set
```

**Solution**: Install Java and set JAVA_HOME:
```bash
# macOS
brew install openjdk@17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17

# Ubuntu
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Out of Memory

```
java.lang.OutOfMemoryError: Java heap space
```

**Solution**: Increase executor memory:
```bash
export SPARK_EXECUTOR_MEMORY=8g
export SPARK_DRIVER_MEMORY=4g
```

### S3 Access Denied

Ensure AWS credentials are configured:
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
# Or use IAM role
```

## Related

- [Backend Selection](index.md) - Choosing the right backend
- [Cloud Storage](../io/cloud-storage.md) - S3, GCS configuration
- [Production Best Practices](../../best-practices/production.md)
