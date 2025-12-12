# fill_null

Replace null values with specified defaults.

## Usage

```yaml
- op: fill_null
  columns:
    amount: 0
    status: "unknown"
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `dict[str, any]` | Column → replacement value |

## Examples

### Numeric Default

```yaml
- op: fill_null
  columns:
    amount: 0
    discount: 0.0
    quantity: 1
```

### String Default

```yaml
- op: fill_null
  columns:
    status: "unknown"
    category: "uncategorized"
```

### Multiple Types

```yaml
- op: fill_null
  columns:
    amount: 0
    discount: 0.0
    status: "pending"
    notes: ""
```

## Input/Output Example

**Input Data:**

| id | amount | status |
|----|--------|--------|
| 1 | 100 | active |
| 2 | NULL | NULL |
| 3 | 200 | NULL |

**Transform:**

```yaml
- op: fill_null
  columns:
    amount: 0
    status: "unknown"
```

**Output Data:**

| id | amount | status |
|----|--------|--------|
| 1 | 100 | active |
| 2 | 0 | unknown |
| 3 | 200 | unknown |

## Python API

```python
from quicketl.config.transforms import FillNullTransform

transform = FillNullTransform(
    columns={
        "amount": 0,
        "status": "unknown",
    }
)
```

## Common Patterns

### Prepare for Calculations

```yaml
transforms:
  # Fill nulls before arithmetic
  - op: fill_null
    columns:
      quantity: 1
      discount: 0

  - op: derive_column
    name: total
    expr: (quantity * price) - discount
```

### Clean for Aggregation

```yaml
transforms:
  - op: fill_null
    columns:
      amount: 0

  - op: aggregate
    group_by: [category]
    aggs:
      total: sum(amount)  # Nulls would be ignored
```

### Default Categories

```yaml
- op: fill_null
  columns:
    region: "Other"
    category: "Uncategorized"
    tier: "Standard"
```

### Boolean Defaults

```yaml
- op: fill_null
  columns:
    is_active: true
    is_verified: false
```

## Tips

### Type Matching

Fill values should match column types:

```yaml
# If amount is integer
- op: fill_null
  columns:
    amount: 0     # Integer, not "0" or 0.0

# If amount is float
- op: fill_null
  columns:
    amount: 0.0   # Float
```

### Alternative: COALESCE in derive_column

For more complex defaults:

```yaml
- op: derive_column
  name: amount_clean
  expr: COALESCE(amount, default_amount, 0)
```

### Fill All String Columns

```yaml
- op: fill_null
  columns:
    name: ""
    email: ""
    phone: ""
    address: ""
```

## Errors

### Type Mismatch

```
Error: Cannot fill integer column with string value
```

Ensure fill value type matches column type.

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Verify the column exists.

## Related

- [derive_column](derive-column.md) - Use COALESCE for conditional filling
- [cast](cast.md) - Convert types after filling
- [not_null check](../quality/not-null.md) - Verify no nulls remain
