# Project Structure

Learn how to organize QuickETL projects for maintainability and scalability.

## Recommended Layout

```
my_project/
├── pipelines/              # Pipeline configurations
│   ├── daily/             # Daily pipelines
│   │   ├── sales_etl.yml
│   │   └── inventory_sync.yml
│   ├── weekly/            # Weekly pipelines
│   │   └── reports.yml
│   └── adhoc/             # One-off pipelines
│       └── migration.yml
├── data/                   # Data directory
│   ├── input/             # Input data (gitignored)
│   ├── output/            # Output data (gitignored)
│   └── samples/           # Sample data for testing
├── scripts/               # Python scripts
│   ├── custom_transforms.py
│   └── utils.py
├── dags/                  # Airflow DAGs (if using Airflow)
│   └── quicketl_dag.py
├── tests/                 # Pipeline tests
│   ├── test_sales_etl.py
│   └── fixtures/
├── .env                   # Environment variables
├── .env.example           # Example env file
├── .gitignore
└── README.md
```

## Pipeline Organization

### By Schedule

Group pipelines by their run schedule:

```
pipelines/
├── hourly/
├── daily/
├── weekly/
└── monthly/
```

### By Domain

Group pipelines by business domain:

```
pipelines/
├── sales/
├── marketing/
├── finance/
└── operations/
```

### By Data Source

Group pipelines by their data source:

```
pipelines/
├── postgres/
├── salesforce/
├── s3/
└── api/
```

## Environment Variables

### The `.env` File

Store configuration in `.env`:

```bash title=".env"
# Database connections
POSTGRES_URL=postgresql://user:pass@localhost:5432/db
SNOWFLAKE_ACCOUNT=abc123.us-east-1

# Cloud storage
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Pipeline variables
DEFAULT_DATE=2025-01-01
OUTPUT_BUCKET=s3://my-data-lake/output
```

### Using in Pipelines

Reference variables in YAML:

```yaml
source:
  type: database
  connection: ${POSTGRES_URL}

sink:
  type: file
  path: ${OUTPUT_BUCKET}/sales/${DATE}/data.parquet
```

### The `.env.example` File

Document required variables (commit this file):

```bash title=".env.example"
# Database connections
POSTGRES_URL=postgresql://user:pass@host:5432/db

# Cloud storage (AWS)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Pipeline variables
DEFAULT_DATE=2025-01-01
```

## Git Ignore Patterns

Recommended `.gitignore`:

```gitignore title=".gitignore"
# Data files
data/input/
data/output/
*.parquet
*.csv
!data/samples/*.csv

# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

## Configuration Patterns

### Base + Override Pattern

Create a base configuration and override for environments:

```yaml title="pipelines/base/sales.yml"
name: sales_etl
engine: duckdb

source:
  type: file
  path: ${INPUT_PATH}
  format: parquet

transforms:
  - op: filter
    predicate: amount > 0

sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
```

```bash
# Development
quicketl run pipelines/base/sales.yml \
  --var INPUT_PATH=data/samples/sales.parquet \
  --var OUTPUT_PATH=data/output/sales.parquet

# Production
quicketl run pipelines/base/sales.yml \
  --var INPUT_PATH=s3://prod-bucket/sales/ \
  --var OUTPUT_PATH=s3://prod-bucket/output/sales/
```

### Shared Transforms

For complex transform sequences, use Python:

```python title="scripts/transforms.py"
from quicketl.config.transforms import (
    FilterTransform,
    DeriveColumnTransform,
    AggregateTransform,
)

# Reusable transform sequences
CLEAN_SALES = [
    FilterTransform(predicate="amount > 0"),
    FilterTransform(predicate="status != 'cancelled'"),
    DeriveColumnTransform(name="net_amount", expr="amount - discount"),
]

AGGREGATE_BY_REGION = AggregateTransform(
    group_by=["region"],
    aggs={
        "total_sales": "sum(net_amount)",
        "order_count": "count(*)",
    }
)
```

## Testing Pipelines

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── fixtures/
│   └── sample_sales.csv  # Test data
├── test_sales_etl.py
└── test_transforms.py
```

### Sample Test

```python title="tests/test_sales_etl.py"
import pytest
from pathlib import Path
from quicketl import Pipeline

FIXTURES = Path(__file__).parent / "fixtures"

def test_sales_pipeline_runs():
    """Test that the sales pipeline runs successfully."""
    pipeline = Pipeline.from_yaml(
        "pipelines/daily/sales_etl.yml",
        variables={
            "INPUT_PATH": str(FIXTURES / "sample_sales.csv"),
            "OUTPUT_PATH": "/tmp/test_output.parquet",
        }
    )

    result = pipeline.run()

    assert result.succeeded
    assert result.rows_processed > 0

def test_sales_pipeline_checks_pass():
    """Test that quality checks pass."""
    pipeline = Pipeline.from_yaml("pipelines/daily/sales_etl.yml")
    result = pipeline.run(dry_run=True)

    assert result.check_results["all_passed"]
```

## Airflow Integration

### DAG Structure

```python title="dags/quicketl_dag.py"
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from quicketl.integrations.airflow import quicketl_task

default_args = {
    "owner": "data-team",
    "retries": 2,
}

with DAG(
    "quicketl_sales_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    @quicketl_task(config_path="pipelines/daily/sales_etl.yml")
    def run_sales_etl(**context):
        return {"DATE": context["ds"]}

    sales_task = PythonOperator(
        task_id="sales_etl",
        python_callable=run_sales_etl,
    )
```

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
name: daily_sales_aggregation_by_region

# Bad
name: pipeline1
```

### 2. Document Your Pipelines

```yaml
name: sales_etl
description: |
  Daily sales ETL pipeline that:
  - Reads from PostgreSQL sales table
  - Filters cancelled orders
  - Aggregates by region and product category
  - Writes to S3 data lake

  Owner: data-team@company.com
  Schedule: Daily at 6 AM UTC
```

### 3. Version Your Schemas

When schemas change, version your pipelines:

```
pipelines/
├── sales_v1.yml  # Original schema
├── sales_v2.yml  # New schema with additional columns
└── sales.yml     # Symlink to current version
```

### 4. Use Consistent Naming

| Convention | Example |
|------------|---------|
| Pipeline files | `snake_case.yml` |
| Pipeline names | `snake_case` |
| Column names | `snake_case` |
| Variables | `UPPER_SNAKE_CASE` |

## Next Steps

- [Configuration Guide](../guides/configuration/index.md) - Deep dive into configuration
- [Airflow Integration](../integrations/airflow.md) - Orchestrate with Airflow
- [Best Practices](../best-practices/pipeline-design.md) - Production patterns
