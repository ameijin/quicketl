# QuickETL Enhancement Backlog

This document tracks enhancement requests and future features for QuickETL.

## Priority Legend

- 🔴 **High**: Core functionality gap, blocking common use cases
- 🟡 **Medium**: Important for production workflows
- 🟢 **Low**: Nice to have, edge cases
- ✅ **Done**: Already implemented (discovered during review)

---

## Transform Enhancements

### ✅ Multi-Source Pipeline Support (Join/Union)

**Status**: IMPLEMENTED

**Implementation**:
- Added `sources: dict[str, SourceConfig]` to `PipelineConfig` for multi-source pipelines
- Updated `apply_transform` in `engines/base.py` to dispatch JoinTransform and UnionTransform
- Pipeline loads all named sources into a context dict for reference in transforms

**Example YAML**:
```yaml
name: orders_with_customers
engine: duckdb

sources:
  orders:
    type: file
    path: data/orders.parquet
  customers:
    type: file
    path: data/customers.parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]  # Note: "on" must be quoted in YAML (reserved word)
    how: left

sink:
  type: file
  path: output/enriched_orders.parquet
```

**Tests**: `tests/test_join_union.py`

---

### ✅ Variable Interpolation in YAML

**Status**: ALREADY IMPLEMENTED (discovered during review)

**Location**: `src/quicketl/config/loader.py`

The `substitute_variables()` function already handles:
- `${VAR_NAME}` - Environment variable lookup
- `${VAR_NAME:-default}` - With default value
- Explicit variables dict passed to `load_pipeline_config()`

**Usage**:
```bash
# CLI with variables
quicketl run pipeline.yml --var DATE=2025-01-01

# Workflow with variables
quicketl workflow run workflow.yml --var BRONZE_URI=s3://bucket/bronze
```

**YAML**:
```yaml
source:
  path: ${BRONZE_URI}/users.parquet  # Already works!
```

**Note**: Move to "Completed Items" section - this was already implemented but not documented well

---

### ✅ Enhanced Expression Parser

**Status**: IMPLEMENTED

**Supported functions** (derive_column expressions):
- `COALESCE(col1, col2, ...)` - Return first non-null value
- `NULLIF(col, value)` - Return null if equal
- `CONCAT(col1, col2, ...)` - String concatenation
- `UPPER(col)`, `LOWER(col)`, `TRIM(col)` - String functions
- `LENGTH(col)` - String length
- `ABS(col)`, `ROUND(col)` - Numeric functions

**Supported predicates** (filter expressions):
- `col IN ('a', 'b', 'c')` - IN operator
- `col NOT IN ('a', 'b')` - NOT IN operator
- `col IS NULL`, `col IS NOT NULL` - Null checks
- `col LIKE 'pattern%'` - Pattern matching

**Tests**: `tests/test_transforms.py`

---

### ✅ Aggregation Functions

**Status**: IMPLEMENTED

**Supported aggregations**:
- Basic: `sum`, `avg`/`mean`, `min`, `max`, `count`, `count(*)`
- Distinct: `count_distinct(column)`, `nunique(column)`
- Order: `first(column)`, `last(column)`
- Statistical: `stddev(column)`/`std(column)`, `variance(column)`/`var(column)`, `median(column)`
- Collection: `any(column)`/`arbitrary(column)`, `collect(column)`/`collect_list(column)`

**Example**:
```yaml
transforms:
  - op: aggregate
    group_by: [region]
    aggs:
      total: sum(amount)
      unique_users: count_distinct(user_id)
      amount_std: stddev(amount)
```

**Tests**: `tests/test_transforms.py`

---

## Sink Enhancements

### ✅ Database Sink Implementation

**Status**: IMPLEMENTED

**Supported modes**:
- `append` - Add rows to existing table
- `truncate` - Clear table then insert new data
- `replace` - Drop and recreate table

**Example**:
```yaml
sink:
  type: database
  connection: postgresql://localhost/warehouse
  table: gold.sales_summary
  mode: replace
```

**Cross-backend support**: Data is materialized to PyArrow for cross-backend compatibility (e.g., DuckDB pipeline writing to PostgreSQL).

**Tests**: `tests/test_database_sink.py`

---

### ✅ Partitioned File Writes

**Status**: IMPLEMENTED

**Supports**:
- Single column partitioning
- Multi-column nested partitioning
- Parquet and CSV formats

**Example**:
```yaml
sink:
  type: file
  path: s3://bucket/output/
  format: parquet
  partition_by: [date, region]
```

**Output structure**:
```
output/
├── 2025-01/
│   ├── North/
│   │   └── part-0.parquet
│   └── South/
│       └── part-0.parquet
└── 2025-02/
    └── ...
```

**Tests**: `tests/test_partitioned_writes.py`

---

## Source Enhancements

### 🟡 Iceberg Source Implementation

**Status**: Config defined, not implemented

**Problem**: `IcebergSource` is defined in models but not handled in `read_source`.

**Solution**: Add Iceberg support via pyiceberg or Spark.

**Files to modify**:
- `src/quicketl/engines/base.py` - Add Iceberg case to `read_source`

---

### 🟢 Delta Lake Support

**Status**: Not defined

**Problem**: Delta Lake is a popular lakehouse format not currently supported.

**Solution**: Add `DeltaSource` and `DeltaSink` configs.

---

## Quality Check Enhancements

### 🟢 Schema Validation Check

**Status**: Not implemented

**Problem**: No way to validate that output schema matches expected structure.

**Desired syntax**:
```yaml
checks:
  - type: schema
    columns:
      user_id: int64
      email: string
      balance: float64
```

---

### 🟢 Referential Integrity Check

**Status**: Not implemented

**Problem**: No way to validate foreign key relationships.

**Desired syntax**:
```yaml
checks:
  - type: foreign_key
    column: user_id
    reference:
      source: users
      column: user_id
```

---

## CLI/Workflow Enhancements

### 🟡 Workflow Variables

**Status**: Parsed but not used

**Problem**: `variables` in workflow YAML are parsed but not passed to pipelines.

**Solution**: Pass workflow variables to pipeline context for interpolation.

**Files to modify**:
- `src/quicketl/workflow/runner.py` - Pass variables to pipeline execution

---

### ✅ Parallel Pipeline Execution

**Status**: ALREADY IMPLEMENTED (discovered during review)

**Location**: `src/quicketl/workflow/workflow.py`

Parallel execution is already implemented using `concurrent.futures.ThreadPoolExecutor`. Workflows with `parallel: true` will execute pipelines concurrently.

**Example**:
```yaml
stages:
  - name: silver_processing
    parallel: true  # Pipelines run in parallel
    pipelines:
      - path: pipelines/silver/clean_users.yml
      - path: pipelines/silver/clean_events.yml
      - path: pipelines/silver/clean_payments.yml
```

---

## Infrastructure

### 🟡 Secrets Management Integration

**Status**: Not implemented

**Problem**: Connection strings with credentials shouldn't be stored in YAML or env vars.

**Solution**: Support secrets managers:
- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager
- HashiCorp Vault

**Desired syntax**:
```yaml
source:
  type: database
  connection: secret://aws/my-db-credentials
```

---

### 🟢 Data Lineage Tracking

**Status**: Not implemented

**Problem**: No way to track data provenance through the pipeline.

**Solution**: Capture and store lineage metadata:
- Source files/tables read
- Transforms applied
- Row counts at each step
- Output location

---

### 🟢 Metrics/Observability

**Status**: Basic logging only

**Problem**: No structured metrics for monitoring pipeline performance.

**Solution**: Add optional metrics export to:
- Prometheus
- OpenTelemetry
- Datadog/New Relic

---

## Documentation

### 🟢 JSON Schema Generation

**Status**: Basic implementation exists

**Enhancement**: Generate complete JSON Schema for IDE autocomplete and validation.

**Command**: `quicketl schema pipeline > pipeline.schema.json`

---

## Contributing

To contribute to these enhancements:

1. Pick an item from this backlog
2. Create a branch: `feature/enhancement-name`
3. Implement with tests
4. Update this document to mark as completed
5. Submit PR

For questions or discussion, open an issue referencing the specific enhancement.
