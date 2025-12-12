# Pipeline Class

The `Pipeline` class is the main entry point for working with QuickETL pipelines programmatically.

## Import

```python
from quicketl import Pipeline
```

## Class Methods

### `from_yaml`

Load a pipeline from a YAML configuration file.

```python
Pipeline.from_yaml(path: str | Path) -> Pipeline
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Path to YAML configuration file |

**Returns:** `Pipeline` instance

**Example:**

```python
pipeline = Pipeline.from_yaml("pipelines/sales_etl.yml")
```

---

### `from_config`

Create a pipeline from a configuration dictionary.

```python
Pipeline.from_config(config: dict) -> Pipeline
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `dict` | Pipeline configuration dictionary |

**Returns:** `Pipeline` instance

**Example:**

```python
pipeline = Pipeline.from_config({
    "name": "sales_etl",
    "engine": "duckdb",
    "source": {
        "type": "file",
        "path": "data/sales.csv",
        "format": "csv"
    },
    "transforms": [
        {"op": "filter", "predicate": "amount > 0"},
        {"op": "select", "columns": ["id", "name", "amount"]}
    ],
    "sink": {
        "type": "file",
        "path": "output/results.parquet",
        "format": "parquet"
    }
})
```

---

### `from_model`

Create a pipeline from a Pydantic configuration model.

```python
Pipeline.from_model(config: PipelineConfig) -> Pipeline
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `PipelineConfig` | Pydantic configuration model |

**Returns:** `Pipeline` instance

**Example:**

```python
from quicketl.config import PipelineConfig, FileSource, FileSink

config = PipelineConfig(
    name="sales_etl",
    engine="duckdb",
    source=FileSource(type="file", path="data.csv", format="csv"),
    sink=FileSink(type="file", path="output.parquet", format="parquet")
)

pipeline = Pipeline.from_model(config)
```

## Instance Methods

### `run`

Execute the pipeline.

```python
Pipeline.run(
    variables: dict[str, str] | None = None,
    engine: str | None = None,
    dry_run: bool = False,
    fail_on_checks: bool = True
) -> PipelineResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `variables` | `dict[str, str] \| None` | `None` | Variable substitutions |
| `engine` | `str \| None` | `None` | Override engine from config |
| `dry_run` | `bool` | `False` | Execute without writing output |
| `fail_on_checks` | `bool` | `True` | Raise exception on check failure |

**Returns:** `PipelineResult` with execution details

**Raises:**

- `ConfigurationError` - Invalid configuration
- `ExecutionError` - Execution failure
- `QualityCheckError` - Quality check failure (if `fail_on_checks=True`)

**Examples:**

```python
# Basic run
result = pipeline.run()

# With variables
result = pipeline.run(variables={
    "DATE": "2025-01-15",
    "REGION": "north"
})

# Override engine
result = pipeline.run(engine="polars")

# Dry run (no output written)
result = pipeline.run(dry_run=True)

# Continue on check failures
result = pipeline.run(fail_on_checks=False)
if result.checks_failed > 0:
    print(f"Warning: {result.checks_failed} checks failed")
```

---

### `validate`

Validate pipeline configuration without executing.

```python
Pipeline.validate() -> list[str]
```

**Returns:** List of validation error messages (empty if valid)

**Example:**

```python
errors = pipeline.validate()
if errors:
    for error in errors:
        print(f"Validation error: {error}")
else:
    print("Configuration is valid")
    result = pipeline.run()
```

---

### `explain`

Get an execution plan explanation.

```python
Pipeline.explain() -> str
```

**Returns:** Human-readable execution plan

**Example:**

```python
print(pipeline.explain())
```

Output:

```
Pipeline: sales_etl
Engine: duckdb

Steps:
1. Read from: data/sales.csv (csv)
2. Filter: amount > 0
3. Select: id, name, amount
4. Quality checks: 2 checks
5. Write to: output/results.parquet (parquet)
```

## Properties

### `name`

Pipeline name from configuration.

```python
pipeline.name  # -> str
```

### `config`

Access the underlying configuration model.

```python
pipeline.config  # -> PipelineConfig
```

### `engine`

Configured engine name.

```python
pipeline.engine  # -> str
```

## PipelineResult

The result returned by `Pipeline.run()`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `pipeline_name` | `str` | Name of the pipeline |
| `status` | `str` | "SUCCESS" or "FAILED" |
| `duration_ms` | `float` | Execution time in milliseconds |
| `rows_processed` | `int` | Total rows read from source |
| `rows_written` | `int` | Rows written to sink |
| `checks_passed` | `int` | Number of passed quality checks |
| `checks_failed` | `int` | Number of failed quality checks |
| `error` | `str \| None` | Error message if failed |

### Methods

#### `to_dict`

Convert result to dictionary.

```python
result.to_dict() -> dict
```

**Example:**

```python
result = pipeline.run()
data = result.to_dict()
# {
#     "pipeline_name": "sales_etl",
#     "status": "SUCCESS",
#     "duration_ms": 245.3,
#     "rows_processed": 1000,
#     "rows_written": 950,
#     "checks_passed": 2,
#     "checks_failed": 0
# }
```

#### `to_json`

Convert result to JSON string.

```python
result.to_json() -> str
```

#### `to_dataframe`

Get the result data as a DataFrame.

```python
result.to_dataframe() -> Any  # Returns backend-specific DataFrame
```

**Example:**

```python
result = pipeline.run()
df = result.to_dataframe()
print(df.head())
```

## Complete Example

```python
from quicketl import Pipeline
from quicketl.exceptions import QualityCheckError

# Load pipeline
pipeline = Pipeline.from_yaml("pipelines/daily_sales.yml")

# Validate first
errors = pipeline.validate()
if errors:
    raise ValueError(f"Invalid config: {errors}")

# Show execution plan
print(pipeline.explain())

# Run with variables
try:
    result = pipeline.run(
        variables={"DATE": "2025-01-15"},
        fail_on_checks=True
    )

    print(f"✓ Pipeline completed in {result.duration_ms:.1f}ms")
    print(f"  Rows: {result.rows_processed} → {result.rows_written}")
    print(f"  Checks: {result.checks_passed} passed")

except QualityCheckError as e:
    print(f"✗ Quality checks failed")
    for check in e.failed_checks:
        print(f"  - {check}")
```

## Related

- [QuickETLEngine](engine.md) - Low-level engine API
- [Configuration Models](config.md) - Type-safe configuration
- [CLI run Command](../reference/cli.md#run) - Command-line execution
