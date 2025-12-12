# Architecture

This document describes the internal architecture of ETLX.

## Overview

ETLX follows a layered architecture:

```
┌─────────────────────────────────────────┐
│                  CLI                     │
├─────────────────────────────────────────┤
│              Pipeline API                │
├─────────────────────────────────────────┤
│         Configuration Layer              │
├─────────────────────────────────────────┤
│            Engine Layer                  │
├─────────────────────────────────────────┤
│          Ibis Abstraction                │
├─────────────────────────────────────────┤
│    DuckDB │ Polars │ Spark │ ...        │
└─────────────────────────────────────────┘
```

## Core Components

### Configuration System

Pydantic models for type-safe configuration:

```python
# etlx/config/models.py
class PipelineConfig(BaseModel):
    name: str
    description: str | None = None
    engine: str = "duckdb"
    source: SourceConfig
    transforms: list[TransformConfig] = []
    checks: list[CheckConfig] = []
    sink: SinkConfig
```

Discriminated unions for transform types:

```python
TransformConfig = Annotated[
    SelectTransform | FilterTransform | DeriveColumnTransform | ...,
    Field(discriminator="op")
]
```

### Engine Layer

The engine orchestrates pipeline execution:

```python
# etlx/engine/engine.py
class ETLXEngine:
    def __init__(self, backend: str = "duckdb"):
        self.backend = backend
        self.connection = self._create_connection()

    def execute(self, config: PipelineConfig) -> ExecutionResult:
        table = self.read_source(config.source)
        table = self.apply_transforms(table, config.transforms)
        check_results = self.run_checks(table, config.checks)
        self.write_sink(table, config.sink)
        return ExecutionResult(...)
```

### Transform System

Each transform is a class implementing a common interface:

```python
# etlx/transforms/base.py
class BaseTransform(ABC):
    @abstractmethod
    def apply(self, table: Table) -> Table:
        """Apply transform to table."""
        pass

# etlx/transforms/filter.py
class FilterTransform(BaseTransform):
    def __init__(self, predicate: str):
        self.predicate = predicate

    def apply(self, table: Table) -> Table:
        return table.filter(self.predicate)
```

### Quality Framework

Quality checks follow the same pattern:

```python
# etlx/quality/base.py
class BaseCheck(ABC):
    @abstractmethod
    def run(self, table: Table, engine: ETLXEngine) -> CheckResult:
        """Execute quality check."""
        pass

# etlx/quality/not_null.py
class NotNullCheck(BaseCheck):
    def __init__(self, columns: list[str]):
        self.columns = columns

    def run(self, table: Table, engine: ETLXEngine) -> CheckResult:
        null_counts = {}
        for col in self.columns:
            null_count = table.filter(f"{col} IS NULL").count().execute()
            null_counts[col] = null_count

        passed = all(c == 0 for c in null_counts.values())
        return CheckResult(passed=passed, details=null_counts)
```

### Backend Abstraction

Ibis provides the backend abstraction layer:

```python
# etlx/backends/factory.py
def create_connection(backend: str) -> ibis.BaseBackend:
    if backend == "duckdb":
        return ibis.duckdb.connect()
    elif backend == "polars":
        return ibis.polars.connect()
    elif backend == "spark":
        return ibis.spark.connect()
    # ... etc
```

## Data Flow

```
YAML Config
    │
    ▼
┌─────────────┐
│ Parse YAML  │ ─→ PipelineConfig (Pydantic)
└─────────────┘
    │
    ▼
┌─────────────┐
│ Read Source │ ─→ Ibis Table Expression
└─────────────┘
    │
    ▼
┌─────────────┐
│ Transforms  │ ─→ Ibis Table Expression (transformed)
└─────────────┘
    │
    ▼
┌─────────────┐
│   Checks    │ ─→ CheckResults
└─────────────┘
    │
    ▼
┌─────────────┐
│ Write Sink  │ ─→ Output (file/database)
└─────────────┘
```

## Key Design Decisions

### Why Ibis?

Ibis provides:

- Unified API across 15+ backends
- Lazy evaluation (query optimization)
- Familiar pandas-like syntax
- SQL expression support

### Why Pydantic?

Pydantic provides:

- Runtime type validation
- Clear error messages
- JSON Schema generation
- IDE autocomplete

### Why YAML?

YAML provides:

- Human-readable configuration
- Comment support
- Version control friendly
- Easy environment variable substitution

## Extension Points

### Adding a New Transform

1. Create transform class:

```python
# etlx/transforms/my_transform.py
class MyTransform(BaseTransform):
    op: Literal["my_transform"] = "my_transform"
    param: str

    def apply(self, table: Table) -> Table:
        # Implementation
        return table
```

2. Register in discriminated union:

```python
# etlx/config/transforms.py
TransformConfig = Annotated[
    ... | MyTransform,
    Field(discriminator="op")
]
```

### Adding a New Backend

1. Implement connection factory:

```python
# etlx/backends/my_backend.py
def create_my_backend_connection(**options):
    return ibis.my_backend.connect(**options)
```

2. Register in backend factory:

```python
# etlx/backends/factory.py
BACKENDS["my_backend"] = create_my_backend_connection
```

### Adding a New Check

1. Create check class:

```python
# etlx/quality/my_check.py
class MyCheck(BaseCheck):
    check: Literal["my_check"] = "my_check"

    def run(self, table: Table, engine: ETLXEngine) -> CheckResult:
        # Implementation
        return CheckResult(...)
```

2. Register in discriminated union.

## Directory Structure

```
src/etlx/
├── __init__.py
├── cli/                 # Command-line interface
│   ├── __init__.py
│   ├── main.py
│   ├── run.py
│   ├── validate.py
│   └── init.py
├── config/              # Configuration models
│   ├── __init__.py
│   ├── models.py
│   ├── sources.py
│   ├── sinks.py
│   └── transforms.py
├── engine/              # Execution engine
│   ├── __init__.py
│   ├── engine.py
│   └── result.py
├── transforms/          # Transform implementations
│   ├── __init__.py
│   ├── base.py
│   ├── select.py
│   ├── filter.py
│   └── ...
├── quality/             # Quality checks
│   ├── __init__.py
│   ├── base.py
│   ├── not_null.py
│   └── ...
├── backends/            # Backend factory
│   ├── __init__.py
│   └── factory.py
└── io/                  # I/O handlers
    ├── __init__.py
    ├── readers.py
    └── writers.py
```

## Related

- [Contributing Guide](contributing.md) - How to contribute
- [API Reference](../api/index.md) - API documentation
