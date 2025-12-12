# QuickETLEngine Class

The `QuickETLEngine` class provides low-level access to the QuickETL execution engine. Use this for advanced use cases where you need direct control over execution.

!!! tip "Use Pipeline Instead"
    For most use cases, the [Pipeline](pipeline.md) class is recommended. Use `QuickETLEngine` only when you need low-level control.

## Import

```python
from quicketl import QuickETLEngine
```

## Constructor

```python
QuickETLEngine(
    backend: str = "duckdb",
    **options
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | `"duckdb"` | Backend engine name |
| `**options` | | | Backend-specific options |

**Supported Backends:**

- `duckdb` - DuckDB (default)
- `polars` - Polars
- `pandas` - Pandas
- `spark` - Apache Spark
- `datafusion` - Apache DataFusion
- `snowflake` - Snowflake
- `bigquery` - Google BigQuery
- `postgres` - PostgreSQL
- `mysql` - MySQL
- `clickhouse` - ClickHouse

**Example:**

```python
# Default (DuckDB)
engine = QuickETLEngine()

# Specific backend
engine = QuickETLEngine(backend="polars")

# With backend options
engine = QuickETLEngine(
    backend="spark",
    master="local[*]",
    executor_memory="4g"
)
```

## Methods

### `execute`

Execute a pipeline configuration.

```python
QuickETLEngine.execute(
    config: PipelineConfig | dict,
    variables: dict[str, str] | None = None,
    dry_run: bool = False
) -> ExecutionResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `PipelineConfig \| dict` | Pipeline configuration |
| `variables` | `dict[str, str] \| None` | Variable substitutions |
| `dry_run` | `bool` | Execute without writing |

**Returns:** `ExecutionResult`

**Example:**

```python
from quicketl import QuickETLEngine
from quicketl.config import PipelineConfig

engine = QuickETLEngine(backend="duckdb")

config = {
    "name": "test",
    "source": {"type": "file", "path": "data.csv", "format": "csv"},
    "sink": {"type": "file", "path": "out.parquet", "format": "parquet"}
}

result = engine.execute(config)
```

---

### `read_source`

Read data from a source configuration.

```python
QuickETLEngine.read_source(
    source_config: SourceConfig | dict
) -> Table
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_config` | `SourceConfig \| dict` | Source configuration |

**Returns:** Ibis table expression

**Example:**

```python
engine = QuickETLEngine()

table = engine.read_source({
    "type": "file",
    "path": "data/sales.csv",
    "format": "csv"
})

# Now you can use Ibis operations
filtered = table.filter(table.amount > 100)
result = filtered.execute()
```

---

### `write_sink`

Write data to a sink configuration.

```python
QuickETLEngine.write_sink(
    table: Table,
    sink_config: SinkConfig | dict,
    mode: str = "replace"
) -> None
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | `Table` | Ibis table expression |
| `sink_config` | `SinkConfig \| dict` | Sink configuration |
| `mode` | `str` | Write mode: "replace", "append" |

**Example:**

```python
engine = QuickETLEngine()

# Read and transform
table = engine.read_source({"type": "file", "path": "in.csv", "format": "csv"})
filtered = table.filter(table.status == "active")

# Write
engine.write_sink(
    filtered,
    {"type": "file", "path": "out.parquet", "format": "parquet"},
    mode="replace"
)
```

---

### `apply_transform`

Apply a single transform to a table.

```python
QuickETLEngine.apply_transform(
    table: Table,
    transform: TransformConfig | dict
) -> Table
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | `Table` | Input Ibis table |
| `transform` | `TransformConfig \| dict` | Transform configuration |

**Returns:** Transformed Ibis table

**Example:**

```python
engine = QuickETLEngine()

table = engine.read_source(source_config)

# Apply transforms one by one
table = engine.apply_transform(table, {"op": "filter", "predicate": "amount > 0"})
table = engine.apply_transform(table, {"op": "select", "columns": ["id", "amount"]})
```

---

### `apply_transforms`

Apply multiple transforms to a table.

```python
QuickETLEngine.apply_transforms(
    table: Table,
    transforms: list[TransformConfig | dict]
) -> Table
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | `Table` | Input Ibis table |
| `transforms` | `list` | List of transform configurations |

**Returns:** Transformed Ibis table

**Example:**

```python
engine = QuickETLEngine()

table = engine.read_source(source_config)

transforms = [
    {"op": "filter", "predicate": "amount > 0"},
    {"op": "select", "columns": ["id", "name", "amount"]},
    {"op": "sort", "by": [{"column": "amount", "order": "desc"}]}
]

result = engine.apply_transforms(table, transforms)
```

---

### `run_checks`

Execute quality checks on a table.

```python
QuickETLEngine.run_checks(
    table: Table,
    checks: list[CheckConfig | dict]
) -> CheckResults
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | `Table` | Table to validate |
| `checks` | `list` | List of check configurations |

**Returns:** `CheckResults` with pass/fail details

**Example:**

```python
engine = QuickETLEngine()
table = engine.read_source(source_config)

checks = [
    {"check": "not_null", "columns": ["id", "name"]},
    {"check": "unique", "columns": ["id"]},
    {"check": "row_count", "min": 1}
]

results = engine.run_checks(table, checks)
print(f"Passed: {results.passed}, Failed: {results.failed}")

for check in results.details:
    print(f"  {check.name}: {check.status}")
```

---

### `get_connection`

Get the underlying Ibis connection.

```python
QuickETLEngine.get_connection() -> Connection
```

**Returns:** Ibis backend connection

**Example:**

```python
engine = QuickETLEngine(backend="duckdb")
conn = engine.get_connection()

# Execute raw SQL
result = conn.raw_sql("SELECT * FROM read_csv('data.csv') LIMIT 10")
```

## Properties

### `backend`

The configured backend name.

```python
engine.backend  # -> str
```

### `is_connected`

Whether the engine has an active connection.

```python
engine.is_connected  # -> bool
```

## ExecutionResult

Result returned by `execute()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | `bool` | Whether execution succeeded |
| `duration_ms` | `float` | Execution time |
| `rows_processed` | `int` | Rows read |
| `rows_written` | `int` | Rows written |
| `check_results` | `CheckResults \| None` | Quality check results |
| `error` | `Exception \| None` | Error if failed |
| `table` | `Table \| None` | Result table (if dry_run) |

## CheckResults

Result returned by `run_checks()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `passed` | `int` | Number passed |
| `failed` | `int` | Number failed |
| `total` | `int` | Total checks |
| `details` | `list[CheckResult]` | Individual results |

## Complete Example

```python
from quicketl import QuickETLEngine

# Initialize engine
engine = QuickETLEngine(backend="duckdb")

# Read source
table = engine.read_source({
    "type": "file",
    "path": "data/sales.csv",
    "format": "csv"
})

# Apply transforms
transforms = [
    {"op": "filter", "predicate": "status = 'completed'"},
    {"op": "derive_column", "name": "total", "expr": "quantity * price"},
    {"op": "aggregate", "group_by": ["category"], "aggregations": {"revenue": "sum(total)"}}
]
table = engine.apply_transforms(table, transforms)

# Run quality checks
checks = [
    {"check": "not_null", "columns": ["category", "revenue"]},
    {"check": "expression", "expr": "revenue >= 0"}
]
check_results = engine.run_checks(table, checks)

if check_results.failed > 0:
    print("Quality checks failed!")
    for detail in check_results.details:
        if not detail.passed:
            print(f"  - {detail.name}: {detail.message}")
else:
    # Write output
    engine.write_sink(
        table,
        {"type": "file", "path": "output/revenue.parquet", "format": "parquet"}
    )
    print("Pipeline completed successfully")
```

## Related

- [Pipeline](pipeline.md) - High-level pipeline API
- [Configuration Models](config.md) - Configuration types
- [Backend Selection](../guides/backends/index.md) - Choosing backends
