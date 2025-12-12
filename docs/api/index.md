# Python API Reference

ETLX provides a Python API for programmatic pipeline creation and execution. Use the API when you need:

- Dynamic pipeline generation
- Integration with Python applications
- Programmatic control over execution
- Custom preprocessing or postprocessing

## Quick Start

```python
from etlx import Pipeline

# Load and run a pipeline
pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

print(f"Processed {result.rows_processed} rows")
```

## Core Classes

### Pipeline

The main entry point for working with ETLX pipelines.

```python
from etlx import Pipeline

# From YAML file
pipeline = Pipeline.from_yaml("pipeline.yml")

# From configuration dict
pipeline = Pipeline.from_config({
    "name": "my_pipeline",
    "engine": "duckdb",
    "source": {"type": "file", "path": "data.csv", "format": "csv"},
    "sink": {"type": "file", "path": "output.parquet", "format": "parquet"}
})
```

[Learn more about Pipeline →](pipeline.md)

### ETLXEngine

Direct access to the execution engine for advanced use cases.

```python
from etlx import ETLXEngine

engine = ETLXEngine(backend="duckdb")
result = engine.execute(config)
```

[Learn more about ETLXEngine →](engine.md)

### Configuration Models

Pydantic models for type-safe pipeline configuration.

```python
from etlx.config import PipelineConfig, FileSource, FileSink

config = PipelineConfig(
    name="typed_pipeline",
    engine="duckdb",
    source=FileSource(type="file", path="input.csv", format="csv"),
    sink=FileSink(type="file", path="output.parquet", format="parquet")
)
```

[Learn more about Configuration →](config.md)

### Quality Checks

Programmatic data quality validation.

```python
from etlx.quality import NotNullCheck, UniqueCheck

checks = [
    NotNullCheck(columns=["id", "name"]),
    UniqueCheck(columns=["id"])
]
```

[Learn more about Quality Checks →](quality.md)

## Common Patterns

### Run Pipeline with Variables

```python
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run(variables={
    "DATE": "2025-01-15",
    "REGION": "north"
})
```

### Validate Before Running

```python
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")

# Validate configuration
errors = pipeline.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    result = pipeline.run()
```

### Dry Run

```python
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run(dry_run=True)

print(f"Would process {result.rows_processed} rows")
```

### Access Results

```python
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

print(f"Pipeline: {result.pipeline_name}")
print(f"Status: {result.status}")
print(f"Duration: {result.duration_ms}ms")
print(f"Rows processed: {result.rows_processed}")
print(f"Rows written: {result.rows_written}")
print(f"Checks passed: {result.checks_passed}")
print(f"Checks failed: {result.checks_failed}")
```

### Get Result DataFrame

```python
from etlx import Pipeline

pipeline = Pipeline.from_yaml("pipeline.yml")
result = pipeline.run()

# Access the result as a DataFrame
df = result.to_dataframe()
print(df.head())
```

## Error Handling

```python
from etlx import Pipeline
from etlx.exceptions import (
    ETLXError,
    ConfigurationError,
    ExecutionError,
    QualityCheckError
)

try:
    pipeline = Pipeline.from_yaml("pipeline.yml")
    result = pipeline.run()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except QualityCheckError as e:
    print(f"Quality check failed: {e}")
    print(f"Failed checks: {e.failed_checks}")
except ExecutionError as e:
    print(f"Execution error: {e}")
except ETLXError as e:
    print(f"ETLX error: {e}")
```

## Integration Examples

### With Airflow

```python
from airflow.decorators import task

@task
def run_etlx_pipeline(config_path: str, **kwargs):
    from etlx import Pipeline

    pipeline = Pipeline.from_yaml(config_path)
    result = pipeline.run(variables=kwargs)

    return {
        "status": result.status,
        "rows": result.rows_written
    }
```

### With FastAPI

```python
from fastapi import FastAPI, BackgroundTasks
from etlx import Pipeline

app = FastAPI()

@app.post("/pipelines/{name}/run")
async def run_pipeline(name: str, background_tasks: BackgroundTasks):
    def execute():
        pipeline = Pipeline.from_yaml(f"pipelines/{name}.yml")
        return pipeline.run()

    background_tasks.add_task(execute)
    return {"status": "started"}
```

### With Prefect

```python
from prefect import flow, task
from etlx import Pipeline

@task
def run_etl(config_path: str):
    pipeline = Pipeline.from_yaml(config_path)
    return pipeline.run()

@flow
def etl_flow():
    result = run_etl("pipeline.yml")
    print(f"Processed {result.rows_written} rows")
```

## API Reference

| Module | Description |
|--------|-------------|
| [Pipeline](pipeline.md) | Main pipeline class |
| [ETLXEngine](engine.md) | Execution engine |
| [Config](config.md) | Configuration models |
| [Quality](quality.md) | Quality check classes |

## Related

- [CLI Reference](../cli/index.md) - Command-line interface
- [Pipeline YAML](../user-guide/configuration/pipeline-yaml.md) - YAML configuration
- [Airflow Integration](../integrations/airflow.md) - Airflow integration
