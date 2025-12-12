# row_count

Verify that the row count is within expected bounds.

## Usage

```yaml
- type: row_count
  min: 1
  max: 1000000
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `min` | No | None | Minimum row count |
| `max` | No | None | Maximum row count |

At least one of `min` or `max` must be specified.

## Examples

### Minimum Only

```yaml
- type: row_count
  min: 1
```

### Maximum Only

```yaml
- type: row_count
  max: 1000000
```

### Both Bounds

```yaml
- type: row_count
  min: 100
  max: 10000
```

## Pass/Fail Behavior

**Pass**: Row count is within specified bounds.

**Fail**: Row count is outside bounds.

### Failure Messages

```
Check failed: row_count
  Row count 0 is below minimum 1

Check failed: row_count
  Row count 1500000 exceeds maximum 1000000
```

## Python API

```python
from quicketl.config.checks import RowCountCheck

# At least 1 row
check = RowCountCheck(min=1)

# Between bounds
check = RowCountCheck(min=100, max=10000)
```

## Common Patterns

### Non-Empty Output

```yaml
- type: row_count
  min: 1
```

### Expected Range

```yaml
# Daily sales should have 1K-10K rows
- type: row_count
  min: 1000
  max: 10000
```

### Detect Anomalies

```yaml
# Alert if unusually high
- type: row_count
  max: 100000
```

### After Filter

```yaml
transforms:
  - op: filter
    predicate: status = 'active'

checks:
  # Ensure filter didn't remove everything
  - type: row_count
    min: 1
```

## Tips

### Use Variables

```yaml
- type: row_count
  min: ${MIN_ROWS:-1}
  max: ${MAX_ROWS:-1000000}
```

### Document Expected Ranges

```yaml
# Daily pipeline: expect 5K-50K rows
# Less than 5K suggests data source issue
# More than 50K suggests duplicate ingestion
- type: row_count
  min: 5000
  max: 50000
```

## Related

- [filter transform](../transforms/filter.md) - May affect row count
- [dedup transform](../transforms/dedup.md) - May reduce row count
