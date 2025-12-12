# union

Vertically combine multiple datasets.

## Usage

```yaml
- op: union
  sources: [data1, data2]
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `sources` | Yes | `list[str]` | References to datasets to combine |

## Examples

### Combine Two Datasets

```yaml
- op: union
  sources: [north_sales, south_sales]
```

### Combine Multiple Datasets

```yaml
- op: union
  sources: [q1_data, q2_data, q3_data, q4_data]
```

## Input/Output Example

**Dataset 1 (north_sales):**

| id | region | amount |
|----|--------|--------|
| 1 | North | 100 |
| 2 | North | 200 |

**Dataset 2 (south_sales):**

| id | region | amount |
|----|--------|--------|
| 3 | South | 150 |
| 4 | South | 250 |

**Transform:**

```yaml
- op: union
  sources: [north_sales, south_sales]
```

**Output:**

| id | region | amount |
|----|--------|--------|
| 1 | North | 100 |
| 2 | North | 200 |
| 3 | South | 150 |
| 4 | South | 250 |

## Python API

```python
from etlx import ETLXEngine

engine = ETLXEngine(backend="duckdb")

# Read datasets
north = engine.read_file("north_sales.parquet", "parquet")
south = engine.read_file("south_sales.parquet", "parquet")

# Union
combined = engine.union([north, south])
```

## Common Patterns

### Combine Daily Files

```python
engine = ETLXEngine(backend="duckdb")

# Read daily files
files = [
    engine.read_file(f"data/{date}/sales.parquet", "parquet")
    for date in ["2025-01-01", "2025-01-02", "2025-01-03"]
]

# Combine
combined = engine.union(files)
```

### Combine Regional Data

```python
# Read regional files
regions = ["north", "south", "east", "west"]
datasets = [
    engine.read_file(f"data/{region}/sales.parquet", "parquet")
    for region in regions
]

combined = engine.union(datasets)
```

### Add Source Column

Track which dataset each row came from:

```python
north = engine.read_file("north.parquet", "parquet")
south = engine.read_file("south.parquet", "parquet")

# Add source identifier
north = engine.derive_column(north, "source", "'north'")
south = engine.derive_column(south, "source", "'south'")

combined = engine.union([north, south])
```

## Requirements

### Matching Schemas

All datasets must have the same columns:

```python
# Both must have: id, name, amount
north = engine.read_file("north.parquet", "parquet")  # id, name, amount
south = engine.read_file("south.parquet", "parquet")  # id, name, amount

combined = engine.union([north, south])  # Works
```

### Column Order

Columns should be in the same order. Use `select` to align:

```python
# Align columns before union
north = engine.select(north, ["id", "name", "amount"])
south = engine.select(south, ["id", "name", "amount"])

combined = engine.union([north, south])
```

## Tips

### Dedup After Union

Remove duplicates that might exist across sources:

```python
combined = engine.union([data1, data2])
deduped = engine.dedup(combined, ["id"])
```

### Filter After Union

Apply consistent filters:

```python
combined = engine.union([q1, q2, q3, q4])
filtered = engine.filter(combined, "amount > 0")
```

### Add Metadata

Track source information:

```yaml
transforms:
  # After union
  - op: derive_column
    name: loaded_at
    expr: current_timestamp()
```

## Errors

### Schema Mismatch

```
Error: Cannot union tables with different schemas
```

Ensure all datasets have identical column names and types.

### Empty Sources

```
Error: Union requires at least two datasets
```

Provide at least two datasets to combine.

## Related

- [dedup](dedup.md) - Remove duplicates after union
- [select](select.md) - Align columns before union
- [derive_column](derive-column.md) - Add source tracking
