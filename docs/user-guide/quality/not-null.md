# not_null

Verify that specified columns contain no null values.

## Usage

```yaml
- type: not_null
  columns: [id, name, amount]
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `list[str]` | Columns that must not contain nulls |

## Examples

### Single Column

```yaml
- type: not_null
  columns: [id]
```

### Multiple Columns

```yaml
- type: not_null
  columns: [id, customer_id, amount, created_at]
```

## Pass/Fail Behavior

**Pass**: All values in specified columns are non-null.

**Fail**: Any null value found in specified columns.

### Failure Message

```
Check failed: not_null
  Column 'customer_id' contains 15 null values
```

## Python API

```python
from etlx.config.checks import NotNullCheck

check = NotNullCheck(columns=["id", "name", "amount"])
```

## Common Patterns

### Check Primary Key

```yaml
- type: not_null
  columns: [id]
```

### Check Foreign Keys

```yaml
- type: not_null
  columns: [customer_id, product_id, order_id]
```

### Check Required Fields

```yaml
- type: not_null
  columns: [email, name, created_at]
```

### After Join

```yaml
transforms:
  - op: join
    right: customers
    on: [customer_id]
    how: left

checks:
  # Verify join found matches
  - type: not_null
    columns: [customer_name]
```

## Tips

### Fill Nulls First

If nulls are expected, fill them before checking:

```yaml
transforms:
  - op: fill_null
    columns:
      status: "unknown"

checks:
  - type: not_null
    columns: [status]  # Now passes
```

### Check After Transforms

Checks run after transforms, so derived columns can be checked:

```yaml
transforms:
  - op: derive_column
    name: total
    expr: quantity * price

checks:
  - type: not_null
    columns: [total]  # Checks derived column
```

## Related

- [fill_null transform](../transforms/fill-null.md) - Replace nulls
- [filter transform](../transforms/filter.md) - Remove null rows
- [unique check](unique.md) - Also catches nulls in unique columns
