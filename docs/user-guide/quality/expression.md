# expression

Validate data using a custom SQL expression.

## Usage

```yaml
- type: expression
  expr: amount >= 0
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `expr` | Yes | `str` | SQL expression that must be true for all rows |

## Examples

### Positive Values

```yaml
- type: expression
  expr: amount >= 0
```

### Range Check

```yaml
- type: expression
  expr: amount BETWEEN 0 AND 10000
```

### Non-Empty String

```yaml
- type: expression
  expr: name IS NOT NULL AND length(name) > 0
```

### Date Validation

```yaml
- type: expression
  expr: created_at <= current_date()
```

### Multiple Conditions

```yaml
- type: expression
  expr: amount > 0 AND quantity > 0 AND price > 0
```

## Pass/Fail Behavior

**Pass**: Expression is true for all rows.

**Fail**: Expression is false for any row.

### Failure Message

```
Check failed: expression
  Expression 'amount >= 0' failed for 5 rows
```

## Python API

```python
from etlx.config.checks import ExpressionCheck

check = ExpressionCheck(expr="amount >= 0")
```

## Common Patterns

### Business Rules

```yaml
# Total must equal sum of parts
- type: expression
  expr: total = subtotal + tax + shipping

# Discount can't exceed amount
- type: expression
  expr: discount <= amount

# End date after start date
- type: expression
  expr: end_date >= start_date
```

### Data Quality Rules

```yaml
# Valid email format (basic)
- type: expression
  expr: email LIKE '%@%.%'

# Reasonable date range
- type: expression
  expr: order_date >= '2020-01-01' AND order_date <= current_date()

# Positive quantities
- type: expression
  expr: quantity > 0
```

### Consistency Checks

```yaml
# Status matches value
- type: expression
  expr: |
    CASE
      WHEN status = 'completed' THEN completed_at IS NOT NULL
      ELSE true
    END
```

### Aggregation Result Checks

```yaml
# After aggregation
- type: expression
  expr: order_count > 0 AND total_sales >= 0
```

## Expression Syntax

### Operators

| Operator | Example |
|----------|---------|
| `=`, `!=` | `status = 'active'` |
| `>`, `<`, `>=`, `<=` | `amount >= 0` |
| `AND`, `OR` | `a > 0 AND b < 100` |
| `IN` | `status IN ('a', 'b')` |
| `BETWEEN` | `amount BETWEEN 0 AND 1000` |
| `LIKE` | `email LIKE '%@%'` |
| `IS NULL` | `discount IS NULL` |

### Functions

| Function | Example |
|----------|---------|
| `length()` | `length(name) > 0` |
| `lower()` | `lower(status) = 'active'` |
| `COALESCE()` | `COALESCE(amount, 0) >= 0` |

## Tips

### Multiline Expressions

```yaml
- type: expression
  expr: |
    amount > 0
    AND quantity > 0
    AND status IN ('pending', 'active', 'completed')
```

### Complex Logic

```yaml
- type: expression
  expr: |
    CASE
      WHEN order_type = 'refund' THEN amount < 0
      ELSE amount > 0
    END
```

### Null-Safe Comparisons

```yaml
# Handle nulls explicitly
- type: expression
  expr: COALESCE(discount, 0) <= amount
```

## Errors

### Syntax Error

```
Error: Could not parse expression
```

Check expression syntax.

### Column Not Found

```
Error: Column 'nonexistent' not found
```

Verify column names.

## Related

- [Expression Language](../../reference/expressions.md) - Full expression reference
- [accepted_values check](accepted-values.md) - Simpler value validation
- [derive_column transform](../transforms/derive-column.md) - Uses same expression syntax
