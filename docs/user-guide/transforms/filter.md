# filter

Filter rows based on a SQL-like predicate.

## Usage

```yaml
- op: filter
  predicate: amount > 100
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `predicate` | Yes | `str` | SQL-like boolean expression |

## Examples

### Simple Comparison

```yaml
- op: filter
  predicate: amount > 100
```

### Equality

```yaml
- op: filter
  predicate: status = 'active'
```

### Multiple Conditions

```yaml
# AND
- op: filter
  predicate: amount > 100 AND status = 'active'

# OR
- op: filter
  predicate: region = 'north' OR region = 'south'
```

### Null Handling

```yaml
# Keep non-null values
- op: filter
  predicate: email IS NOT NULL

# Keep null values
- op: filter
  predicate: discount IS NULL
```

### Date Filtering

```yaml
- op: filter
  predicate: created_at >= '2025-01-01'

- op: filter
  predicate: created_at >= '${START_DATE}' AND created_at < '${END_DATE}'
```

### IN Operator

```yaml
- op: filter
  predicate: category IN ('Electronics', 'Home', 'Office')
```

### String Matching

```yaml
# Starts with
- op: filter
  predicate: name LIKE 'Widget%'

# Contains
- op: filter
  predicate: description LIKE '%sale%'
```

## Input/Output Example

**Input Data:**

| id | name | amount | status |
|----|------|--------|--------|
| 1 | Widget A | 50 | active |
| 2 | Widget B | 150 | active |
| 3 | Widget C | 200 | inactive |
| 4 | Widget D | 75 | active |

**Transform:**

```yaml
- op: filter
  predicate: amount > 100 AND status = 'active'
```

**Output Data:**

| id | name | amount | status |
|----|------|--------|--------|
| 2 | Widget B | 150 | active |

## Operators Reference

### Comparison

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `status = 'active'` |
| `!=` or `<>` | Not equal | `status != 'cancelled'` |
| `>` | Greater than | `amount > 100` |
| `<` | Less than | `amount < 1000` |
| `>=` | Greater or equal | `amount >= 100` |
| `<=` | Less or equal | `amount <= 1000` |

### Logical

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Both conditions | `a > 1 AND b < 10` |
| `OR` | Either condition | `a = 1 OR b = 2` |
| `NOT` | Negate | `NOT status = 'cancelled'` |

### Null

| Operator | Description | Example |
|----------|-------------|---------|
| `IS NULL` | Is null | `discount IS NULL` |
| `IS NOT NULL` | Is not null | `email IS NOT NULL` |

### Other

| Operator | Description | Example |
|----------|-------------|---------|
| `IN` | In list | `region IN ('north', 'south')` |
| `NOT IN` | Not in list | `status NOT IN ('cancelled', 'refunded')` |
| `BETWEEN` | In range | `amount BETWEEN 100 AND 500` |
| `LIKE` | Pattern match | `name LIKE 'Widget%'` |

## Python API

```python
from etlx.config.transforms import FilterTransform

# Simple
transform = FilterTransform(predicate="amount > 100")

# Complex
transform = FilterTransform(
    predicate="amount > 100 AND status = 'active' AND region IN ('north', 'south')"
)
```

## Common Patterns

### Clean Invalid Data

```yaml
transforms:
  - op: filter
    predicate: amount > 0 AND amount IS NOT NULL

  - op: filter
    predicate: customer_id IS NOT NULL
```

### Date Range

```yaml
- op: filter
  predicate: |
    created_at >= '${START_DATE}'
    AND created_at < '${END_DATE}'
```

### Exclude Test Data

```yaml
- op: filter
  predicate: email NOT LIKE '%@test.com' AND name NOT LIKE 'Test %'
```

### Active Records Only

```yaml
- op: filter
  predicate: status = 'active' AND deleted_at IS NULL
```

## Performance Tips

### Filter Early

Apply filters as early as possible:

```yaml
transforms:
  # Good: filter first, reduces data for subsequent operations
  - op: filter
    predicate: date >= '2025-01-01'

  - op: derive_column
    name: complex_metric
    expr: expensive_calculation
```

### Use Database Filters

For database sources, filter in the query:

```yaml
# Better: filter in database
source:
  type: database
  query: SELECT * FROM sales WHERE date >= '2025-01-01'

# Less efficient: filter after loading
source:
  type: database
  table: sales
transforms:
  - op: filter
    predicate: date >= '2025-01-01'
```

## Tips

### Quoting Strings

Use single quotes for string values:

```yaml
predicate: status = 'active'   # Correct
predicate: status = "active"   # May not work
```

### Escaping Quotes

For values containing quotes:

```yaml
predicate: name = 'O''Brien'   # Single quote escape
```

### Complex Predicates

Use parentheses for clarity:

```yaml
predicate: (region = 'north' OR region = 'south') AND amount > 100
```

## Errors

### Syntax Error

```
Error: Could not parse predicate
```

Check your predicate syntax. Common issues:

- Missing quotes around strings
- Typo in column name
- Invalid operator

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Verify the column exists in your data.

## Related

- [derive_column](derive-column.md) - Create columns for filtering
- [dedup](dedup.md) - Another way to reduce rows
- [Expression Language](../../reference/expressions.md) - Full expression syntax
