# unique

Verify that column values are unique (no duplicates).

## Usage

```yaml
- type: unique
  columns: [id]
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `columns` | Yes | `list[str]` | Columns that must be unique |

## Examples

### Single Column

```yaml
- type: unique
  columns: [id]
```

### Composite Key

```yaml
- type: unique
  columns: [customer_id, order_date]
```

## Pass/Fail Behavior

**Pass**: All combinations of specified columns are unique.

**Fail**: Duplicate values found.

### Failure Message

```
Check failed: unique
  Found 23 duplicate values in columns [id]
```

## Python API

```python
from etlx.config.checks import UniqueCheck

check = UniqueCheck(columns=["id"])
check = UniqueCheck(columns=["customer_id", "order_date"])
```

## Common Patterns

### Primary Key

```yaml
- type: unique
  columns: [id]
```

### Natural Key

```yaml
- type: unique
  columns: [customer_id, product_id, order_date]
```

### After Dedup

```yaml
transforms:
  - op: dedup
    columns: [id]

checks:
  - type: unique
    columns: [id]  # Verify dedup worked
```

## Tips

### Null Handling

Nulls are treated as equal for uniqueness:

- Two rows with `NULL` in `id` → Duplicate

To exclude nulls:

```yaml
transforms:
  - op: filter
    predicate: id IS NOT NULL

checks:
  - type: unique
    columns: [id]
```

### Composite Uniqueness

Check combination of columns:

```yaml
# Each customer can have one order per day
- type: unique
  columns: [customer_id, order_date]
```

## Related

- [dedup transform](../transforms/dedup.md) - Remove duplicates
- [not_null check](not-null.md) - Often combined with unique
