# accepted_values

Verify that all values in a column are from an allowed list.

## Usage

```yaml
- type: accepted_values
  column: status
  values: [pending, active, completed]
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `column` | Yes | `str` | Column to check |
| `values` | Yes | `list[any]` | Allowed values |

## Examples

### Status Field

```yaml
- type: accepted_values
  column: status
  values: [pending, active, completed, cancelled]
```

### Region Codes

```yaml
- type: accepted_values
  column: region
  values: [north, south, east, west]
```

### Numeric Values

```yaml
- type: accepted_values
  column: priority
  values: [1, 2, 3, 4, 5]
```

## Pass/Fail Behavior

**Pass**: All values in the column are in the allowed list.

**Fail**: Any value not in the allowed list.

### Failure Message

```
Check failed: accepted_values
  Column 'status' contains invalid values: ['invalid', 'unknown']
```

## Python API

```python
from quicketl.config.checks import AcceptedValuesCheck

check = AcceptedValuesCheck(
    column="status",
    values=["pending", "active", "completed"]
)
```

## Common Patterns

### Enum-like Fields

```yaml
- type: accepted_values
  column: order_type
  values: [online, in_store, phone, partner]
```

### Boolean-ish Fields

```yaml
- type: accepted_values
  column: is_verified
  values: [true, false, "Y", "N", 1, 0]
```

### Category Validation

```yaml
- type: accepted_values
  column: category
  values: [Electronics, Home, Office, Clothing, Food]
```

## Tips

### Null Handling

By default, nulls are considered invalid. To allow nulls:

```yaml
- type: accepted_values
  column: status
  values: [pending, active, null]
```

Or filter first:

```yaml
transforms:
  - op: filter
    predicate: status IS NOT NULL

checks:
  - type: accepted_values
    column: status
    values: [pending, active, completed]
```

### Case Sensitivity

Values are case-sensitive:

```yaml
# "ACTIVE" won't match "active"
values: [pending, active, completed]
```

Standardize case first:

```yaml
transforms:
  - op: derive_column
    name: status_lower
    expr: lower(status)

checks:
  - type: accepted_values
    column: status_lower
    values: [pending, active, completed]
```

## Related

- [expression check](expression.md) - More complex validations
- [filter transform](../transforms/filter.md) - Remove invalid values
