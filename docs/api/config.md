# Configuration Models

QuickETL uses Pydantic models for type-safe pipeline configuration. These models provide validation, IDE autocomplete, and documentation.

## Import

```python
from quicketl.config import (
    PipelineConfig,
    FileSource,
    DatabaseSource,
    FileSink,
    DatabaseSink,
    # Transforms
    SelectTransform,
    FilterTransform,
    DeriveColumnTransform,
    AggregateTransform,
    JoinTransform,
    # ... and more
)
```

## PipelineConfig

The root configuration model for a complete pipeline.

```python
from quicketl.config import PipelineConfig

class PipelineConfig(BaseModel):
    name: str
    description: str | None = None
    engine: str = "duckdb"
    source: SourceConfig
    transforms: list[TransformConfig] = []
    checks: list[CheckConfig] = []
    sink: SinkConfig
```

### Example

```python
from quicketl.config import (
    PipelineConfig,
    FileSource,
    FileSink,
    FilterTransform,
    SelectTransform
)

config = PipelineConfig(
    name="sales_etl",
    description="Process daily sales data",
    engine="duckdb",
    source=FileSource(
        type="file",
        path="data/sales.csv",
        format="csv"
    ),
    transforms=[
        FilterTransform(op="filter", predicate="amount > 0"),
        SelectTransform(op="select", columns=["id", "name", "amount"])
    ],
    sink=FileSink(
        type="file",
        path="output/results.parquet",
        format="parquet"
    )
)
```

## Source Models

### FileSource

Read from local or cloud files.

```python
class FileSource(BaseModel):
    type: Literal["file"]
    path: str
    format: Literal["csv", "parquet", "json", "excel"]
    options: dict | None = None
```

**Example:**

```python
source = FileSource(
    type="file",
    path="data/*.parquet",
    format="parquet"
)

# With options
source = FileSource(
    type="file",
    path="data/input.csv",
    format="csv",
    options={
        "delimiter": ";",
        "encoding": "utf-8",
        "has_header": True
    }
)
```

### DatabaseSource

Read from databases.

```python
class DatabaseSource(BaseModel):
    type: Literal["database"]
    connection: str
    table: str | None = None
    query: str | None = None
```

**Example:**

```python
# From table
source = DatabaseSource(
    type="database",
    connection="postgres",
    table="public.orders"
)

# From query
source = DatabaseSource(
    type="database",
    connection="postgres",
    query="""
        SELECT * FROM orders
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
    """
)
```

## Sink Models

### FileSink

Write to files.

```python
class FileSink(BaseModel):
    type: Literal["file"]
    path: str
    format: Literal["csv", "parquet", "json"]
    mode: Literal["replace", "append"] = "replace"
    options: dict | None = None
```

**Example:**

```python
sink = FileSink(
    type="file",
    path="output/results.parquet",
    format="parquet",
    mode="replace"
)
```

### DatabaseSink

Write to databases.

```python
class DatabaseSink(BaseModel):
    type: Literal["database"]
    connection: str
    table: str
    mode: Literal["replace", "append", "upsert"] = "replace"
    upsert_keys: list[str] | None = None
```

**Example:**

```python
# Replace mode
sink = DatabaseSink(
    type="database",
    connection="postgres",
    table="analytics.summary",
    mode="replace"
)

# Upsert mode
sink = DatabaseSink(
    type="database",
    connection="postgres",
    table="analytics.summary",
    mode="upsert",
    upsert_keys=["id"]
)
```

## Transform Models

All transforms use a discriminated union based on the `op` field.

### SelectTransform

```python
class SelectTransform(BaseModel):
    op: Literal["select"]
    columns: list[str]
```

### RenameTransform

```python
class RenameTransform(BaseModel):
    op: Literal["rename"]
    columns: dict[str, str]  # old_name: new_name
```

### FilterTransform

```python
class FilterTransform(BaseModel):
    op: Literal["filter"]
    predicate: str
```

### DeriveColumnTransform

```python
class DeriveColumnTransform(BaseModel):
    op: Literal["derive_column"]
    name: str
    expr: str
```

### CastTransform

```python
class CastTransform(BaseModel):
    op: Literal["cast"]
    columns: dict[str, str]  # column: type
```

### FillNullTransform

```python
class FillNullTransform(BaseModel):
    op: Literal["fill_null"]
    columns: dict[str, Any]  # column: value
```

### DedupTransform

```python
class DedupTransform(BaseModel):
    op: Literal["dedup"]
    columns: list[str] | None = None  # None = all columns
    keep: Literal["first", "last"] = "first"
```

### SortTransform

```python
class SortColumn(BaseModel):
    column: str
    order: Literal["asc", "desc"] = "asc"

class SortTransform(BaseModel):
    op: Literal["sort"]
    by: list[SortColumn]
```

### JoinTransform

```python
class JoinTransform(BaseModel):
    op: Literal["join"]
    right: SourceConfig
    on: list[str]
    how: Literal["inner", "left", "right", "outer"] = "inner"
```

### AggregateTransform

```python
class AggregateTransform(BaseModel):
    op: Literal["aggregate"]
    group_by: list[str]
    aggregations: dict[str, str]  # output_name: expression
```

### UnionTransform

```python
class UnionTransform(BaseModel):
    op: Literal["union"]
    sources: list[SourceConfig]
```

### LimitTransform

```python
class LimitTransform(BaseModel):
    op: Literal["limit"]
    n: int
    offset: int = 0
```

## Check Models

### NotNullCheck

```python
class NotNullCheck(BaseModel):
    check: Literal["not_null"]
    columns: list[str]
```

### UniqueCheck

```python
class UniqueCheck(BaseModel):
    check: Literal["unique"]
    columns: list[str]
```

### RowCountCheck

```python
class RowCountCheck(BaseModel):
    check: Literal["row_count"]
    min: int | None = None
    max: int | None = None
    exact: int | None = None
```

### AcceptedValuesCheck

```python
class AcceptedValuesCheck(BaseModel):
    check: Literal["accepted_values"]
    column: str
    values: list[Any]
```

### ExpressionCheck

```python
class ExpressionCheck(BaseModel):
    check: Literal["expression"]
    expr: str
    threshold: float = 1.0  # Fraction that must pass
```

## Complete Example

```python
from quicketl import Pipeline
from quicketl.config import (
    PipelineConfig,
    FileSource,
    FileSink,
    FilterTransform,
    DeriveColumnTransform,
    AggregateTransform,
    SortTransform,
    SortColumn,
    NotNullCheck,
    RowCountCheck
)

config = PipelineConfig(
    name="sales_analytics",
    description="Compute sales metrics by category",
    engine="duckdb",

    source=FileSource(
        type="file",
        path="data/sales.parquet",
        format="parquet"
    ),

    transforms=[
        FilterTransform(
            op="filter",
            predicate="status = 'completed' AND amount > 0"
        ),
        DeriveColumnTransform(
            op="derive_column",
            name="net_amount",
            expr="amount - discount"
        ),
        AggregateTransform(
            op="aggregate",
            group_by=["category"],
            aggregations={
                "total_revenue": "sum(net_amount)",
                "order_count": "count(*)",
                "avg_order": "avg(net_amount)"
            }
        ),
        SortTransform(
            op="sort",
            by=[SortColumn(column="total_revenue", order="desc")]
        )
    ],

    checks=[
        NotNullCheck(check="not_null", columns=["category", "total_revenue"]),
        RowCountCheck(check="row_count", min=1)
    ],

    sink=FileSink(
        type="file",
        path="output/category_metrics.parquet",
        format="parquet"
    )
)

# Create and run pipeline
pipeline = Pipeline.from_model(config)
result = pipeline.run()
```

## Validation

Pydantic models provide automatic validation:

```python
from pydantic import ValidationError
from quicketl.config import PipelineConfig

try:
    config = PipelineConfig(
        name="test",
        source={"type": "invalid"},  # Invalid!
        sink={"type": "file", "path": "out.csv", "format": "csv"}
    )
except ValidationError as e:
    print(e)
    # source -> type
    #   Input should be 'file' or 'database'
```

## Serialization

### To Dictionary

```python
config_dict = config.model_dump()
```

### To JSON

```python
config_json = config.model_dump_json(indent=2)
```

### To YAML

```python
import yaml

config_dict = config.model_dump()
config_yaml = yaml.dump(config_dict)
```

## Related

- [Pipeline YAML](../guides/configuration/pipeline-yaml.md) - YAML format reference
- [Transforms](../guides/transforms/index.md) - Transform documentation
- [Quality Checks](../guides/quality/index.md) - Check documentation
