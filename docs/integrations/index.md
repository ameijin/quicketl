# Integrations

ETLX integrates with popular data orchestration and workflow tools. This section covers how to use ETLX within larger data ecosystems.

## Orchestration Platforms

### Apache Airflow

Run ETLX pipelines as Airflow tasks with proper dependency management, retries, and monitoring.

[Airflow Integration →](airflow.md)

**Features:**

- `@etlx_task` decorator for simple integration
- Pass Airflow variables to pipelines
- Automatic retry handling
- XCom integration for result passing

```python
from airflow.decorators import dag
from etlx.integrations.airflow import etlx_task

@dag(schedule="@daily")
def etl_pipeline():
    @etlx_task(config="pipelines/sales.yml")
    def process_sales(**context):
        return {"date": context["ds"]}

    process_sales()
```

### Prefect (Coming Soon)

Integration with Prefect for modern workflow orchestration.

### Dagster (Coming Soon)

Integration with Dagster for software-defined assets.

## Data Platforms

### dbt

Use ETLX alongside dbt for transformation workflows.

**Pattern: ETLX for Ingestion, dbt for Transformation**

```
Raw Sources → ETLX → Staging Tables → dbt → Marts
```

```yaml
# ETLX: Load raw data
name: load_raw_orders
source:
  type: file
  path: s3://bucket/orders/*.parquet
  format: parquet
sink:
  type: database
  connection: postgres
  table: staging.raw_orders
  mode: replace
```

```sql
-- dbt: Transform
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount
FROM {{ source('staging', 'raw_orders') }}
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
```

### Great Expectations

Use Great Expectations for additional data validation.

```python
from etlx import Pipeline
import great_expectations as gx

# Run ETLX pipeline
pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

# Validate with Great Expectations
df = result.to_dataframe()
context = gx.get_context()
validator = context.get_validator(df)
validation_result = validator.validate()
```

## Cloud Services

### AWS

**S3 Integration:**

```yaml
source:
  type: file
  path: s3://bucket/data/*.parquet
  format: parquet
```

**Environment Setup:**

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

### Google Cloud

**GCS Integration:**

```yaml
source:
  type: file
  path: gs://bucket/data/*.parquet
  format: parquet
```

**BigQuery Backend:**

```yaml
engine: bigquery
source:
  type: database
  connection: bigquery
  table: project.dataset.table
```

### Azure

**Azure Blob Storage:**

```yaml
source:
  type: file
  path: az://container/data/*.parquet
  format: parquet
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/etl.yml
name: Run ETL Pipeline

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  etl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install ETLX
        run: pip install quicketl[duckdb]

      - name: Validate Pipeline
        run: quicketl validate pipelines/daily.yml

      - name: Run Pipeline
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: quicketl run pipelines/daily.yml --json
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - run

validate:
  stage: validate
  image: python:3.12
  script:
    - pip install quicketl[duckdb]
    - quicketl validate pipelines/*.yml

run:
  stage: run
  image: python:3.12
  script:
    - pip install quicketl[duckdb]
    - quicketl run pipelines/daily.yml
  only:
    - schedules
```

## Python Frameworks

### FastAPI

```python
from fastapi import FastAPI, BackgroundTasks
from etlx import Pipeline

app = FastAPI()

@app.post("/pipelines/{name}/run")
async def run_pipeline(
    name: str,
    background_tasks: BackgroundTasks,
    variables: dict = None
):
    def execute():
        pipeline = Pipeline.from_yaml(f"pipelines/{name}.yml")
        return pipeline.run(variables=variables)

    background_tasks.add_task(execute)
    return {"status": "started", "pipeline": name}
```

### Flask

```python
from flask import Flask, request, jsonify
from etlx import Pipeline

app = Flask(__name__)

@app.route("/run/<pipeline_name>", methods=["POST"])
def run_pipeline(pipeline_name):
    variables = request.json or {}

    pipeline = Pipeline.from_yaml(f"pipelines/{pipeline_name}.yml")
    result = pipeline.run(variables=variables)

    return jsonify(result.to_dict())
```

### Streamlit

```python
import streamlit as st
from etlx import Pipeline

st.title("ETLX Dashboard")

config_file = st.selectbox("Pipeline", ["sales.yml", "inventory.yml"])
variables = st.text_input("Variables (JSON)", "{}")

if st.button("Run Pipeline"):
    import json
    vars_dict = json.loads(variables)

    pipeline = Pipeline.from_yaml(f"pipelines/{config_file}")
    result = pipeline.run(variables=vars_dict)

    st.success(f"Completed in {result.duration_ms:.1f}ms")
    st.metric("Rows Processed", result.rows_processed)
    st.metric("Rows Written", result.rows_written)
```

## Message Queues

### Celery

```python
from celery import Celery
from etlx import Pipeline

app = Celery('etlx_tasks', broker='redis://localhost:6379')

@app.task
def run_etlx_pipeline(config_path: str, variables: dict = None):
    pipeline = Pipeline.from_yaml(config_path)
    result = pipeline.run(variables=variables)
    return result.to_dict()

# Trigger
run_etlx_pipeline.delay("pipelines/sales.yml", {"date": "2025-01-15"})
```

## Related

- [Airflow Integration](airflow.md) - Detailed Airflow guide
- [Python API](../api/index.md) - API reference
- [Production Best Practices](../best-practices/production.md)
