# Airflow DAG Example

This example demonstrates a complete Airflow DAG that orchestrates multiple ETLX pipelines with proper error handling, alerting, and monitoring.

## Overview

**Scenario**: Daily data pipeline that:

1. Extracts data from multiple sources
2. Transforms and validates data
3. Loads to data warehouse
4. Sends notifications on completion/failure

## DAG Structure

```
extract_orders ─┬─► transform_data ─► load_warehouse ─► notify_success
extract_products─┤                                    │
extract_customers┘                                    └─► notify_failure (on error)
```

## Complete DAG Code

Create `dags/daily_etl_dag.py`:

```python
"""
Daily ETL Pipeline DAG

This DAG orchestrates the daily ETL process using ETLX pipelines.
Runs daily at 6 AM UTC.
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule
from etlx.integrations.airflow import etlx_task


# Default arguments for all tasks
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email": ["data-alerts@company.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=1),
}


@dag(
    dag_id="daily_etl_pipeline",
    description="Daily ETL pipeline using ETLX",
    schedule="0 6 * * *",  # 6 AM UTC daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["quicketl", "production", "daily"],
    doc_md=__doc__,
)
def daily_etl_pipeline():
    """
    Daily ETL pipeline that extracts, transforms, and loads data.

    ## Pipeline Steps
    1. Extract: Pull data from source systems
    2. Transform: Clean, validate, and aggregate
    3. Load: Write to data warehouse
    4. Notify: Send completion status

    ## Variables Required
    - `etlx_database_url`: Connection string for warehouse
    - `etlx_s3_bucket`: S3 bucket for raw data

    ## Connections Required
    - `snowflake_default`: Snowflake warehouse connection
    """

    # =========================================================================
    # EXTRACT PHASE
    # =========================================================================

    @etlx_task(config="pipelines/extract/orders.yml")
    def extract_orders(**context):
        """Extract orders from source system."""
        return {
            "DATE": context["ds"],
            "EXECUTION_DATE": context["execution_date"].isoformat(),
        }

    @etlx_task(config="pipelines/extract/products.yml")
    def extract_products(**context):
        """Extract product catalog."""
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/extract/customers.yml")
    def extract_customers(**context):
        """Extract customer data."""
        return {"DATE": context["ds"]}

    # =========================================================================
    # TRANSFORM PHASE
    # =========================================================================

    @etlx_task(config="pipelines/transform/daily_metrics.yml")
    def transform_data(**context):
        """Transform and aggregate extracted data."""
        return {
            "DATE": context["ds"],
            "PREV_DATE": context["prev_ds"],
        }

    # =========================================================================
    # LOAD PHASE
    # =========================================================================

    @etlx_task(
        config="pipelines/load/warehouse.yml",
        fail_on_checks=True,
    )
    def load_warehouse(**context):
        """Load transformed data to warehouse."""
        from airflow.models import Variable

        return {
            "DATE": context["ds"],
            "WAREHOUSE": Variable.get("etlx_warehouse", default_var="ETL_WH"),
        }

    # =========================================================================
    # NOTIFICATION PHASE
    # =========================================================================

    @task
    def prepare_success_report(**context):
        """Prepare success notification with metrics."""
        ti = context["task_instance"]

        # Get results from upstream tasks
        extract_orders_result = ti.xcom_pull(task_ids="extract_orders")
        extract_products_result = ti.xcom_pull(task_ids="extract_products")
        extract_customers_result = ti.xcom_pull(task_ids="extract_customers")
        transform_result = ti.xcom_pull(task_ids="transform_data")
        load_result = ti.xcom_pull(task_ids="load_warehouse")

        # Calculate totals
        total_rows = sum([
            extract_orders_result.get("rows_written", 0),
            extract_products_result.get("rows_written", 0),
            extract_customers_result.get("rows_written", 0),
        ])

        total_duration = sum([
            extract_orders_result.get("duration_ms", 0),
            extract_products_result.get("duration_ms", 0),
            extract_customers_result.get("duration_ms", 0),
            transform_result.get("duration_ms", 0),
            load_result.get("duration_ms", 0),
        ])

        return {
            "date": context["ds"],
            "total_rows_extracted": total_rows,
            "rows_loaded": load_result.get("rows_written", 0),
            "total_duration_ms": total_duration,
            "checks_passed": load_result.get("checks_passed", 0),
        }

    notify_success = EmailOperator(
        task_id="notify_success",
        to=["data-team@company.com"],
        subject="✓ Daily ETL Success: {{ ds }}",
        html_content="""
        <h2>Daily ETL Pipeline Completed Successfully</h2>

        <p><strong>Date:</strong> {{ ds }}</p>
        <p><strong>Run ID:</strong> {{ run_id }}</p>

        <h3>Metrics</h3>
        <ul>
            <li>Rows Extracted: {{ ti.xcom_pull(task_ids='prepare_success_report')['total_rows_extracted'] }}</li>
            <li>Rows Loaded: {{ ti.xcom_pull(task_ids='prepare_success_report')['rows_loaded'] }}</li>
            <li>Duration: {{ ti.xcom_pull(task_ids='prepare_success_report')['total_duration_ms'] }}ms</li>
            <li>Quality Checks Passed: {{ ti.xcom_pull(task_ids='prepare_success_report')['checks_passed'] }}</li>
        </ul>

        <p><a href="{{ conf.get('webserver', 'base_url') }}/dags/daily_etl_pipeline/grid">View in Airflow</a></p>
        """,
    )

    notify_failure = EmailOperator(
        task_id="notify_failure",
        to=["data-alerts@company.com", "oncall@company.com"],
        subject="✗ Daily ETL FAILED: {{ ds }}",
        html_content="""
        <h2>Daily ETL Pipeline Failed</h2>

        <p><strong>Date:</strong> {{ ds }}</p>
        <p><strong>Run ID:</strong> {{ run_id }}</p>

        <p>Please investigate immediately.</p>

        <p><a href="{{ conf.get('webserver', 'base_url') }}/dags/daily_etl_pipeline/grid">View in Airflow</a></p>
        """,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    # =========================================================================
    # DAG DEPENDENCIES
    # =========================================================================

    # Extract phase (parallel)
    orders = extract_orders()
    products = extract_products()
    customers = extract_customers()

    # Transform phase (after all extracts)
    transformed = transform_data()
    [orders, products, customers] >> transformed

    # Load phase
    loaded = load_warehouse()
    transformed >> loaded

    # Notification phase
    report = prepare_success_report()
    loaded >> report >> notify_success

    # Failure notification (triggers if any task fails)
    [orders, products, customers, transformed, loaded] >> notify_failure


# Instantiate DAG
daily_etl_pipeline()
```

## Pipeline Configuration Files

### Extract Orders (`pipelines/extract/orders.yml`)

```yaml
name: extract_orders
description: Extract orders from source database
engine: duckdb

source:
  type: database
  connection: postgres
  query: |
    SELECT *
    FROM orders
    WHERE order_date = '${DATE}'

sink:
  type: file
  path: staging/orders/date=${DATE}/orders.parquet
  format: parquet
  mode: replace
```

### Extract Products (`pipelines/extract/products.yml`)

```yaml
name: extract_products
description: Extract product catalog
engine: duckdb

source:
  type: database
  connection: postgres
  table: products

sink:
  type: file
  path: staging/products/products.parquet
  format: parquet
  mode: replace
```

### Transform (`pipelines/transform/daily_metrics.yml`)

```yaml
name: transform_daily_metrics
description: Transform and aggregate daily data
engine: duckdb

source:
  type: file
  path: staging/orders/date=${DATE}/*.parquet
  format: parquet

transforms:
  - op: join
    right:
      type: file
      path: staging/products/products.parquet
      format: parquet
    on: [product_id]
    how: left

  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  - op: aggregate
    group_by: [category, order_date]
    aggregations:
      total_revenue: sum(line_total)
      order_count: count(distinct order_id)

checks:
  - check: not_null
    columns: [category, total_revenue]
  - check: row_count
    min: 1

sink:
  type: file
  path: staging/metrics/date=${DATE}/metrics.parquet
  format: parquet
```

### Load Warehouse (`pipelines/load/warehouse.yml`)

```yaml
name: load_warehouse
description: Load metrics to data warehouse
engine: snowflake

source:
  type: file
  path: staging/metrics/date=${DATE}/*.parquet
  format: parquet

transforms:
  - op: derive_column
    name: loaded_at
    expr: current_timestamp()

checks:
  - check: not_null
    columns: [category, total_revenue, loaded_at]
  - check: expression
    expr: total_revenue >= 0

sink:
  type: database
  connection: snowflake
  table: analytics.daily_metrics
  mode: merge
  merge_keys: [category, order_date]
```

## Advanced Patterns

### Dynamic Task Generation

```python
@dag(...)
def dynamic_pipeline():
    @task
    def get_regions():
        # Could come from database or API
        return ["us-east", "us-west", "eu-west", "ap-south"]

    @etlx_task(config="pipelines/regional.yml")
    def process_region(region, **context):
        return {
            "DATE": context["ds"],
            "REGION": region,
        }

    regions = get_regions()
    process_region.expand(region=regions)
```

### Conditional Execution

```python
from airflow.operators.python import BranchPythonOperator

@dag(...)
def conditional_pipeline():
    def choose_pipeline(**context):
        # Monday = full refresh, other days = incremental
        if context["execution_date"].weekday() == 0:
            return "full_refresh"
        return "incremental"

    branch = BranchPythonOperator(
        task_id="choose_pipeline",
        python_callable=choose_pipeline,
    )

    @etlx_task(config="pipelines/full_refresh.yml")
    def full_refresh(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/incremental.yml")
    def incremental(**context):
        return {"DATE": context["ds"]}

    branch >> [full_refresh(), incremental()]
```

### SLA Monitoring

```python
@dag(
    sla_miss_callback=slack_sla_alert,
    default_args={
        "sla": timedelta(hours=2),
    },
)
def sla_monitored_pipeline():
    @etlx_task(
        config="pipelines/critical.yml",
        sla=timedelta(hours=1),  # Stricter SLA for this task
    )
    def critical_task(**context):
        return {"DATE": context["ds"]}
```

## Deployment

### Project Structure

```
airflow/
├── dags/
│   ├── daily_etl_dag.py
│   └── weekly_etl_dag.py
├── pipelines/
│   ├── extract/
│   │   ├── orders.yml
│   │   ├── products.yml
│   │   └── customers.yml
│   ├── transform/
│   │   └── daily_metrics.yml
│   └── load/
│       └── warehouse.yml
└── requirements.txt
```

### Requirements

```
# requirements.txt
apache-airflow>=2.8.0
etlx[airflow,duckdb,snowflake]
```

### Airflow Variables

Set in Airflow UI or via CLI:

```bash
airflow variables set etlx_warehouse "ETL_WH"
airflow variables set etlx_s3_bucket "data-lake-prod"
```

### Airflow Connections

```bash
# PostgreSQL source
airflow connections add postgres_source \
    --conn-type postgres \
    --conn-host localhost \
    --conn-login user \
    --conn-password pass \
    --conn-schema mydb

# Snowflake destination
airflow connections add snowflake_default \
    --conn-type snowflake \
    --conn-host xy12345.us-east-1 \
    --conn-login etl_user \
    --conn-password pass \
    --conn-schema analytics
```

## Next Steps

- [Airflow Integration Guide](../integrations/airflow.md) - Complete reference
- [Cloud ETL Example](cloud-etl.md) - Cloud-native pipelines
- [Production Best Practices](../best-practices/production.md)
