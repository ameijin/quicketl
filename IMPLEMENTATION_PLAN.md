# ETLX Framework Implementation Plan

## Overview
Build the ETLX Framework MVP (v0.1) - a Python ETL/ELT framework with unified engine abstraction supporting Polars, DuckDB, Spark, pandas, and 20+ backends.

**Key Decisions:**
- Package manager: uv
- Layout: src/etlx/
- Testing: pytest + hypothesis
- CI/CD: GitHub Actions
- **Engine Layer: Hybrid Ibis Approach** - Use Ibis as internal implementation, expose simplified ETLX API

## Why Ibis (Hybrid Approach)
Ibis is a mature, portable Python dataframe library that handles the hard part of translating operations across backends.

**Benefits:**
- 20+ supported backends (Polars, DuckDB, Spark, pandas, BigQuery, Snowflake, Trino, etc.)
- Battle-tested expression system
- Lazy evaluation / deferred execution
- SQL compilation for debugging
- Active development (Voltron Data backed)

**Our Value Add (ETLX Layer):**
- Simplified, ETL-focused API (not full dataframe API)
- YAML configuration with variable substitution
- Quality checks layer
- Pipeline orchestration
- CLI tooling
- Airflow integration
- Opinionated defaults for common ETL patterns

---

## Project Structure

```
quicketl-cloud/
├── .github/workflows/
│   ├── ci.yml                    # Lint, test, type-check
│   └── release.yml               # PyPI publishing
├── src/etlx/
│   ├── __init__.py               # Public API exports
│   ├── py.typed                  # PEP 561 marker
│   ├── _version.py               # Version (0.1.0)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── models.py             # SourceConfig, SinkConfig (discriminated unions)
│   │   ├── transforms.py         # TransformStep discriminated union
│   │   ├── checks.py             # CheckConfig discriminated union
│   │   ├── loader.py             # YAML loading with variable substitution
│   │   └── schema.py             # JSON Schema generation
│   ├── engines/
│   │   ├── __init__.py           # Engine factory, get_backend()
│   │   ├── base.py               # ETLXEngine wrapper around Ibis
│   │   ├── backends.py           # Backend configuration (connection strings, options)
│   │   └── expressions.py        # Expression helpers (ETLX syntax → Ibis expressions)
│   ├── io/
│   │   ├── __init__.py
│   │   ├── readers/
│   │   │   ├── __init__.py
│   │   │   ├── file.py           # CSV, Parquet, JSON (fsspec)
│   │   │   └── database.py       # PostgreSQL, MySQL, SQL Server
│   │   └── writers/
│   │       ├── __init__.py
│   │       ├── file.py           # Parquet (fsspec)
│   │       └── database.py       # PostgreSQL
│   ├── quality/
│   │   ├── __init__.py
│   │   ├── checks.py             # 5 check implementations
│   │   └── runner.py             # Check execution
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Pipeline class
│   │   ├── context.py            # Execution context
│   │   └── result.py             # PipelineResult
│   ├── logging/
│   │   ├── __init__.py
│   │   └── setup.py              # structlog configuration
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── airflow.py            # Airflow task decorator
│   └── cli/
│       ├── __init__.py
│       ├── main.py               # Main Typer app
│       ├── run.py                # etlx run
│       ├── validate.py           # etlx validate
│       ├── init.py               # etlx init
│       ├── info.py               # etlx info
│       └── schema.py             # etlx schema
├── tests/
│   ├── conftest.py               # Fixtures, engine parametrization
│   ├── unit/
│   ├── integration/
│   ├── parity/                   # Engine parity tests
│   └── fixtures/
├── docs/
├── examples/
├── pyproject.toml
├── README.md
├── LICENSE
└── .pre-commit-config.yaml
```

---

## Implementation Phases

### Phase 1: Foundation (Files 1-7)
1. `pyproject.toml` - Project setup with uv, dependencies, extras
2. `src/etlx/_version.py` - Version info
3. `src/etlx/logging/setup.py` - structlog configuration (JSON + console)
4. `src/etlx/config/models.py` - SourceConfig, SinkConfig (Pydantic discriminated unions)
5. `src/etlx/config/transforms.py` - TransformStep union (12 ops)
6. `src/etlx/config/checks.py` - CheckConfig union (5 checks)
7. `src/etlx/config/loader.py` - YAML loading with ${VAR} substitution

### Phase 2: Engine Layer - Ibis Integration (Files 8-10)
8. `src/etlx/engines/base.py` - ETLXEngine class wrapping Ibis backend
9. `src/etlx/engines/backends.py` - Backend registry and connection helpers
10. `src/etlx/engines/expressions.py` - ETLX expression syntax → Ibis expressions

**Key Insight:** With Ibis, we get Polars, DuckDB, Spark, pandas, BigQuery, Snowflake, and 15+ more backends for free. No per-engine implementation needed.

### Phase 3: IO Layer (Files 11-14)
11. `src/etlx/io/readers/file.py` - CSV, Parquet, JSON (Ibis handles via backends)
12. `src/etlx/io/writers/file.py` - Parquet writer with partitioning
13. `src/etlx/io/readers/database.py` - Database reads (Ibis handles natively)
14. `src/etlx/io/writers/database.py` - Database writes

**Note:** Ibis has native read_parquet(), read_csv(), read_json() and database connections - we wrap these.

### Phase 4: Quality & Pipeline (Files 15-19)
15. `src/etlx/quality/checks.py` - 5 check implementations using Ibis expressions
16. `src/etlx/quality/runner.py` - Check execution with reporting
17. `src/etlx/pipeline/context.py` - Execution context
18. `src/etlx/pipeline/result.py` - PipelineResult dataclass
19. `src/etlx/pipeline/pipeline.py` - Pipeline class (builder + YAML)

### Phase 5: CLI & Integration (Files 20-26)
20. `src/etlx/cli/run.py` - etlx run command
21. `src/etlx/cli/validate.py` - etlx validate command
22. `src/etlx/cli/init.py` - etlx init scaffolding
23. `src/etlx/cli/info.py` - etlx info command
24. `src/etlx/cli/schema.py` - etlx schema command
25. `src/etlx/cli/main.py` - Main Typer app assembly
26. `src/etlx/integrations/airflow.py` - Airflow task decorator

### Phase 6: Polish (Files 27-31)
27. `tests/conftest.py` - Test fixtures with backend parametrization
28. `tests/parity/test_transform_parity.py` - Backend parity tests
29. `.github/workflows/ci.yml` - CI pipeline
30. `README.md` - Documentation
31. `examples/` - Working examples

---

## Key Design Patterns

### 1. Pydantic Discriminated Unions
```python
# Use Literal types with Field(discriminator='type')
class FileSource(BaseModel):
    type: Literal["file"] = "file"
    path: str
    format: Literal["csv", "parquet", "json"] = "parquet"

class DatabaseSource(BaseModel):
    type: Literal["database"] = "database"
    connection: str
    query: str | None = None

SourceConfig = Annotated[
    Union[FileSource, DatabaseSource],
    Field(discriminator="type")
]
```

### 2. Ibis-Based Engine Wrapper
```python
import ibis
from ibis import _

class ETLXEngine:
    """ETLX wrapper around Ibis backend."""

    def __init__(self, backend: str = "duckdb", **kwargs):
        self._backend = ibis.connect(f"{backend}://", **kwargs)

    def read_file(self, path: str, format: str) -> ibis.Table:
        match format:
            case "parquet": return self._backend.read_parquet(path)
            case "csv": return self._backend.read_csv(path)
            case "json": return self._backend.read_json(path)

    def filter(self, table: ibis.Table, predicate: str) -> ibis.Table:
        # Ibis supports SQL-like expressions natively
        return table.filter(ibis._.sql(predicate))

    def derive_column(self, table: ibis.Table, name: str, expr: str) -> ibis.Table:
        return table.mutate(**{name: ibis._.sql(expr)})

    def to_polars(self, table: ibis.Table):
        return self._backend.to_polars(table)

    def to_pandas(self, table: ibis.Table):
        return self._backend.to_pandas(table)
```

### 3. Backend Parity Testing (Ibis handles this!)
```python
@pytest.fixture(params=["duckdb", "polars", "datafusion"])
def backend(request):
    return ibis.connect(f"{request.param}://")

def test_filter_parity(backend):
    table = backend.read_parquet("test.parquet")
    result = table.filter(table.amount > 150)
    # Ibis guarantees same semantics across backends
    assert result.count().execute() == 2
```

### 4. Deferred Execution (Lazy by Default)
```python
# Ibis expressions are lazy - only execute when needed
table = engine.read_file("data.parquet", "parquet")
filtered = engine.filter(table, "amount > 100")
aggregated = engine.aggregate(filtered, ["region"], {"total": "sum(amount)"})

# Nothing executed yet! Only when we call:
result = aggregated.to_polars()  # Now it executes
```

### 5. structlog Configuration
```python
# JSON for production, pretty console for development
if sys.stderr.isatty():
    processors = [..., structlog.dev.ConsoleRenderer()]
else:
    processors = [..., structlog.processors.JSONRenderer()]
```

---

## Core Dependencies (pyproject.toml)

```toml
dependencies = [
    # Core
    "pydantic>=2.10",
    "pyyaml>=6.0",
    "structlog>=24.0",
    "typer>=0.12",

    # Ibis (the engine abstraction layer)
    "ibis-framework[duckdb,polars]>=9.0",

    # Cloud storage
    "fsspec>=2024.6",
]

[project.optional-dependencies]
# Additional Ibis backends
spark = ["ibis-framework[pyspark]>=9.0"]
pandas = ["ibis-framework[pandas]>=9.0"]
datafusion = ["ibis-framework[datafusion]>=9.0"]

# Cloud storage
aws = ["s3fs>=2024.6", "boto3>=1.34"]
gcp = ["gcsfs>=2024.6", "google-cloud-storage>=2.14"]
azure = ["adlfs>=2024.4", "azure-storage-blob>=12.19"]

# Data warehouses (via Ibis)
snowflake = ["ibis-framework[snowflake]>=9.0"]
bigquery = ["ibis-framework[bigquery]>=9.0"]
trino = ["ibis-framework[trino]>=9.0"]
postgres = ["ibis-framework[postgres]>=9.0"]

# Development
dev = ["pytest>=8.0", "pytest-cov>=5.0", "hypothesis>=6.100", "ruff>=0.5", "mypy>=1.10"]

# All backends
all = ["etlx[spark,pandas,datafusion,aws,gcp,azure,snowflake,bigquery,trino,postgres,dev]"]
```

**Key Change:** Ibis provides 20+ backends through optional dependencies. We just pick which ones to install.

---

## Transform Operations (12 total)
1. `select` - Choose columns
2. `rename` - Rename columns
3. `filter` - Filter rows (SQL predicate)
4. `derive_column` - Computed column (SQL expression)
5. `cast` - Type conversion
6. `fill_null` - Replace nulls
7. `dedup` - Remove duplicates
8. `sort` - Order rows
9. `join` - Join DataFrames
10. `aggregate` - Group + aggregate
11. `union` - Vertical concat
12. `limit` - Take N rows

## Quality Checks (5 total)
1. `not_null` - Fail on nulls
2. `unique` - Fail on duplicates
3. `row_count` - Row count bounds
4. `accepted_values` - Value whitelist
5. `expression` - Custom predicate

---

## CLI Commands
```bash
etlx run pipeline.yml                    # Run pipeline
etlx run pipeline.yml --engine duckdb    # Override engine
etlx run pipeline.yml --var RUN_DATE=2025-12-01
etlx validate pipeline.yml               # Validate config
etlx init my_project                     # Create project
etlx info pipeline.yml                   # Show pipeline info
etlx schema                              # Output JSON schema
```

---

## Success Criteria
- [ ] All 12 transform operations working via Ibis abstraction
- [ ] Backend parity tests passing (DuckDB, Polars, DataFusion)
- [ ] File IO: CSV, Parquet, JSON read; Parquet write (local + cloud)
- [ ] Database connections working (PostgreSQL via Ibis)
- [ ] All 5 quality checks implemented using Ibis expressions
- [ ] CLI commands functional
- [ ] >80% test coverage
- [ ] Type hints throughout (mypy strict)
- [ ] CI/CD pipeline running

## Supported Backends (via Ibis)
**Local/Embedded:**
- DuckDB (default) - Fast analytical queries
- Polars - Rust-powered DataFrame
- DataFusion - Apache Arrow-native
- pandas - Legacy compatibility

**Cloud Data Warehouses:**
- BigQuery
- Snowflake
- Trino/Starburst
- Databricks

**Databases:**
- PostgreSQL
- MySQL
- SQLite
- ClickHouse
