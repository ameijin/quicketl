# derive_column

Create a new computed column from an expression.

## Usage

```yaml
- op: derive_column
  name: total_with_tax
  expr: amount * 1.1
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | `str` | Name for the new column |
| `expr` | Yes | `str` | SQL-like expression |

## Examples

### Arithmetic

```yaml
# Multiplication
- op: derive_column
  name: total_with_tax
  expr: amount * 1.1

# Division
- op: derive_column
  name: unit_price
  expr: total / quantity

# Complex calculation
- op: derive_column
  name: profit_margin
  expr: (revenue - cost) / revenue * 100
```

### String Operations

```yaml
# Uppercase
- op: derive_column
  name: name_upper
  expr: upper(name)

# Concatenation
- op: derive_column
  name: full_name
  expr: concat(first_name, ' ', last_name)

# Substring
- op: derive_column
  name: country_code
  expr: substring(phone, 1, 2)
```

### Date Operations

```yaml
# Extract year
- op: derive_column
  name: year
  expr: extract(year from created_at)

# Extract month
- op: derive_column
  name: month
  expr: extract(month from created_at)

# Date truncation
- op: derive_column
  name: week_start
  expr: date_trunc('week', created_at)
```

### Conditional Logic

```yaml
# CASE expression
- op: derive_column
  name: size_category
  expr: |
    CASE
      WHEN amount < 100 THEN 'small'
      WHEN amount < 1000 THEN 'medium'
      ELSE 'large'
    END

# Simpler conditional
- op: derive_column
  name: is_high_value
  expr: amount >= 1000
```

### Null Handling

```yaml
# Default value for nulls
- op: derive_column
  name: discount_safe
  expr: COALESCE(discount, 0)

# Replace value with null
- op: derive_column
  name: amount_clean
  expr: NULLIF(amount, 0)
```

## Input/Output Example

**Input Data:**

| id | quantity | unit_price | discount |
|----|----------|------------|----------|
| 1 | 5 | 10.00 | 2.00 |
| 2 | 3 | 25.00 | NULL |
| 3 | 10 | 5.00 | 5.00 |

**Transforms:**

```yaml
- op: derive_column
  name: subtotal
  expr: quantity * unit_price

- op: derive_column
  name: total
  expr: subtotal - COALESCE(discount, 0)
```

**Output Data:**

| id | quantity | unit_price | discount | subtotal | total |
|----|----------|------------|----------|----------|-------|
| 1 | 5 | 10.00 | 2.00 | 50.00 | 48.00 |
| 2 | 3 | 25.00 | NULL | 75.00 | 75.00 |
| 3 | 10 | 5.00 | 5.00 | 50.00 | 45.00 |

## Expression Reference

### Arithmetic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `price + tax` |
| `-` | Subtraction | `total - discount` |
| `*` | Multiplication | `qty * price` |
| `/` | Division | `total / count` |

### Functions

#### String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `upper(s)` | Uppercase | `upper(name)` |
| `lower(s)` | Lowercase | `lower(email)` |
| `trim(s)` | Remove whitespace | `trim(name)` |
| `concat(...)` | Concatenate | `concat(a, b, c)` |
| `substring(s, start, len)` | Extract substring | `substring(phone, 1, 3)` |
| `length(s)` | String length | `length(name)` |

#### Date Functions

| Function | Description | Example |
|----------|-------------|---------|
| `extract(part from d)` | Extract component | `extract(year from date)` |
| `date_trunc(part, d)` | Truncate date | `date_trunc('month', date)` |

#### Null Functions

| Function | Description | Example |
|----------|-------------|---------|
| `COALESCE(a, b, ...)` | First non-null | `COALESCE(discount, 0)` |
| `NULLIF(a, b)` | Null if equal | `NULLIF(amount, 0)` |

#### Math Functions

| Function | Description | Example |
|----------|-------------|---------|
| `abs(n)` | Absolute value | `abs(difference)` |
| `round(n, d)` | Round | `round(price, 2)` |
| `floor(n)` | Round down | `floor(score)` |
| `ceil(n)` | Round up | `ceil(rating)` |

## Python API

```python
from etlx.config.transforms import DeriveColumnTransform

transform = DeriveColumnTransform(
    name="total_with_tax",
    expr="amount * 1.1"
)
```

## Common Patterns

### Calculate Metrics

```yaml
transforms:
  - op: derive_column
    name: revenue
    expr: quantity * unit_price

  - op: derive_column
    name: profit
    expr: revenue - cost

  - op: derive_column
    name: margin_pct
    expr: profit / revenue * 100
```

### Categorize Data

```yaml
- op: derive_column
  name: customer_tier
  expr: |
    CASE
      WHEN lifetime_value >= 10000 THEN 'platinum'
      WHEN lifetime_value >= 5000 THEN 'gold'
      WHEN lifetime_value >= 1000 THEN 'silver'
      ELSE 'bronze'
    END
```

### Clean Data

```yaml
transforms:
  - op: derive_column
    name: email_clean
    expr: lower(trim(email))

  - op: derive_column
    name: phone_digits
    expr: regexp_replace(phone, '[^0-9]', '')
```

### Date Dimensions

```yaml
transforms:
  - op: derive_column
    name: year
    expr: extract(year from order_date)

  - op: derive_column
    name: quarter
    expr: extract(quarter from order_date)

  - op: derive_column
    name: month
    expr: extract(month from order_date)

  - op: derive_column
    name: day_of_week
    expr: extract(dow from order_date)
```

## Tips

### Column Chaining

Derived columns can reference previously derived columns:

```yaml
transforms:
  - op: derive_column
    name: subtotal
    expr: quantity * price

  - op: derive_column
    name: tax
    expr: subtotal * 0.1     # References subtotal

  - op: derive_column
    name: total
    expr: subtotal + tax     # References both
```

### Readable Expressions

For complex expressions, use YAML multiline:

```yaml
- op: derive_column
  name: score
  expr: |
    CASE
      WHEN rating >= 4.5 THEN 'excellent'
      WHEN rating >= 3.5 THEN 'good'
      WHEN rating >= 2.5 THEN 'average'
      ELSE 'poor'
    END
```

### Handle Division by Zero

```yaml
- op: derive_column
  name: rate
  expr: CASE WHEN count > 0 THEN total / count ELSE 0 END
```

## Errors

### Syntax Error

```
Error: Could not parse expression
```

Check expression syntax. Common issues:

- Missing quotes around strings
- Incorrect function syntax
- Unbalanced parentheses

### Type Mismatch

```
Error: Cannot multiply string and integer
```

Cast columns if needed:

```yaml
- op: cast
  columns:
    quantity: int64

- op: derive_column
  name: total
  expr: quantity * price
```

## Related

- [cast](cast.md) - Convert types before calculations
- [fill_null](fill-null.md) - Handle nulls before calculations
- [Expression Language](../../reference/expressions.md) - Full expression reference
