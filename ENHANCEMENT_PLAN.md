# QuickETL Testing & Data Quality Enhancement Plan

## Summary
Enhance QuickETL with robust testing and modern data quality/contracts following 2026 data engineering best practices. Implementation in parallel tracks: testing infrastructure + data quality features.

---

## Progress Tracker

### Completed
- [x] **pyproject.toml** - Added new dependencies: `pytest-benchmark>=4.0`, `moto>=5.0`, `responses>=0.25`, `pandera[polars]>=0.20`, `quality` bundle
- [x] **pytest markers** - Added `benchmark` marker
- [x] **Logging tests** - Created `tests/unit/logging/test_logging_setup.py` with comprehensive tests
- [x] **Airflow tests** - Created `tests/unit/integrations/test_airflow.py` with full coverage
- [x] **Contracts module** - Created `src/quicketl/quality/contracts/` with:
  - `__init__.py` - Module exports
  - `pandera_adapter.py` - PanderaContractValidator with check parsing
  - `schema.py` - DataContract and ColumnContract Pydantic models
  - `registry.py` - File-based ContractRegistry
- [x] **ContractCheck config** - Added ContractCheck to `src/quicketl/config/checks.py`
- [x] **Check runner** - Extended `src/quicketl/quality/checks.py` with `run_contract_check()`

### In Progress
- [ ] Secrets provider tests (AWS and Azure)

### Not Started
- [ ] Database writer tests
- [ ] dbt staging sink implementation
- [ ] Data profiling module
- [ ] Profile CLI command
- [ ] Concurrency tests
- [ ] S3 I/O tests
- [ ] Performance benchmarks
- [ ] Run full test suite

---

---

## Track 1: Testing Infrastructure Enhancement

### 1.1 Logging Module Tests (NEW)
**File to create:** `tests/unit/logging/test_logging_setup.py`

Tests for `src/quicketl/logging/setup.py`:
- `configure_logging()` - test "json", "console", "auto" format modes
- Log level configuration (DEBUG, INFO, WARNING, ERROR)
- TTY vs non-TTY auto-detection (mock `sys.stderr.isatty()`)
- `get_logger()` name binding and structured output

### 1.2 Airflow Integration Tests (NEW)
**File to create:** `tests/unit/integrations/test_airflow.py`

Tests for `src/quicketl/integrations/airflow.py`:
- `@quicketl_task` decorator with config_path
- `@quicketl_task` decorator with Pipeline object return
- Error handling when pipeline fails (RuntimeError)
- XCom return dict format verification
- `run_pipeline_task()` variable substitution
- `fail_on_check_failure` parameter behavior

**Mocking:** Mock `Pipeline.from_yaml()` and `Pipeline.run()` with pytest-mock

### 1.3 Secrets Provider Tests (NEW)
**Files to create:**
- `tests/unit/secrets/test_aws_secrets.py`
- `tests/unit/secrets/test_azure_secrets.py`

Tests for `src/quicketl/secrets/aws.py`:
- Initialization with region and profile
- `get_secret()` plain string response
- `get_secret()` JSON response with key extraction
- Missing secret with default fallback
- Missing secret without default (KeyError)
- ImportError when boto3 not installed (mock `HAS_BOTO3`)

Tests for `src/quicketl/secrets/azure.py`:
- Same patterns as AWS
- Mock Azure SDK with unittest.mock

**Add dependency:** `moto>=5.0` for AWS mocking

### 1.4 Database Writer Tests (ENHANCE)
**File to create:** `tests/unit/io/test_database_writer.py`

Tests for `src/quicketl/io/writers/database.py`:
- Write modes: append, truncate, replace
- Auto-create table for non-existent target
- Schema mismatch handling
- `rows_written` and `duration_ms` result verification

**Use DuckDB in-memory** for fast, isolated tests

### 1.5 Cloud Storage I/O Tests (NEW)
**Files to create:**
- `tests/integration/io/test_s3_io.py`
- `tests/integration/io/test_gcs_io.py`
- `tests/integration/io/test_azure_io.py`

Tests (using moto for S3, mocks for GCS/Azure):
- Read parquet/csv/json from cloud paths
- Write parquet/csv to cloud paths
- Partitioned writes to cloud storage
- Cloud path parsing and validation

**Mark as:** `@pytest.mark.integration` with skip if cloud packages not installed

### 1.6 Concurrency Tests (NEW)
**File to create:** `tests/unit/pipeline/test_concurrent_execution.py`

Tests for parallel execution:
- Multiple pipelines running in parallel (thread safety)
- Shared engine isolation between parallel runs
- Workflow parallel stage execution

### 1.7 Performance Benchmarks (NEW)
**File to create:** `tests/benchmark/test_pipeline_performance.py`

**Add dependency:** `pytest-benchmark>=4.0`

Benchmarks:
- Transform chain execution (filter -> derive -> aggregate)
- File read/write performance
- Large dataset handling (100K+ rows)

**Mark as:** `@pytest.mark.slow` and `@pytest.mark.benchmark`

### 1.8 pyproject.toml Test Dependencies Update
```toml
[project.optional-dependencies]
dev = [
    # ... existing ...
    "pytest-benchmark>=4.0",  # NEW
    "moto>=5.0",              # NEW - AWS mocking
    "responses>=0.25",        # NEW - HTTP mocking
]
```

---

## Track 2: Data Quality & Contracts (Pandera)

### 2.1 New Module Structure
```
src/quicketl/quality/
    __init__.py              # existing
    checks.py                # existing - extend CheckConfig union
    runner.py                # existing - extend for contract checks
    contracts/               # NEW
        __init__.py
        pandera_adapter.py   # Pandera schema validation
        schema.py            # DataContract model definitions
        registry.py          # File-based contract registry
```

### 2.2 Pandera Adapter
**File to create:** `src/quicketl/quality/contracts/pandera_adapter.py`

```python
"""Pandera adapter for QuickETL data contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

try:
    import pandera as pa
    from pandera.polars import DataFrameSchema
    HAS_PANDERA = True
except ImportError:
    HAS_PANDERA = False
    pa = None
    DataFrameSchema = None

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class ContractResult:
    """Result of contract validation."""
    passed: bool
    errors: list[dict[str, Any]] | None = None
    validated_rows: int = 0


class PanderaContractValidator:
    """Validate Ibis tables against Pandera schemas."""

    def __init__(self, schema_config: dict[str, Any]):
        if not HAS_PANDERA:
            raise ImportError(
                "pandera is required for contract validation. "
                "Install with: pip install quicketl[contracts]"
            )
        self.schema = self._build_schema(schema_config)

    def _build_schema(self, config: dict[str, Any]) -> DataFrameSchema:
        """Build Pandera schema from config dict."""
        columns = {}
        for col_name, col_config in config.get("columns", {}).items():
            dtype = col_config.get("dtype", "str")
            nullable = col_config.get("nullable", True)
            unique = col_config.get("unique", False)
            checks = self._parse_checks(col_config.get("checks", []))

            columns[col_name] = pa.Column(
                dtype=dtype,
                nullable=nullable,
                unique=unique,
                checks=checks,
            )

        return DataFrameSchema(
            columns=columns,
            strict=config.get("strict", False),
        )

    def _parse_checks(self, check_strs: list[str]) -> list[pa.Check]:
        """Parse check strings like 'ge(0)' into Pandera checks."""
        checks = []
        for check_str in check_strs:
            if check_str.startswith("ge("):
                val = float(check_str[3:-1])
                checks.append(pa.Check.ge(val))
            elif check_str.startswith("le("):
                val = float(check_str[3:-1])
                checks.append(pa.Check.le(val))
            elif check_str.startswith("gt("):
                val = float(check_str[3:-1])
                checks.append(pa.Check.gt(val))
            elif check_str.startswith("lt("):
                val = float(check_str[3:-1])
                checks.append(pa.Check.lt(val))
            elif check_str.startswith("str_matches("):
                pattern = check_str[12:-2]  # Remove str_matches(' and ')
                checks.append(pa.Check.str_matches(pattern))
            elif check_str.startswith("isin("):
                values = eval(check_str[5:-1])  # Parse list
                checks.append(pa.Check.isin(values))
        return checks

    def validate(self, table: ir.Table) -> ContractResult:
        """Validate Ibis table against schema."""
        # Convert to Polars for Pandera validation
        df = table.to_polars()

        try:
            self.schema.validate(df, lazy=True)
            return ContractResult(
                passed=True,
                validated_rows=len(df),
            )
        except pa.errors.SchemaErrors as e:
            return ContractResult(
                passed=False,
                errors=e.failure_cases.to_dicts() if hasattr(e, 'failure_cases') else [{"error": str(e)}],
                validated_rows=len(df),
            )
```

### 2.3 Configuration Model Extension
**File to modify:** `src/quicketl/config/checks.py`

Add new check type:
```python
class ContractCheck(BaseModel):
    """Data contract validation using Pandera schema.

    Example YAML:
        - type: contract
          schema:
            columns:
              id: {dtype: int64, nullable: false, unique: true}
              email: {dtype: str, checks: ["str_matches('^[^@]+@[^@]+$')"]}
              amount: {dtype: float64, checks: ["ge(0)"]}
            strict: false
    """

    type: Literal["contract"] = "contract"
    schema: dict[str, Any] = Field(
        ...,
        description="Pandera schema definition with columns and checks",
    )
    strict: bool = Field(
        default=False,
        description="If true, reject columns not in schema",
    )


# Update discriminated union
CheckConfig = Annotated[
    NotNullCheck | UniqueCheck | RowCountCheck | AcceptedValuesCheck | ExpressionCheck | ContractCheck,
    Field(discriminator="type"),
]
```

### 2.4 Data Contract Schema Definition
**File to create:** `src/quicketl/quality/contracts/schema.py`

```python
"""Data contract schema definitions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColumnContract(BaseModel):
    """Contract specification for a single column."""

    name: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Expected data type (int64, float64, str, bool, datetime)")
    nullable: bool = Field(default=True, description="Whether nulls are allowed")
    unique: bool = Field(default=False, description="Whether values must be unique")
    checks: list[str] = Field(
        default_factory=list,
        description="Validation checks (e.g., 'ge(0)', 'le(100)', 'str_matches(...)')",
    )
    description: str = Field(default="", description="Column documentation")


class DataContract(BaseModel):
    """Complete data contract definition.

    Example YAML file (contracts/orders_v1.yml):
        name: orders
        version: "1.0.0"
        owner: data-team
        description: Order transaction data
        columns:
          - name: order_id
            dtype: int64
            nullable: false
            unique: true
          - name: amount
            dtype: float64
            checks: ["ge(0)"]
          - name: status
            dtype: str
            checks: ["isin(['pending', 'completed', 'cancelled'])"]
    """

    name: str = Field(..., description="Contract name")
    version: str = Field(default="1.0.0", description="Semantic version")
    owner: str = Field(default="", description="Team or person responsible")
    description: str = Field(default="", description="Contract documentation")
    columns: list[ColumnContract] = Field(..., description="Column specifications")
    strict: bool = Field(default=False, description="Reject unlisted columns")

    def to_pandera_config(self) -> dict:
        """Convert to Pandera-compatible configuration dict."""
        columns = {}
        for col in self.columns:
            columns[col.name] = {
                "dtype": col.dtype,
                "nullable": col.nullable,
                "unique": col.unique,
                "checks": col.checks,
            }
        return {
            "columns": columns,
            "strict": self.strict,
        }
```

### 2.5 Contract Registry (Lightweight, File-based)
**File to create:** `src/quicketl/quality/contracts/registry.py`

```python
"""File-based contract registry."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from quicketl.quality.contracts.schema import DataContract

if TYPE_CHECKING:
    pass


class ContractRegistry:
    """Load and manage data contracts from YAML files.

    Directory structure:
        contracts/
            orders_v1.yml
            customers_v2.yml
            products.yml

    Usage:
        registry = ContractRegistry(Path("./contracts"))
        contract = registry.get_contract("orders")
        # Returns latest version, or specify: registry.get_contract("orders", "1.0.0")
    """

    def __init__(self, contracts_dir: Path):
        self.contracts_dir = Path(contracts_dir)
        if not self.contracts_dir.exists():
            raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")

    def list_contracts(self) -> list[str]:
        """List all available contract names."""
        contracts = []
        for file in self.contracts_dir.glob("*.yml"):
            contracts.append(file.stem)
        for file in self.contracts_dir.glob("*.yaml"):
            contracts.append(file.stem)
        return sorted(set(contracts))

    def get_contract(self, name: str, version: str | None = None) -> DataContract:
        """Load contract by name.

        Args:
            name: Contract name (filename without extension)
            version: Optional version filter (not yet implemented)

        Returns:
            DataContract object
        """
        # Try .yml first, then .yaml
        for ext in [".yml", ".yaml"]:
            path = self.contracts_dir / f"{name}{ext}"
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f)
                return DataContract(**data)

        raise FileNotFoundError(f"Contract not found: {name}")

    def validate_all(self) -> dict[str, bool]:
        """Validate all contract files are parseable."""
        results = {}
        for name in self.list_contracts():
            try:
                self.get_contract(name)
                results[name] = True
            except Exception:
                results[name] = False
        return results
```

### 2.6 Check Runner Extension
**File to modify:** `src/quicketl/quality/checks.py`

Add contract check runner:
```python
from quicketl.config.checks import ContractCheck
from quicketl.quality.contracts.pandera_adapter import PanderaContractValidator


def run_contract_check(table: ir.Table, config: ContractCheck) -> CheckResult:
    """Run Pandera contract validation.

    Args:
        table: Ibis Table expression
        config: ContractCheck configuration

    Returns:
        CheckResult with validation details
    """
    try:
        validator = PanderaContractValidator(config.schema)
        result = validator.validate(table)

        if result.passed:
            return CheckResult(
                check_type="contract",
                passed=True,
                message=f"Contract validation passed for {result.validated_rows} rows",
                details={"validated_rows": result.validated_rows},
            )
        else:
            return CheckResult(
                check_type="contract",
                passed=False,
                message=f"Contract validation failed",
                details={
                    "validated_rows": result.validated_rows,
                    "errors": result.errors,
                },
            )
    except ImportError as e:
        return CheckResult(
            check_type="contract",
            passed=False,
            message=str(e),
            details={"error": "pandera_not_installed"},
        )
    except Exception as e:
        return CheckResult(
            check_type="contract",
            passed=False,
            message=f"Contract validation error: {e}",
            details={"error": str(e)},
        )


# Update run_check() match statement to include:
#     case ContractCheck():
#         return run_contract_check(table, config)
```

### 2.7 Example YAML Usage
```yaml
# Pipeline with contract validation
name: orders_pipeline
engine: duckdb

source:
  type: file
  path: s3://bucket/orders.parquet

transforms:
  - op: filter
    predicate: amount > 0

checks:
  # Built-in checks
  - type: not_null
    columns: [order_id, customer_id]
  - type: row_count
    min: 1

  # Pandera contract check
  - type: contract
    schema:
      columns:
        order_id: {dtype: int64, nullable: false, unique: true}
        customer_id: {dtype: int64, nullable: false}
        amount: {dtype: float64, checks: ["ge(0)"]}
        status: {dtype: str, checks: ["isin(['pending', 'completed', 'cancelled'])"]}
      strict: false

sink:
  type: file
  path: s3://bucket/validated_orders/
  format: parquet
```

### 2.8 pyproject.toml Contracts Dependency
```toml
[project.optional-dependencies]
# Data contracts
contracts = ["pandera[polars]>=0.20"]

# Quality bundle (contracts + profiling)
quality = ["quicketl[contracts]"]
```

---

## Track 3: dbt Integration (as Sink)

### 3.1 Design Philosophy
QuickETL writes to **staging tables** that dbt then transforms. This enables:
- QuickETL for Python-based ingestion and transforms
- dbt for SQL-based analytics transformations
- Clear separation of concerns

### 3.2 dbt Staging Sink
**File to create:** `src/quicketl/integrations/dbt.py`

```python
"""dbt integration - staging sink for dbt consumption."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis.expr.types as ir

from pydantic import BaseModel, Field


class DbtStagingSinkConfig(BaseModel):
    """Configuration for dbt-compatible staging output.

    Example YAML:
        sink:
          type: dbt_staging
          connection: postgresql://user:pass@host/db
          schema: staging
          table: stg_orders
          include_metadata: true
    """

    type: str = "dbt_staging"
    connection: str = Field(..., description="Database connection string")
    schema: str = Field(default="staging", description="Target schema name")
    table: str = Field(..., description="Target table name (recommend stg_ prefix)")
    include_metadata: bool = Field(
        default=True,
        description="Add _loaded_at and _source_file metadata columns",
    )
    write_mode: str = Field(
        default="replace",
        description="Write mode: append, replace, truncate",
    )


@dataclass
class DbtStagingWriteResult:
    """Result of writing to dbt staging."""

    rows_written: int
    table: str
    schema: str
    duration_ms: float
    metadata_columns: list[str]


class DbtStagingWriter:
    """Write to staging tables with dbt conventions.

    Adds metadata columns:
    - _loaded_at: Timestamp when data was loaded
    - _source_file: Source file path (if available)
    """

    def __init__(self, config: DbtStagingSinkConfig):
        self.config = config

    def write(
        self,
        table: ir.Table,
        source_path: str | None = None,
    ) -> DbtStagingWriteResult:
        """Write table to staging with metadata."""
        import time
        import ibis

        start = time.perf_counter()

        # Add metadata columns if configured
        if self.config.include_metadata:
            now = datetime.now(timezone.utc)
            table = table.mutate(
                _loaded_at=ibis.literal(now),
                _source_file=ibis.literal(source_path or "unknown"),
            )
            metadata_columns = ["_loaded_at", "_source_file"]
        else:
            metadata_columns = []

        # Connect to database and write
        con = ibis.connect(self.config.connection)

        full_table_name = f"{self.config.schema}.{self.config.table}"

        if self.config.write_mode == "replace":
            con.create_table(
                full_table_name,
                table.to_pyarrow(),
                overwrite=True,
            )
        elif self.config.write_mode == "append":
            con.insert(full_table_name, table.to_pyarrow())
        elif self.config.write_mode == "truncate":
            con.truncate_table(full_table_name)
            con.insert(full_table_name, table.to_pyarrow())

        rows = table.count().execute()
        duration = (time.perf_counter() - start) * 1000

        return DbtStagingWriteResult(
            rows_written=rows,
            table=self.config.table,
            schema=self.config.schema,
            duration_ms=duration,
            metadata_columns=metadata_columns,
        )


def generate_dbt_source_yaml(
    tables: list[str],
    schema: str = "staging",
    source_name: str = "quicketl_staging",
) -> str:
    """Generate dbt sources.yml for QuickETL staging tables.

    Args:
        tables: List of staging table names
        schema: Schema name
        source_name: dbt source name

    Returns:
        YAML string for dbt sources.yml
    """
    import yaml

    source_config = {
        "version": 2,
        "sources": [
            {
                "name": source_name,
                "schema": schema,
                "description": "Staging tables loaded by QuickETL",
                "tables": [
                    {
                        "name": table,
                        "loaded_at_field": "_loaded_at",
                        "freshness": {
                            "warn_after": {"count": 24, "period": "hour"},
                            "error_after": {"count": 48, "period": "hour"},
                        },
                    }
                    for table in tables
                ],
            }
        ],
    }

    return yaml.dump(source_config, default_flow_style=False, sort_keys=False)
```

### 3.3 Sink Configuration Extension
**File to modify:** `src/quicketl/config/models.py`

```python
class DbtStagingSink(BaseModel):
    """dbt staging table sink.

    Example YAML:
        sink:
          type: dbt_staging
          connection: ${DB_CONNECTION}
          schema: staging
          table: stg_orders
          include_metadata: true
    """

    type: Literal["dbt_staging"] = "dbt_staging"
    connection: str = Field(..., description="Database connection string")
    schema: str = Field(default="staging", description="Target schema")
    table: str = Field(..., description="Target table name")
    include_metadata: bool = Field(default=True, description="Add metadata columns")
    write_mode: Literal["append", "replace", "truncate"] = Field(
        default="replace",
        description="Write mode",
    )


# Update SinkConfig union to include DbtStagingSink
```

### 3.4 Example Usage
```yaml
# Pipeline that loads data for dbt
name: load_orders_for_dbt
engine: duckdb

source:
  type: file
  path: s3://data-lake/raw/orders/*.parquet

transforms:
  - op: filter
    predicate: order_date >= '2024-01-01'
  - op: select
    columns: [order_id, customer_id, product_id, quantity, amount, order_date]
  - op: derive_column
    name: order_month
    expr: "date_trunc('month', order_date)"

checks:
  - type: not_null
    columns: [order_id, customer_id]
  - type: unique
    columns: [order_id]

sink:
  type: dbt_staging
  connection: ${WAREHOUSE_CONNECTION}
  schema: staging
  table: stg_orders
  include_metadata: true
  write_mode: replace
```

dbt can then reference:
```sql
-- models/marts/orders.sql
SELECT
    order_id,
    customer_id,
    amount,
    order_month,
    _loaded_at
FROM {{ source('quicketl_staging', 'stg_orders') }}
WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
```

---

## Track 4: Data Profiling (Lightweight)

### 4.1 Profiler Module
**File to create:** `src/quicketl/quality/profiling.py`

```python
"""Data profiling for QuickETL pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class ColumnProfile:
    """Profile statistics for a single column."""

    name: str
    dtype: str
    total_count: int
    null_count: int
    null_percentage: float
    distinct_count: int
    distinct_percentage: float
    min_value: Any | None = None
    max_value: Any | None = None
    mean: float | None = None
    std: float | None = None
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class TableProfile:
    """Profile for an entire table."""

    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    profile_duration_ms: float


class DataProfiler:
    """Generate data profiles using Ibis expressions.

    Usage:
        profiler = DataProfiler()
        profile = profiler.profile_table(table)
        print(profile.row_count)
        for col in profile.columns:
            print(f"{col.name}: {col.null_percentage:.1%} nulls")
    """

    def __init__(self, sample_size: int = 5):
        self.sample_size = sample_size

    def profile_table(self, table: ir.Table) -> TableProfile:
        """Generate comprehensive table profile."""
        import time

        start = time.perf_counter()

        row_count = table.count().execute()
        columns = []

        for col_name in table.columns:
            col_profile = self._profile_column(table, col_name, row_count)
            columns.append(col_profile)

        duration = (time.perf_counter() - start) * 1000

        return TableProfile(
            row_count=row_count,
            column_count=len(table.columns),
            columns=columns,
            profile_duration_ms=duration,
        )

    def _profile_column(
        self,
        table: ir.Table,
        col_name: str,
        total_rows: int,
    ) -> ColumnProfile:
        """Profile single column using Ibis aggregations."""
        col = table[col_name]
        dtype = str(col.type())

        # Basic stats in single query
        stats = table.aggregate([
            col.isnull().sum().name("null_count"),
            col.nunique().name("distinct_count"),
        ]).execute()

        null_count = int(stats["null_count"].iloc[0])
        distinct_count = int(stats["distinct_count"].iloc[0])

        profile = ColumnProfile(
            name=col_name,
            dtype=dtype,
            total_count=total_rows,
            null_count=null_count,
            null_percentage=null_count / total_rows if total_rows > 0 else 0,
            distinct_count=distinct_count,
            distinct_percentage=distinct_count / total_rows if total_rows > 0 else 0,
        )

        # Numeric stats
        if self._is_numeric(dtype):
            numeric_stats = table.aggregate([
                col.min().name("min_val"),
                col.max().name("max_val"),
                col.mean().name("mean_val"),
                col.std().name("std_val"),
            ]).execute()

            profile.min_value = numeric_stats["min_val"].iloc[0]
            profile.max_value = numeric_stats["max_val"].iloc[0]
            profile.mean = float(numeric_stats["mean_val"].iloc[0]) if numeric_stats["mean_val"].iloc[0] is not None else None
            profile.std = float(numeric_stats["std_val"].iloc[0]) if numeric_stats["std_val"].iloc[0] is not None else None

        # Sample values
        samples = (
            table.select(col_name)
            .filter(col.notnull())
            .distinct()
            .limit(self.sample_size)
            .execute()
        )
        profile.sample_values = samples[col_name].tolist()

        return profile

    def _is_numeric(self, dtype: str) -> bool:
        """Check if dtype is numeric."""
        numeric_types = ["int", "float", "decimal", "double"]
        return any(t in dtype.lower() for t in numeric_types)

    def to_dict(self, profile: TableProfile) -> dict:
        """Convert profile to dictionary for JSON/YAML output."""
        return {
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "profile_duration_ms": profile.profile_duration_ms,
            "columns": [
                {
                    "name": col.name,
                    "dtype": col.dtype,
                    "null_count": col.null_count,
                    "null_percentage": f"{col.null_percentage:.2%}",
                    "distinct_count": col.distinct_count,
                    "min": col.min_value,
                    "max": col.max_value,
                    "mean": round(col.mean, 4) if col.mean else None,
                    "std": round(col.std, 4) if col.std else None,
                    "samples": col.sample_values,
                }
                for col in profile.columns
            ],
        }
```

### 4.2 CLI Command
**File to modify:** `src/quicketl/cli/main.py`

```python
@app.command()
def profile(
    path: str = typer.Argument(..., help="Path to file or table to profile"),
    format: str = typer.Option("table", help="Output format: table, json, yaml"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save to file"),
):
    """Profile data to understand structure and quality.

    Examples:
        quicketl profile data.parquet
        quicketl profile s3://bucket/data.csv --format json
        quicketl profile data.parquet -o profile.json
    """
    from quicketl.quality.profiling import DataProfiler
    from quicketl.engines.base import ETLXEngine

    engine = ETLXEngine(backend="duckdb")
    table = engine.read_file(path)

    profiler = DataProfiler()
    profile = profiler.profile_table(table)

    if format == "json":
        import json
        output_str = json.dumps(profiler.to_dict(profile), indent=2)
    elif format == "yaml":
        import yaml
        output_str = yaml.dump(profiler.to_dict(profile), default_flow_style=False)
    else:
        # Rich table output
        from rich.table import Table
        from rich.console import Console

        console = Console()
        rich_table = Table(title=f"Profile: {path}")
        rich_table.add_column("Column")
        rich_table.add_column("Type")
        rich_table.add_column("Nulls %")
        rich_table.add_column("Distinct")
        rich_table.add_column("Min")
        rich_table.add_column("Max")

        for col in profile.columns:
            rich_table.add_row(
                col.name,
                col.dtype,
                f"{col.null_percentage:.1%}",
                str(col.distinct_count),
                str(col.min_value) if col.min_value is not None else "-",
                str(col.max_value) if col.max_value is not None else "-",
            )

        console.print(rich_table)
        console.print(f"\nRows: {profile.row_count:,} | Columns: {profile.column_count}")
        return

    if output:
        output.write_text(output_str)
        typer.echo(f"Profile saved to {output}")
    else:
        typer.echo(output_str)
```

---

## Critical Files Summary

### New Files to Create
| File | Purpose |
|------|---------|
| `tests/unit/logging/test_logging_setup.py` | Logging module tests |
| `tests/unit/integrations/test_airflow.py` | Airflow integration tests |
| `tests/unit/secrets/test_aws_secrets.py` | AWS secrets tests |
| `tests/unit/secrets/test_azure_secrets.py` | Azure secrets tests |
| `tests/unit/io/test_database_writer.py` | Database writer tests |
| `tests/integration/io/test_s3_io.py` | S3 I/O tests |
| `tests/unit/pipeline/test_concurrent_execution.py` | Concurrency tests |
| `tests/benchmark/test_pipeline_performance.py` | Performance benchmarks |
| `src/quicketl/quality/contracts/__init__.py` | Contracts module init |
| `src/quicketl/quality/contracts/pandera_adapter.py` | Pandera integration |
| `src/quicketl/quality/contracts/schema.py` | DataContract models |
| `src/quicketl/quality/contracts/registry.py` | Contract registry |
| `src/quicketl/integrations/dbt.py` | dbt staging sink |
| `src/quicketl/quality/profiling.py` | Data profiling |

### Files to Modify
| File | Changes |
|------|---------|
| `src/quicketl/config/checks.py` | Add ContractCheck model to union |
| `src/quicketl/quality/checks.py` | Add run_contract_check() function |
| `src/quicketl/quality/runner.py` | Handle ContractCheck in run_check() |
| `src/quicketl/config/models.py` | Add DbtStagingSink to sink union |
| `src/quicketl/cli/main.py` | Add profile command |
| `pyproject.toml` | Add new optional dependencies |

---

## Implementation Order (Parallel Tracks)

### Week 1-2: Foundation ✅ COMPLETED
**Testing Track:**
- [x] Logging module tests
- [x] Airflow integration tests
- [x] Update pyproject.toml with test deps (moto, pytest-benchmark)

**Quality Track:**
- [x] Create contracts module structure
- [x] Implement Pandera adapter
- [x] Add ContractCheck configuration

### Week 3-4: Core Features (NEXT)
**Testing Track:**
- [ ] Secrets provider tests (AWS, Azure)
- [ ] Database writer tests
- [ ] Concurrency tests

**Quality Track:**
- [x] DataContract schema models
- [x] Contract registry implementation
- [x] Extend check runner for contracts

### Week 5-6: Integration & Polish
**Testing Track:**
- [ ] Cloud storage I/O tests (S3, GCS, Azure)
- [ ] Performance benchmarks
- [ ] Ensure >90% coverage

**Quality Track:**
- [ ] dbt staging sink implementation
- [ ] Data profiling module
- [ ] CLI profile command

### Week 7: Documentation & CI
- [ ] Update docs for contracts
- [ ] Update docs for dbt integration
- [ ] Add contract validation to CI
- [ ] Update CHANGELOG

---

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data quality framework | Pandera | Lightweight, Pythonic, native Polars support, fits Ibis |
| dbt integration | As sink | Write staging tables for dbt consumption, clear separation |
| Anomaly detection | Skip | Existing expression checks sufficient, keep scope minimal |
| Contract registry | File-based | Pragmatic, git-versioned, upgrade path to schema registry |
| Implementation order | Parallel | Testing + quality features simultaneously |

---

## Success Criteria
- [ ] All testing gaps filled with >90% code coverage
- [x] Pandera contract checks work in pipelines (ContractCheck implemented)
- [ ] dbt staging sink writes with metadata columns
- [ ] Data profiling available via CLI
- [ ] All new features have comprehensive tests
- [ ] Documentation updated for all new features

---

## Files Created/Modified (for reference)

### New Files Created:
```
tests/unit/logging/__init__.py
tests/unit/logging/test_logging_setup.py
tests/unit/integrations/__init__.py
tests/unit/integrations/test_airflow.py
src/quicketl/quality/contracts/__init__.py
src/quicketl/quality/contracts/pandera_adapter.py
src/quicketl/quality/contracts/schema.py
src/quicketl/quality/contracts/registry.py
```

### Files Modified:
```
pyproject.toml                      # Added deps: pytest-benchmark, moto, responses, pandera[polars], quality bundle
src/quicketl/config/checks.py       # Added ContractCheck model
src/quicketl/quality/checks.py      # Added run_contract_check(), updated imports
```

### Next Steps:
1. Run `uv sync` or `pip install -e ".[dev,contracts]"` to install new dependencies
2. Run `pytest tests/unit/logging/ tests/unit/integrations/` to verify new tests pass
3. Continue with secrets provider tests (AWS/Azure)
4. Implement dbt staging sink
5. Add data profiling module
