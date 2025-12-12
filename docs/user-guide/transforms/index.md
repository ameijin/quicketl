# Transforms

Transforms modify data as it flows through your pipeline. QuickETL provides 12 built-in transform operations.

## Overview

Transforms are applied in sequence. Each transform takes the output of the previous step as input.

```yaml
transforms:
  - op: filter          # Step 1: Filter rows
    predicate: amount > 0

  - op: derive_column   # Step 2: Add column (uses filtered data)
    name: tax
    expr: amount * 0.1

  - op: aggregate       # Step 3: Aggregate (uses data with tax column)
    group_by: [category]
    aggs:
      total: sum(amount)
```

## Transform Operations

### Data Selection

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`select`](select.md) | Choose columns | Keep only `id`, `name`, `amount` |
| [`rename`](rename.md) | Rename columns | Change `cust_id` to `customer_id` |
| [`limit`](limit.md) | Limit rows | Take first 1000 rows |

### Data Filtering

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`filter`](filter.md) | Filter rows | Keep rows where `amount > 100` |
| [`dedup`](dedup.md) | Remove duplicates | Keep unique `customer_id` |

### Data Modification

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`derive_column`](derive-column.md) | Add computed column | Calculate `total = qty * price` |
| [`cast`](cast.md) | Convert types | Change `id` from int to string |
| [`fill_null`](fill-null.md) | Replace nulls | Set null `status` to `"unknown"` |

### Data Organization

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`sort`](sort.md) | Order rows | Sort by `amount` descending |
| [`aggregate`](aggregate.md) | Group and summarize | Sum `amount` by `region` |

### Data Combination

| Transform | Purpose | Example |
|-----------|---------|---------|
| [`join`](join.md) | Join datasets | Join orders with customers |
| [`union`](union.md) | Stack datasets | Combine daily files |

## Quick Reference

```yaml
# Select columns
- op: select
  columns: [id, name, amount]

# Rename columns
- op: rename
  mapping:
    old_name: new_name

# Filter rows
- op: filter
  predicate: amount > 100 AND status = 'active'

# Add computed column
- op: derive_column
  name: total_with_tax
  expr: amount * 1.1

# Convert types
- op: cast
  columns:
    id: string
    amount: float64

# Replace nulls
- op: fill_null
  columns:
    status: "unknown"
    amount: 0

# Remove duplicates
- op: dedup
  columns: [customer_id]

# Sort rows
- op: sort
  by: [amount]
  descending: true

# Join datasets
- op: join
  right: customers
  on: [customer_id]
  how: left

# Aggregate
- op: aggregate
  group_by: [region]
  aggs:
    total: sum(amount)
    count: count(*)

# Combine datasets
- op: union
  sources: [data1, data2]

# Limit rows
- op: limit
  n: 1000
```

## Transform Order Best Practices

### 1. Filter Early

Apply filters as early as possible to reduce data volume:

```yaml
transforms:
  - op: filter              # First: reduce rows
    predicate: date >= '2025-01-01'

  - op: derive_column       # Then: compute on smaller dataset
    name: metric
    expr: complex_calculation
```

### 2. Select Before Aggregate

Remove unnecessary columns before aggregation:

```yaml
transforms:
  - op: select              # Remove unused columns
    columns: [category, amount]

  - op: aggregate           # Aggregate on smaller dataset
    group_by: [category]
    aggs:
      total: sum(amount)
```

### 3. Derive Before Aggregate

Create columns needed for aggregation:

```yaml
transforms:
  - op: derive_column       # Create column first
    name: net_amount
    expr: amount - discount

  - op: aggregate           # Then aggregate
    group_by: [region]
    aggs:
      total_net: sum(net_amount)
```

## Expression Language

Many transforms use SQL-like expressions:

### Operators

| Type | Operators |
|------|-----------|
| Arithmetic | `+`, `-`, `*`, `/` |
| Comparison | `=`, `!=`, `>`, `<`, `>=`, `<=` |
| Logical | `AND`, `OR`, `NOT` |
| Null | `IS NULL`, `IS NOT NULL` |

### Functions

| Category | Functions |
|----------|-----------|
| String | `UPPER()`, `LOWER()`, `TRIM()`, `CONCAT()` |
| Math | `ABS()`, `ROUND()`, `FLOOR()`, `CEIL()` |
| Date | `EXTRACT()`, `DATE_TRUNC()` |
| Null | `COALESCE()`, `NULLIF()` |
| Aggregate | `SUM()`, `AVG()`, `MIN()`, `MAX()`, `COUNT()` |

See [Expression Language](../../reference/expressions.md) for full reference.

## Python API

```python
from quicketl.config.transforms import (
    SelectTransform,
    FilterTransform,
    DeriveColumnTransform,
    AggregateTransform,
)

pipeline = (
    Pipeline("example")
    .source(source)
    .transform(FilterTransform(predicate="amount > 0"))
    .transform(DeriveColumnTransform(name="tax", expr="amount * 0.1"))
    .transform(AggregateTransform(
        group_by=["category"],
        aggs={"total": "sum(amount)"}
    ))
    .sink(sink)
)
```

## Next Steps

Explore each transform in detail:

- [select](select.md) - Choose and reorder columns
- [filter](filter.md) - Filter rows with predicates
- [aggregate](aggregate.md) - Group and summarize data
