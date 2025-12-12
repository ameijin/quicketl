# sort

Order rows by one or more columns.

## Usage

```yaml
- op: sort
  by: [amount]
  descending: true
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `by` | Yes | - | Columns to sort by |
| `descending` | No | `false` | Sort in descending order |

## Examples

### Single Column Ascending

```yaml
- op: sort
  by: [name]
```

### Single Column Descending

```yaml
- op: sort
  by: [amount]
  descending: true
```

### Multiple Columns

```yaml
- op: sort
  by: [category, amount]
  descending: true
```

## Input/Output Example

**Input Data:**

| id | name | amount |
|----|------|--------|
| 1 | Widget C | 50 |
| 2 | Widget A | 150 |
| 3 | Widget B | 100 |

**Transform (ascending):**

```yaml
- op: sort
  by: [amount]
```

**Output:**

| id | name | amount |
|----|------|--------|
| 1 | Widget C | 50 |
| 3 | Widget B | 100 |
| 2 | Widget A | 150 |

**Transform (descending):**

```yaml
- op: sort
  by: [amount]
  descending: true
```

**Output:**

| id | name | amount |
|----|------|--------|
| 2 | Widget A | 150 |
| 3 | Widget B | 100 |
| 1 | Widget C | 50 |

## Python API

```python
from quicketl.config.transforms import SortTransform

# Ascending
transform = SortTransform(by=["amount"])

# Descending
transform = SortTransform(by=["amount"], descending=True)

# Multiple columns
transform = SortTransform(by=["category", "amount"], descending=True)
```

## Common Patterns

### Top N Pattern

```yaml
transforms:
  - op: sort
    by: [sales]
    descending: true

  - op: limit
    n: 10
```

### Sort After Aggregation

```yaml
transforms:
  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)

  - op: sort
    by: [total]
    descending: true
```

### Sort for Reporting

```yaml
transforms:
  # Sort by region, then by sales within region
  - op: sort
    by: [region, total_sales]
    descending: true
```

## Tips

### Nulls

Null values typically sort last (ascending) or first (descending).

### Performance

Sorting large datasets is expensive. Consider:

- Sort after filtering to reduce rows
- Sort after aggregation when possible
- May not be needed if output order doesn't matter

### Multiple Sort Directions

Currently, all columns use the same direction. For mixed directions, use multiple sorts or SQL in the source query.

## Errors

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Verify the column exists.

## Related

- [limit](limit.md) - Often used after sort for Top N
- [aggregate](aggregate.md) - Sort aggregation results
