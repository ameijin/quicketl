# ETLX Framework
## Product Requirements Document v1.0

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 2025 |
| **Status** | Draft |
| **Target** | Python 3.12+ (tested on 3.13, 3.14) \| MIT License |

---

## Executive Summary

ETLX is a personal Python ETL/ELT framework designed for reusability across projects, clients, and organizations. It provides a unified abstraction layer supporting multiple compute engines (Polars, DuckDB, Spark, BigQuery, Snowflake) and storage backends while remaining lightweight enough for a solo developer to maintain.

**Primary Goal:** A portable data engineering toolkit that travels with you—same patterns, same code, regardless of where you're working.

**Key Architecture Decision:** ETLX uses [Ibis](https://ibis-project.org) (Apache 2.0 licensed) as its internal engine abstraction layer. Users interact with ETLX's simplified API—Ibis is an implementation detail, not a user-facing dependency. This gives you 20+ backend support with minimal code to maintain.

**Use Cases:**
- Drop into any consulting engagement with a ready-to-go ETL foundation
- Standardize pipeline patterns across all personal/client projects
- Demonstrate engineering maturity in interviews and technical discussions
- Eliminate "reinventing the wheel" on every new data project

---

## 1. Objectives & Constraints

### 1.1 Primary Objectives

1. **Unified Engine Abstraction:** Single API across Polars, DuckDB, pandas, and PySpark
2. **Configuration-Driven Pipelines:** YAML-first with Python API parity
3. **Cloud-Agnostic:** First-class support for AWS, GCP, and Azure via fsspec
4. **Orchestrator-Agnostic:** Native Airflow integration; compatible with Prefect/Dagster
5. **Solo-Maintainable:** Small codebase, minimal dependencies, easy to extend
6. **AI-Assisted Development Ready:** Clear interfaces, comprehensive type hints, LLM-parseable docs

### 1.2 Design Principles

- **Convention over configuration:** Sensible defaults, override when needed
- **Explicit over implicit:** No magic; clear data flow
- **Composable:** Mix and match engines, sources, sinks, transforms
- **Testable:** Every component unit-testable in isolation
- **Documented:** Self-documenting configs, generated schema docs

### 1.3 Non-Goals

- Not replacing dbt (complementary for SQL-first warehouse transforms)
- Not a hosted platform or SaaS
- Not a workflow scheduler (integrates with existing orchestrators)
- Not trying to handle every edge case (80/20 rule—cover common patterns well)

### 1.4 Success Metrics

| Metric | MVP Target | v1.0 Target |
|--------|------------|-------------|
| Engine coverage | Polars + DuckDB | + Spark + pandas |
| Transform operations | 12 core ops | 20+ ops |
| Test coverage | >80% | >90% |
| Documentation | README + examples | Full docs site |
| Setup time (new project) | <5 minutes | <2 minutes |

---

## 2. Technology Stack (December 2025)

### 2.1 Core Dependencies

| Category | Package | Version / Notes |
|----------|---------|-----------------|
| Runtime | Python | 3.12+ (tested on 3.13, 3.14) |
| Package Manager | uv | Fast Rust-based manager with lockfile |
| Config/Validation | Pydantic | 2.10+ (discriminated unions, JSON Schema) |
| **Engine Layer** | **Ibis** | **10.x+ (internal abstraction—not user-facing)** |
| Cloud Storage | fsspec | + s3fs, gcsfs, adlfs for cloud URIs |
| Logging | structlog | Structured JSON logs, cloud-native |
| Observability | OpenTelemetry | Traces + metrics |
| Lineage | OpenLineage | Industry standard, Airflow 2.9+ native |
| CLI | Typer | Modern CLI framework |
| Testing | pytest + hypothesis | Property-based testing for engine parity |

### 2.2 Ibis-Supported Backends (Available via ETLX)

Ibis provides the engine abstraction internally. Users just specify `engine: <name>` in config:

| Backend | Type | Notes |
|---------|------|-------|
| **Polars** | Local DataFrame | Default for small/medium data, fastest |
| **DuckDB** | Local SQL | Great for SQL-native transforms, <100GB |
| **pandas** | Local DataFrame | Legacy support, PyArrow backend |
| **PySpark** | Distributed | Databricks, EMR, Synapse |
| **Snowflake** | Cloud Warehouse | Direct warehouse execution |
| **BigQuery** | Cloud Warehouse | Direct warehouse execution |
| **PostgreSQL** | Database | Pushdown queries to Postgres |
| **MySQL** | Database | Pushdown queries to MySQL |
| **SQLite** | Local Database | Lightweight local SQL |
| **ClickHouse** | OLAP | High-performance analytics |
| **Trino** | Query Federation | Cross-source queries |

**Note:** Users never import or interact with Ibis directly—it's an internal implementation detail.

### 2.3 Cloud Provider Support

Provider-agnostic via fsspec abstraction—same pipeline YAML works everywhere:

| Provider | Storage | URI Format | Credential Source |
|----------|---------|------------|-------------------|
| **AWS** | S3 | `s3://bucket/path` | `AWS_PROFILE`, IAM role, env vars |
| **GCP** | Cloud Storage | `gs://bucket/path` | `GOOGLE_APPLICATION_CREDENTIALS` |
| **Azure** | ADLS Gen2 | `abfss://container@account.dfs.core.windows.net/path` | Connection string or managed identity |
| **Local** | Filesystem | `/path/to/file` | N/A |
| **MinIO/R2** | S3-compatible | `s3://bucket/path` | Custom endpoint config |

### 2.4 Optional Dependencies

Installed via extras to keep base install light:

```bash
pip install etlx                     # Core (Polars + DuckDB backends)
pip install etlx[spark]              # + PySpark backend
pip install etlx[aws]                # + s3fs for S3 access
pip install etlx[gcp]                # + gcsfs + BigQuery backend
pip install etlx[azure]              # + adlfs for ADLS access
pip install etlx[snowflake]          # + Snowflake backend
pip install etlx[all]                # Everything
```

Or with uv (recommended):

```bash
uv add etlx
uv add etlx --extra spark --extra aws
```

---

## 3. Architecture

### 3.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Configuration Layer                     │
│  (Pydantic models: Pipeline, Source, Sink, Transform, Check) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Engine Layer                          │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │  Polars  │ │  DuckDB  │ │  Spark   │ │  pandas  │      │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    IO Layer     │ │ Transform Layer │ │  Quality Layer  │
│ (Sources/Sinks) │ │  (Operations)   │ │   (Checks)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Observability Layer                       │
│         (structlog, OpenLineage, OpenTelemetry)             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Engine Interface

ETLX wraps Ibis internally, exposing a simplified API. Users never import Ibis directly:

```python
# Internal implementation (users don't see this)
import ibis

class ETLXEngine:
    """Thin wrapper around Ibis backends."""
    
    def __init__(self, backend: str = "polars"):
        self.backend = backend
        self._conn = self._connect(backend)
    
    def _connect(self, backend: str):
        """Connect to the specified Ibis backend."""
        match backend:
            case "polars":
                return ibis.polars.connect()
            case "duckdb":
                return ibis.duckdb.connect()
            case "spark":
                return ibis.pyspark.connect()
            case "snowflake":
                return ibis.snowflake.connect(...)
            case "bigquery":
                return ibis.bigquery.connect(...)
            case _:
                raise ValueError(f"Unknown backend: {backend}")
    
    def read_source(self, config: SourceConfig) -> ibis.Table:
        """Read from source into Ibis table expression."""
        match config.type:
            case "file":
                return self._conn.read_parquet(config.path)
            case "database":
                return self._conn.sql(config.query)
            case "table":
                return self._conn.table(config.table)
    
    def execute_transforms(self, table: ibis.Table, transforms: list) -> ibis.Table:
        """Apply transforms using Ibis expressions."""
        for t in transforms:
            table = self._apply_transform(table, t)
        return table
    
    def _apply_transform(self, table: ibis.Table, transform: TransformStep):
        """Map ETLX transform to Ibis operation."""
        match transform.op:
            case "select":
                return table.select(transform.columns)
            case "filter":
                return table.filter(transform.predicate)
            case "derive_column":
                return table.mutate(**{transform.name: transform.expr})
            case "aggregate":
                return table.group_by(transform.group_by).aggregate(...)
            # ... other transforms
    
    def write_sink(self, table: ibis.Table, config: SinkConfig) -> WriteResult:
        """Materialize and write to sink."""
        df = table.to_polars()  # or to_pandas(), to_pyarrow()
        # Write using fsspec/native connectors
        ...
```

**Key insight:** The transform operations are expressed in Ibis's expression language internally, but users write simple YAML/Python config. Ibis handles translating to each backend's native operations.

### 3.3 Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Any

# Sources
class FileSource(BaseModel):
    type: Literal["file"] = "file"
    path: str
    format: Literal["csv", "parquet", "json"] = "parquet"
    options: dict[str, Any] = Field(default_factory=dict)

class DatabaseSource(BaseModel):
    type: Literal["database"] = "database"
    connection: str
    query: str | None = None
    table: str | None = None

class IcebergSource(BaseModel):
    type: Literal["iceberg"] = "iceberg"
    catalog: str
    database: str
    table: str
    snapshot_id: int | None = None

SourceConfig = Annotated[
    Union[FileSource, DatabaseSource, IcebergSource],
    Field(discriminator="type")
]

# Sinks
class FileSink(BaseModel):
    type: Literal["file"] = "file"
    path: str
    format: Literal["parquet", "csv"] = "parquet"
    partition_by: list[str] = Field(default_factory=list)
    mode: Literal["overwrite", "append"] = "overwrite"

class DatabaseSink(BaseModel):
    type: Literal["database"] = "database"
    connection: str
    table: str
    mode: Literal["append", "truncate", "upsert"] = "append"
    upsert_keys: list[str] = Field(default_factory=list)

SinkConfig = Annotated[
    Union[FileSink, DatabaseSink],
    Field(discriminator="type")
]

# Pipeline
class PipelineConfig(BaseModel):
    name: str
    description: str = ""
    engine: Literal["polars", "duckdb", "spark", "pandas"] = "polars"
    source: SourceConfig
    transforms: list[TransformStep] = Field(default_factory=list)
    checks: list[CheckConfig] = Field(default_factory=list)
    sink: SinkConfig
```

### 3.4 Example Pipeline YAML

```yaml
name: daily_sales_etl
description: Extract sales, compute revenue, aggregate by region
engine: polars

source:
  type: database
  connection: ${POSTGRES_URI}
  query: |
    SELECT * FROM sales 
    WHERE sale_date = '${RUN_DATE}'

transforms:
  - op: derive_column
    name: revenue
    expr: quantity * unit_price
  
  - op: filter
    predicate: revenue > 0
  
  - op: aggregate
    group_by: [region, product_category]
    aggs:
      total_revenue: sum(revenue)
      order_count: count(*)
      avg_order_value: mean(revenue)

checks:
  - type: not_null
    columns: [region, total_revenue]
  - type: row_count
    min: 1

sink:
  type: file
  path: s3://analytics-bucket/daily_sales/${RUN_DATE}/
  format: parquet
  partition_by: [region]
```

### 3.5 Python API (Equivalent)

```python
from etlx import Pipeline, sources, sinks, transforms as T, checks as C

pipeline = (
    Pipeline("daily_sales_etl")
    .source(sources.database(
        connection="${POSTGRES_URI}",
        query="SELECT * FROM sales WHERE sale_date = '${RUN_DATE}'"
    ))
    .transform(T.derive_column("revenue", "quantity * unit_price"))
    .transform(T.filter("revenue > 0"))
    .transform(T.aggregate(
        group_by=["region", "product_category"],
        aggs={
            "total_revenue": "sum(revenue)",
            "order_count": "count(*)",
            "avg_order_value": "mean(revenue)"
        }
    ))
    .check(C.not_null(["region", "total_revenue"]))
    .check(C.row_count(min=1))
    .sink(sinks.file(
        path="s3://analytics-bucket/daily_sales/${RUN_DATE}/",
        format="parquet",
        partition_by=["region"]
    ))
)

result = pipeline.run(variables={"RUN_DATE": "2025-12-01"})
```

---

## 4. MVP Specification (v0.1)

### 4.1 Scope

**Timeline:** 5-6 weeks

**Goal:** Define a pipeline once, run locally with Polars/DuckDB, deploy to Airflow unchanged.

### 4.2 Required Features

#### 4.2.1 Engines

Since Ibis handles backend abstraction, all backends work with the same code:

| Engine | MVP Status | Notes |
|--------|------------|-------|
| Polars | ✅ Full | Default, fastest for local data |
| DuckDB | ✅ Full | SQL-native, great for analytics |
| pandas | ✅ Full | Legacy support via Ibis |
| Spark | ✅ Full | Databricks/EMR ready via Ibis |
| Snowflake | 🔶 v0.2 | Warehouse pushdown |
| BigQuery | 🔶 v0.2 | Warehouse pushdown |

**MVP simplification:** Because Ibis abstracts the backends, we get all local engines "for free" in v0.1. Warehouse backends (Snowflake, BigQuery) are v0.2 primarily for connection config and testing, not engine implementation.

#### 4.2.2 IO Operations

| Type | Read | Write |
|------|------|-------|
| File (local) | CSV, Parquet, JSON | Parquet |
| File (cloud) | S3, GCS, ADLS via fsspec | S3, GCS, ADLS |
| Database | PostgreSQL, MySQL, SQL Server | PostgreSQL |

#### 4.2.3 Transform Operations

| Operation | Description | Example |
|-----------|-------------|---------|
| `select` | Choose columns | `select: [id, name, amount]` |
| `rename` | Rename columns | `rename: {old_name: new_name}` |
| `filter` | Filter rows | `filter: amount > 100` |
| `derive_column` | Computed column | `derive_column: {name: tax, expr: amount * 0.1}` |
| `cast` | Type conversion | `cast: {id: string, amount: float64}` |
| `fill_null` | Replace nulls | `fill_null: {discount: 0}` |
| `dedup` | Remove duplicates | `dedup: [id]` or `dedup: ~` (all cols) |
| `sort` | Order rows | `sort: {by: [date], desc: true}` |
| `join` | Join DataFrames | `join: {right: other_df, on: [id], how: left}` |
| `aggregate` | Group + aggregate | `aggregate: {group_by: [region], aggs: {...}}` |
| `union` | Vertical concat | `union: [df1, df2]` |
| `limit` | Take N rows | `limit: 1000` |

#### 4.2.4 Data Quality Checks

| Check | Description | Config |
|-------|-------------|--------|
| `not_null` | Fail on nulls | `columns: [id, name]` |
| `unique` | Fail on duplicates | `columns: [id]` |
| `row_count` | Row count bounds | `min: 1, max: 1000000` |
| `accepted_values` | Value whitelist | `column: status, values: [a, b, c]` |
| `expression` | Custom predicate | `expr: amount >= 0` |

#### 4.2.5 CLI

```bash
etlx run pipeline.yml                      # Run pipeline
etlx run pipeline.yml --engine duckdb      # Override engine
etlx run pipeline.yml --var RUN_DATE=2025-12-01
etlx validate pipeline.yml                 # Validate config
etlx init my_project                       # Create project from template
etlx info pipeline.yml                     # Show pipeline info
etlx schema                                # Output JSON schema for IDE support
```

#### 4.2.6 Airflow Integration

```python
from airflow.decorators import task, dag
from etlx import Pipeline

@dag(schedule='@daily', start_date=datetime(2025, 1, 1))
def daily_sales():
    
    @task
    def run_pipeline(**context):
        return Pipeline.from_yaml(
            'pipelines/daily_sales.yml',
            variables={'RUN_DATE': context['ds']}
        ).run().to_dict()
    
    run_pipeline()

daily_sales()
```

### 4.3 Excluded from MVP

- Warehouse backends (Snowflake, BigQuery) — connection configs need testing (v0.2)
- Iceberg/Delta Lake table formats (v0.2)
- Warehouse-native SQL transforms with Jinja (v0.3)
- Schema contracts (v0.4)
- OpenLineage/OpenTelemetry (v0.5)

---

## 5. Release Roadmap

| Version | Timeline | Focus | Deliverables |
|---------|----------|-------|--------------|
| **v0.1** | 3-4 weeks | Core MVP | Ibis engine wrapper, local backends, IO, checks, CLI, Airflow |
| **v0.2** | 2-3 weeks | Warehouses + Lakehouse | Snowflake, BigQuery, Iceberg, Delta, partitioning |
| **v0.3** | 2-3 weeks | SQL Transforms | Warehouse-native SQL, Jinja templating |
| **v0.4** | 2 weeks | Contracts | Schema contracts, validation, doc generation |
| **v0.5** | 2-3 weeks | Observability | OpenLineage, OpenTelemetry, retry policies |
| **v1.0** | 1-2 weeks | Polish | Full docs, examples, stable API |

**Total:** 12-17 weeks (part-time) — significantly shorter due to Ibis handling engine abstraction

---

## 6. Project Structure

```
my_project/
├── pipelines/                 # Pipeline definitions
│   ├── daily_sales.yml
│   └── weekly_report.yml
├── contracts/                 # Schema contracts (v0.4+)
│   └── sales_schema.yml
├── sql/                       # SQL files for warehouse transforms (v0.3+)
│   └── transform_events.sql
├── dags/                      # Airflow DAGs
│   └── daily_sales_dag.py
├── tests/
│   ├── test_pipelines.py
│   └── conftest.py
├── .env.example               # Environment template
├── pyproject.toml
└── README.md
```

---

## 7. Development Workflow

### 7.1 Phase 1: API Design (1-2 days)

- [ ] Finalize YAML schema
- [ ] Define Python builder API
- [ ] Document Ibis wrapper interface
- [ ] Write spec document in repo

### 7.2 Phase 2: Core Implementation (3-4 weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Ibis engine wrapper + transform mapping |
| 2 | File IO (local + cloud via fsspec) + Database IO |
| 3 | Quality checks + structlog logging + CLI |
| 4 | Airflow integration + copier template + docs |

### 7.3 Testing Strategy

```python
import pytest
from hypothesis import given, strategies as st
from etlx import Pipeline

# Engine parity: Ibis guarantees this, but we verify
@pytest.mark.parametrize("engine", ["polars", "duckdb", "pandas"])
def test_transform_parity(engine, sample_data):
    pipeline = Pipeline.from_yaml('tests/fixtures/test_pipeline.yml')
    result = pipeline.run(engine=engine)
    
    assert result.row_count == 100
    assert set(result.columns) == {'id', 'name', 'revenue'}
    assert result.get_column('revenue').sum() == pytest.approx(50000.0)

# Property-based testing for edge cases
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_aggregation_consistency(values):
    """Verify sum aggregation matches across engines."""
    # Ibis should handle this, but hypothesis finds edge cases
    ...
```

### 7.4 Project Layout (src layout)

```
etlx/
├── src/
│   └── etlx/
│       ├── __init__.py
│       ├── pipeline.py        # Pipeline class
│       ├── engine.py          # Ibis wrapper
│       ├── config/
│       │   ├── __init__.py
│       │   ├── models.py      # Pydantic models
│       │   └── loader.py      # YAML loading
│       ├── transforms/
│       │   └── __init__.py    # Transform definitions
│       ├── checks/
│       │   └── __init__.py    # Quality checks
│       ├── io/
│       │   ├── __init__.py
│       │   ├── sources.py
│       │   └── sinks.py
│       └── cli/
│           └── __init__.py    # Typer CLI
├── tests/
│   ├── conftest.py
│   ├── test_pipeline.py
│   ├── test_transforms.py
│   └── fixtures/
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Appendix A: Expression Language

SQL-like syntax mapped to engine-native implementations:

| Expression | Description |
|------------|-------------|
| `quantity * unit_price` | Arithmetic |
| `status == 'active'` | Equality |
| `amount > 100 AND active = true` | Logical |
| `COALESCE(discount, 0)` | Null handling |
| `CASE WHEN x > 0 THEN 'pos' ELSE 'neg' END` | Conditional |
| `LOWER(name)` | String functions |
| `DATE_TRUNC('month', created_at)` | Date functions |
| `CAST(id AS string)` | Type casting |

---

## Appendix B: Environment Variables

| Variable | Description |
|----------|-------------|
| `ETLX_ENGINE` | Default engine |
| `ETLX_LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR |
| `ETLX_LOG_FORMAT` | json, console |
| `AWS_PROFILE` | AWS credentials profile |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account path |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure storage connection |

---

## Appendix C: Cloud Quick Start

### AWS
```bash
export AWS_PROFILE=my-profile
```
```yaml
source:
  type: file
  path: s3://bucket/data.parquet
```

### GCP
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
```
```yaml
source:
  type: file
  path: gs://bucket/data.parquet
```

### Azure
```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpoints..."
```
```yaml
source:
  type: file
  path: abfss://container@account.dfs.core.windows.net/data.parquet
```

---

*— End of Document —*