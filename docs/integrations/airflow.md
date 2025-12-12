# Airflow Integration

ETLX provides first-class integration with Apache Airflow for orchestrating data pipelines. Run ETLX pipelines as Airflow tasks with proper dependency management, retries, and monitoring.

## Installation

```bash
pip install etlx[airflow]
# or
uv add etlx[airflow]
```

## Quick Start

### Using the Decorator

The simplest way to run ETLX in Airflow:

```python
from airflow.decorators import dag
from datetime import datetime
from etlx.integrations.airflow import etlx_task

@dag(
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False
)
def sales_pipeline():

    @etlx_task(config="pipelines/daily_sales.yml")
    def process_sales(**context):
        # Return variables to pass to pipeline
        return {
            "DATE": context["ds"],
            "REGION": "all"
        }

    process_sales()

sales_pipeline()
```

### Using the Operator

For more control, use the operator directly:

```python
from airflow import DAG
from datetime import datetime
from etlx.integrations.airflow import ETLXOperator

with DAG(
    "sales_etl",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False
) as dag:

    process_sales = ETLXOperator(
        task_id="process_sales",
        config_path="pipelines/daily_sales.yml",
        variables={
            "DATE": "{{ ds }}",
            "REGION": "{{ var.value.region }}"
        },
        engine="duckdb",
        fail_on_checks=True
    )
```

## ETLXOperator Reference

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | `str` | Required | Path to YAML config |
| `variables` | `dict` | `None` | Variables to pass (supports Jinja) |
| `engine` | `str` | `None` | Override engine |
| `fail_on_checks` | `bool` | `True` | Fail task on check failure |
| `dry_run` | `bool` | `False` | Execute without writing |

### Jinja Templating

Variables support Airflow's Jinja templating:

```python
ETLXOperator(
    task_id="process",
    config_path="pipelines/sales.yml",
    variables={
        "DATE": "{{ ds }}",
        "EXECUTION_DATE": "{{ execution_date }}",
        "PREV_DATE": "{{ prev_ds }}",
        "NEXT_DATE": "{{ next_ds }}",
        "RUN_ID": "{{ run_id }}",
        "DAG_ID": "{{ dag.dag_id }}",
        "CUSTOM_VAR": "{{ var.value.my_variable }}",
        "CONNECTION": "{{ conn.my_connection.host }}"
    }
)
```

## @etlx_task Decorator

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `str` | Required | Path to YAML config |
| `engine` | `str` | `None` | Override engine |
| `fail_on_checks` | `bool` | `True` | Fail on check failure |

### Return Values

The decorated function should return a dictionary of variables:

```python
@etlx_task(config="pipelines/sales.yml")
def process_sales(**context):
    return {
        "DATE": context["ds"],
        "BATCH_ID": context["run_id"]
    }
```

### XCom Integration

Results are automatically pushed to XCom:

```python
@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def pipeline():

    @etlx_task(config="pipelines/extract.yml")
    def extract(**context):
        return {"DATE": context["ds"]}

    @task
    def log_results(result):
        print(f"Rows processed: {result['rows_processed']}")
        print(f"Duration: {result['duration_ms']}ms")

    result = extract()
    log_results(result)
```

## DAG Patterns

### Sequential Pipeline

```python
from airflow.decorators import dag, task
from etlx.integrations.airflow import etlx_task

@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def sequential_pipeline():

    @etlx_task(config="pipelines/extract.yml")
    def extract(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/transform.yml")
    def transform(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/load.yml")
    def load(**context):
        return {"DATE": context["ds"]}

    extract() >> transform() >> load()
```

### Parallel Processing

```python
@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def parallel_pipeline():

    @etlx_task(config="pipelines/sales.yml")
    def process_sales(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/inventory.yml")
    def process_inventory(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/aggregate.yml")
    def aggregate(**context):
        return {"DATE": context["ds"]}

    # Parallel tasks feed into aggregate
    [process_sales(), process_inventory()] >> aggregate()
```

### Dynamic Task Mapping

```python
@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def dynamic_pipeline():

    @task
    def get_regions():
        return ["north", "south", "east", "west"]

    @etlx_task(config="pipelines/regional_sales.yml")
    def process_region(region, **context):
        return {
            "DATE": context["ds"],
            "REGION": region
        }

    regions = get_regions()
    process_region.expand(region=regions)
```

### Conditional Execution

```python
from airflow.operators.python import BranchPythonOperator

@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def conditional_pipeline():

    def choose_path(**context):
        day = context["execution_date"].weekday()
        if day == 0:  # Monday
            return "full_refresh"
        return "incremental"

    branch = BranchPythonOperator(
        task_id="choose_path",
        python_callable=choose_path
    )

    @etlx_task(config="pipelines/full_refresh.yml")
    def full_refresh(**context):
        return {"DATE": context["ds"]}

    @etlx_task(config="pipelines/incremental.yml")
    def incremental(**context):
        return {"DATE": context["ds"]}

    branch >> [full_refresh(), incremental()]
```

## Error Handling

### Retry Configuration

```python
from airflow.decorators import dag
from datetime import timedelta

@dag(
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(hours=1)
    }
)
def pipeline_with_retries():
    @etlx_task(config="pipelines/sales.yml")
    def process(**context):
        return {"DATE": context["ds"]}

    process()
```

### Custom Error Handling

```python
from airflow.decorators import dag, task
from etlx import Pipeline
from etlx.exceptions import QualityCheckError

@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def pipeline_with_error_handling():

    @task
    def run_pipeline(**context):
        pipeline = Pipeline.from_yaml("pipelines/sales.yml")

        try:
            result = pipeline.run(
                variables={"DATE": context["ds"]},
                fail_on_checks=True
            )
            return result.to_dict()

        except QualityCheckError as e:
            # Log warning but don't fail
            print(f"Quality checks failed: {e}")
            return {"status": "WARNING", "checks_failed": len(e.failed_checks)}

    run_pipeline()
```

### Alerting on Failure

```python
from airflow.decorators import dag
from airflow.operators.email import EmailOperator

@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def pipeline_with_alerts():

    @etlx_task(config="pipelines/sales.yml")
    def process(**context):
        return {"DATE": context["ds"]}

    alert = EmailOperator(
        task_id="send_alert",
        to="team@example.com",
        subject="Pipeline Failed: {{ dag.dag_id }}",
        html_content="Task failed at {{ ts }}",
        trigger_rule="one_failed"
    )

    process() >> alert
```

## Best Practices

### 1. Use Variables for Configuration

```python
# airflow variables
# etlx_database_url = postgresql://...
# etlx_s3_bucket = my-bucket

@etlx_task(config="pipelines/sales.yml")
def process(**context):
    from airflow.models import Variable
    return {
        "DATABASE_URL": Variable.get("etlx_database_url"),
        "S3_BUCKET": Variable.get("etlx_s3_bucket"),
        "DATE": context["ds"]
    }
```

### 2. Use Connections for Secrets

```python
@task
def run_with_connection(**context):
    from airflow.hooks.base import BaseHook
    from etlx import Pipeline

    conn = BaseHook.get_connection("my_database")

    import os
    os.environ["POSTGRES_HOST"] = conn.host
    os.environ["POSTGRES_USER"] = conn.login
    os.environ["POSTGRES_PASSWORD"] = conn.password
    os.environ["POSTGRES_DATABASE"] = conn.schema

    pipeline = Pipeline.from_yaml("pipelines/sales.yml")
    return pipeline.run(variables={"DATE": context["ds"]}).to_dict()
```

### 3. Organize Pipeline Files

```
dags/
├── sales_dag.py
├── inventory_dag.py
└── pipelines/
    ├── sales/
    │   ├── extract.yml
    │   ├── transform.yml
    │   └── load.yml
    └── inventory/
        ├── daily.yml
        └── weekly.yml
```

### 4. Use SLAs

```python
@dag(
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    sla_miss_callback=sla_alert
)
def pipeline_with_sla():

    @etlx_task(
        config="pipelines/sales.yml",
        sla=timedelta(hours=2)
    )
    def process(**context):
        return {"DATE": context["ds"]}
```

## Monitoring

### Task Metrics

Access metrics from XCom:

```python
@dag(schedule="@daily", start_date=datetime(2025, 1, 1))
def monitored_pipeline():

    @etlx_task(config="pipelines/sales.yml")
    def process(**context):
        return {"DATE": context["ds"]}

    @task
    def log_metrics(result):
        # Send to monitoring system
        print(f"Pipeline: {result['pipeline_name']}")
        print(f"Duration: {result['duration_ms']}ms")
        print(f"Rows: {result['rows_processed']} → {result['rows_written']}")
        print(f"Checks: {result['checks_passed']}/{result['checks_passed'] + result['checks_failed']}")

    result = process()
    log_metrics(result)
```

### Custom Callbacks

```python
def on_success(context):
    result = context["task_instance"].xcom_pull()
    # Send to monitoring
    print(f"Success: {result['rows_written']} rows")

def on_failure(context):
    # Send alert
    print(f"Failed: {context['exception']}")

@etlx_task(
    config="pipelines/sales.yml",
    on_success_callback=on_success,
    on_failure_callback=on_failure
)
def process(**context):
    return {"DATE": context["ds"]}
```

## Related

- [Integrations Overview](index.md) - Other integrations
- [Python API](../api/index.md) - ETLX API reference
- [Production Best Practices](../best-practices/production.md)
