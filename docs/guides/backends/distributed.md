# Distributed Backend: Apache Spark

Apache Spark is a distributed computing framework for big data processing. Use Spark for datasets that exceed single-machine capacity.

## Installation

```bash
pip install quicketl[spark]
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

- Data fits in memory (use DuckDB or Polars - much faster)
- Low latency is critical (Spark has 5-30s startup overhead)
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
    aggs:
      revenue: sum(amount)

sink:
  type: file
  path: s3://bucket/output/
  format: parquet
```

### Spark Configuration

Configure via environment variables:

```bash
export SPARK_MASTER=spark://master:7077
export SPARK_EXECUTOR_MEMORY=4g
export SPARK_EXECUTOR_CORES=2
export SPARK_DRIVER_MEMORY=4g
```

## Deployment Modes

### Local Mode (Development)

```bash
export SPARK_MASTER=local[*]
quicketl run pipeline.yml --engine spark
```

### Standalone Cluster

```bash
export SPARK_MASTER=spark://master:7077
quicketl run pipeline.yml --engine spark
```

### YARN (Hadoop)

```bash
export SPARK_MASTER=yarn
export HADOOP_CONF_DIR=/etc/hadoop/conf
quicketl run pipeline.yml --engine spark
```

### Kubernetes

```bash
export SPARK_MASTER=k8s://https://kubernetes:443
export SPARK_KUBERNETES_CONTAINER_IMAGE=spark:3.5.0
quicketl run pipeline.yml --engine spark
```

## Cloud Integration

### AWS EMR

```bash
export SPARK_MASTER=yarn
export AWS_REGION=us-east-1
quicketl run pipeline.yml --engine spark
```

### Databricks

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

## Data Sources

Spark excels at reading from distributed storage:

```yaml
# S3
source:
  type: file
  path: s3a://bucket/data/*.parquet

# HDFS
source:
  type: file
  path: hdfs://namenode/data/*.parquet

# Delta Lake
source:
  type: file
  path: s3://bucket/delta-table/
  format: delta
```

## Performance Optimization

### 1. Partition Data

```yaml
sink:
  type: file
  path: s3://bucket/output/
  format: parquet
  options:
    partition_by: [date, region]
```

### 2. Filter Early

Push predicates as early as possible to reduce shuffle:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'  # Filter first
  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)
```

### 3. Use Appropriate File Formats

- **Parquet**: Best for analytics (columnar, compressed)
- **Delta**: ACID transactions, time travel
- **ORC**: Hive compatibility

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
  - op: filter
    predicate: amount > 0 AND status = 'completed'

  - op: join
    right:
      type: file
      path: s3://data-lake/dim/products/
      format: parquet
    on: [product_id]
    how: left

  - op: aggregate
    group_by: [region, category, date]
    aggs:
      total_revenue: sum(amount)
      order_count: count(*)

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

```bash
# macOS
brew install openjdk@17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17

# Ubuntu
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Out of Memory

```bash
export SPARK_EXECUTOR_MEMORY=8g
export SPARK_DRIVER_MEMORY=4g
```

### S3 Access Denied

Ensure AWS credentials are configured:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

## Related

- [Local Backends](local.md) - For smaller datasets
- [Cloud Warehouses](cloud-warehouses.md) - Serverless alternatives
