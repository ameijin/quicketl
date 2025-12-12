# limit

Limit output to the first N rows.

## Usage

```yaml
- op: limit
  n: 1000
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `n` | Yes | `int` | Maximum number of rows (must be > 0) |

## Examples

### Basic Limit

```yaml
- op: limit
  n: 100
```

### Top N Pattern

```yaml
transforms:
  - op: sort
    by: [sales]
    descending: true

  - op: limit
    n: 10
```

### Sample Data

```yaml
# Get sample for testing
- op: limit
  n: 1000
```

## Input/Output Example

**Input Data (1000 rows):**

| id | name | amount |
|----|------|--------|
| 1 | Widget A | 500 |
| 2 | Widget B | 400 |
| 3 | Widget C | 300 |
| ... | ... | ... |

**Transform:**

```yaml
- op: limit
  n: 3
```

**Output Data:**

| id | name | amount |
|----|------|--------|
| 1 | Widget A | 500 |
| 2 | Widget B | 400 |
| 3 | Widget C | 300 |

## Python API

```python
from quicketl.config.transforms import LimitTransform

transform = LimitTransform(n=1000)
```

## Common Patterns

### Top N by Value

```yaml
transforms:
  - op: sort
    by: [revenue]
    descending: true

  - op: limit
    n: 10
```

### Top N per Group

For top N per group, use Python:

```python
# Top 5 products per category
result = (
    engine.sort(data, ["amount"], descending=True)
    .over(group_by=["category"])
    .head(5)
)
```

### Development Sampling

```yaml
# Limit data for faster development
transforms:
  - op: limit
    n: ${SAMPLE_SIZE:-10000}
```

```bash
# Development
quicketl run pipeline.yml --var SAMPLE_SIZE=1000

# Production
quicketl run pipeline.yml --var SAMPLE_SIZE=1000000
```

### Preview Data

```yaml
transforms:
  # Quick preview
  - op: limit
    n: 5
```

## Tips

### Order Matters

Without sorting, limit returns arbitrary rows:

```yaml
# Arbitrary 10 rows
- op: limit
  n: 10

# Definite top 10 by amount
transforms:
  - op: sort
    by: [amount]
    descending: true
  - op: limit
    n: 10
```

### Use for Testing

Limit data during development:

```yaml
transforms:
  # ... your transforms ...

  # Remove in production
  - op: limit
    n: 100
```

### Memory Management

For very large datasets, limit early:

```yaml
transforms:
  - op: limit
    n: 1000000  # Process at most 1M rows

  # ... expensive transforms ...
```

## Errors

### Invalid N

```
Error: 'n' must be greater than 0
```

Provide a positive integer.

## Related

- [sort](sort.md) - Sort before limit for Top N
- [filter](filter.md) - Filter instead of arbitrary limit
