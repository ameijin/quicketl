# Variable Substitution

QuickETL supports variable substitution in YAML configurations, allowing dynamic values at runtime.

## Basic Syntax

Reference variables using `${VAR_NAME}`:

```yaml
source:
  type: file
  path: data/${DATE}/sales.parquet
```

## Default Values

Provide defaults with `${VAR_NAME:-default}`:

```yaml
engine: ${ENGINE:-duckdb}

source:
  type: file
  path: ${INPUT_PATH:-data/sales.parquet}
```

## Setting Variables

### CLI Flag

Pass variables with `--var`:

```bash
quicketl run pipeline.yml --var DATE=2025-01-15
quicketl run pipeline.yml --var DATE=2025-01-15 --var REGION=north
```

### Environment Variables

Variables are resolved from the environment:

```bash
export DATE=2025-01-15
export DATABASE_URL=postgresql://localhost/db

quicketl run pipeline.yml
```

### Python API

Pass variables to `Pipeline.from_yaml()` or `run()`:

```python
# At load time
pipeline = Pipeline.from_yaml(
    "pipeline.yml",
    variables={"DATE": "2025-01-15"}
)

# At run time
result = pipeline.run(variables={"DATE": "2025-01-15"})
```

## Resolution Order

Variables are resolved in this order:

1. **Explicit variables** - `--var` flag or `variables` parameter
2. **Environment variables** - `os.environ`
3. **Default value** - From `${VAR:-default}` syntax
4. **Error** - If no value found and no default

```yaml
# Uses --var DATE if provided
# Falls back to $DATE environment variable
# Falls back to "2025-01-01" if neither exists
path: data/${DATE:-2025-01-01}/sales.parquet
```

## Common Patterns

### Date-Based Paths

```yaml
source:
  type: file
  path: s3://bucket/data/${YEAR}/${MONTH}/${DAY}/

sink:
  type: file
  path: s3://bucket/output/${RUN_DATE}/
```

```bash
quicketl run pipeline.yml --var YEAR=2025 --var MONTH=01 --var DAY=15
# OR
quicketl run pipeline.yml --var RUN_DATE=2025-01-15
```

### Environment-Specific Configuration

```yaml
source:
  type: database
  connection: ${DATABASE_URL}

sink:
  type: file
  path: ${OUTPUT_BUCKET}/results/
```

```bash
# Development
export DATABASE_URL=postgresql://localhost/dev
export OUTPUT_BUCKET=./data/output

# Production
export DATABASE_URL=postgresql://prod-server/db
export OUTPUT_BUCKET=s3://prod-bucket
```

### Dynamic Filtering

```yaml
transforms:
  - op: filter
    predicate: region = '${REGION}'

  - op: filter
    predicate: date >= '${START_DATE}' AND date <= '${END_DATE}'
```

```bash
quicketl run pipeline.yml \
  --var REGION=north \
  --var START_DATE=2025-01-01 \
  --var END_DATE=2025-01-31
```

### Optional Features

```yaml
# Only aggregate if GROUP_BY is set
transforms:
  - op: aggregate
    group_by: [${GROUP_BY:-category}]
    aggs:
      total: sum(amount)
```

## Airflow Integration

When using the `@quicketl_task` decorator, return variables from your task:

```python
from quicketl.integrations.airflow import quicketl_task

@quicketl_task(config_path="pipelines/daily.yml")
def run_daily_pipeline(**context):
    return {
        "DATE": context["ds"],                    # Airflow execution date
        "BUCKET": context["params"].get("bucket", "default-bucket"),
    }
```

Access Airflow variables:

```yaml
source:
  type: file
  path: s3://${BUCKET}/data/${DATE}/
```

## The .env File

Store variables in `.env` for local development:

```bash title=".env"
DATABASE_URL=postgresql://localhost/dev
OUTPUT_PATH=./data/output
DEFAULT_ENGINE=duckdb
```

!!! warning "Security"
    Never commit `.env` files with secrets. Add `.env` to `.gitignore`.

## Escaping

To use a literal `${`, escape with `$${`:

```yaml
# Outputs: The variable syntax is ${VAR}
description: The variable syntax is $${VAR}
```

## Validation

Unresolved required variables cause validation errors:

```bash
$ quicketl run pipeline.yml
Error: Variable 'DATABASE_URL' is not set and has no default value
```

Use `quicketl validate` to check variables:

```bash
quicketl validate pipeline.yml --var DATE=2025-01-15
```

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
path: ${INPUT_SALES_PATH}
path: ${S3_OUTPUT_BUCKET}

# Bad
path: ${PATH}
path: ${P1}
```

### 2. Provide Sensible Defaults

```yaml
# Good - works out of the box for development
engine: ${ENGINE:-duckdb}
path: ${INPUT:-data/sample.parquet}

# Less good - requires variables to be set
path: ${INPUT}
```

### 3. Document Required Variables

```yaml
# Required variables:
#   DATABASE_URL: PostgreSQL connection string
#   DATE: Run date in YYYY-MM-DD format
#
# Optional variables:
#   ENGINE: Compute backend (default: duckdb)
#   OUTPUT_PATH: Output location (default: ./output/)

name: documented_pipeline
```

### 4. Use .env.example

Create a template for required variables:

```bash title=".env.example"
# Copy this file to .env and fill in values

# Required
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional
ENGINE=duckdb
OUTPUT_PATH=./output/
```

## Related

- [Pipeline YAML](pipeline-yaml.md) - Full YAML reference
- [Airflow Integration](../../integrations/airflow.md) - Using with Airflow
- [Project Structure](../../getting-started/project-structure.md) - Organizing variables
