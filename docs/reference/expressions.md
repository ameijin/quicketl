# Expression Language Reference

ETLX uses SQL expressions for filters, derived columns, and quality checks. This reference covers the supported expression syntax.

## Basic Syntax

Expressions are written as SQL-compatible strings:

```yaml
transforms:
  - op: filter
    predicate: amount > 100

  - op: derive_column
    name: total
    expr: quantity * price
```

## Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `status = 'active'` |
| `!=` or `<>` | Not equal | `status != 'deleted'` |
| `>` | Greater than | `amount > 100` |
| `>=` | Greater than or equal | `amount >= 100` |
| `<` | Less than | `amount < 1000` |
| `<=` | Less than or equal | `amount <= 1000` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Logical AND | `status = 'active' AND amount > 0` |
| `OR` | Logical OR | `status = 'pending' OR status = 'active'` |
| `NOT` | Logical NOT | `NOT status = 'deleted'` |

### Arithmetic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `price + tax` |
| `-` | Subtraction | `gross - discount` |
| `*` | Multiplication | `quantity * price` |
| `/` | Division | `total / count` |
| `%` | Modulo | `id % 10` |

### String Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `\|\|` | Concatenation | `first_name \|\| ' ' \|\| last_name` |
| `LIKE` | Pattern match | `email LIKE '%@gmail.com'` |
| `ILIKE` | Case-insensitive pattern | `name ILIKE '%smith%'` |

## NULL Handling

### Check for NULL

```yaml
- op: filter
  predicate: email IS NOT NULL

- op: filter
  predicate: phone IS NULL
```

### COALESCE

Return first non-NULL value:

```yaml
- op: derive_column
  name: display_name
  expr: coalesce(nickname, first_name, 'Unknown')
```

### NULLIF

Return NULL if values equal:

```yaml
- op: derive_column
  name: safe_divisor
  expr: amount / nullif(count, 0)
```

## CASE Expressions

### Simple CASE

```yaml
- op: derive_column
  name: status_label
  expr: |
    case status
      when 'A' then 'Active'
      when 'P' then 'Pending'
      when 'D' then 'Deleted'
      else 'Unknown'
    end
```

### Searched CASE

```yaml
- op: derive_column
  name: size_category
  expr: |
    case
      when amount < 100 then 'Small'
      when amount < 1000 then 'Medium'
      when amount < 10000 then 'Large'
      else 'Enterprise'
    end
```

## String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `upper(s)` | Uppercase | `upper(name)` |
| `lower(s)` | Lowercase | `lower(email)` |
| `trim(s)` | Remove whitespace | `trim(name)` |
| `ltrim(s)` | Left trim | `ltrim(name)` |
| `rtrim(s)` | Right trim | `rtrim(name)` |
| `length(s)` | String length | `length(description)` |
| `substring(s, start, len)` | Extract substring | `substring(phone, 1, 3)` |
| `replace(s, old, new)` | Replace text | `replace(phone, '-', '')` |
| `concat(s1, s2, ...)` | Concatenate | `concat(first, ' ', last)` |
| `split_part(s, delim, n)` | Split and get part | `split_part(email, '@', 2)` |

### Examples

```yaml
transforms:
  - op: derive_column
    name: email_domain
    expr: split_part(email, '@', 2)

  - op: derive_column
    name: full_name
    expr: concat(upper(substring(first_name, 1, 1)), lower(substring(first_name, 2, 100)), ' ', last_name)

  - op: derive_column
    name: clean_phone
    expr: replace(replace(phone, '-', ''), ' ', '')
```

## Numeric Functions

| Function | Description | Example |
|----------|-------------|---------|
| `abs(n)` | Absolute value | `abs(balance)` |
| `round(n, d)` | Round to decimals | `round(amount, 2)` |
| `floor(n)` | Round down | `floor(amount)` |
| `ceil(n)` | Round up | `ceil(amount)` |
| `sqrt(n)` | Square root | `sqrt(value)` |
| `power(n, p)` | Power | `power(base, 2)` |
| `mod(n, d)` | Modulo | `mod(id, 10)` |
| `greatest(a, b, ...)` | Maximum of values | `greatest(a, b, c)` |
| `least(a, b, ...)` | Minimum of values | `least(a, b, c)` |

### Examples

```yaml
transforms:
  - op: derive_column
    name: rounded_amount
    expr: round(amount, 2)

  - op: derive_column
    name: percentage
    expr: round(part / total * 100, 1)

  - op: derive_column
    name: capped_value
    expr: least(amount, 1000)
```

## Date and Time Functions

| Function | Description | Example |
|----------|-------------|---------|
| `current_date` | Today's date | `current_date` |
| `current_timestamp` | Current timestamp | `current_timestamp` |
| `date(ts)` | Extract date | `date(created_at)` |
| `year(d)` | Extract year | `year(order_date)` |
| `month(d)` | Extract month | `month(order_date)` |
| `day(d)` | Extract day | `day(order_date)` |
| `hour(ts)` | Extract hour | `hour(created_at)` |
| `minute(ts)` | Extract minute | `minute(created_at)` |
| `extract(part from d)` | Extract date part | `extract(dow from date)` |
| `date_trunc(part, d)` | Truncate date | `date_trunc('month', date)` |
| `date_diff(part, d1, d2)` | Date difference | `date_diff('day', start, end)` |

### Date Parts

- `year`, `quarter`, `month`, `week`, `day`
- `hour`, `minute`, `second`
- `dow` (day of week), `doy` (day of year)

### Examples

```yaml
transforms:
  - op: derive_column
    name: order_month
    expr: date_trunc('month', order_date)

  - op: derive_column
    name: days_since_signup
    expr: date_diff('day', signup_date, current_date)

  - op: derive_column
    name: is_weekend
    expr: extract(dow from date) in (0, 6)

  - op: filter
    predicate: order_date >= current_date - interval '30 days'
```

## Aggregate Functions

Used in `aggregate` transforms:

| Function | Description | Example |
|----------|-------------|---------|
| `count(*)` | Count rows | `count(*)` |
| `count(col)` | Count non-NULL | `count(email)` |
| `count(distinct col)` | Count unique | `count(distinct customer_id)` |
| `sum(col)` | Sum values | `sum(amount)` |
| `avg(col)` | Average | `avg(amount)` |
| `min(col)` | Minimum | `min(date)` |
| `max(col)` | Maximum | `max(date)` |
| `stddev(col)` | Standard deviation | `stddev(amount)` |
| `variance(col)` | Variance | `variance(amount)` |

### Examples

```yaml
- op: aggregate
  group_by: [category]
  aggregations:
    total_revenue: sum(amount)
    avg_order: avg(amount)
    order_count: count(*)
    unique_customers: count(distinct customer_id)
    first_order: min(order_date)
    last_order: max(order_date)
```

## Conditional Aggregation

```yaml
- op: aggregate
  group_by: [region]
  aggregations:
    total_orders: count(*)
    completed_orders: sum(case when status = 'completed' then 1 else 0 end)
    completion_rate: avg(case when status = 'completed' then 1.0 else 0.0 end)
    high_value_revenue: sum(case when amount > 1000 then amount else 0 end)
```

## IN and BETWEEN

### IN Operator

```yaml
- op: filter
  predicate: status IN ('active', 'pending', 'review')

- op: filter
  predicate: category NOT IN ('test', 'internal')
```

### BETWEEN Operator

```yaml
- op: filter
  predicate: amount BETWEEN 100 AND 1000

- op: filter
  predicate: date BETWEEN '2025-01-01' AND '2025-12-31'
```

## Type Casting

### CAST Function

```yaml
- op: derive_column
  name: amount_str
  expr: cast(amount as varchar)

- op: derive_column
  name: amount_int
  expr: cast(amount as integer)
```

### Shorthand (PostgreSQL-style)

```yaml
- op: derive_column
  name: amount_int
  expr: amount::integer
```

## Backend-Specific Functions

Some functions are backend-specific. Check backend documentation:

### DuckDB

```yaml
- op: derive_column
  name: json_value
  expr: json_extract(data, '$.name')
```

### BigQuery

```yaml
- op: derive_column
  name: json_value
  expr: JSON_EXTRACT_SCALAR(data, '$.name')
```

## Multi-line Expressions

For complex expressions, use YAML multi-line syntax:

```yaml
- op: derive_column
  name: customer_tier
  expr: |
    case
      when lifetime_value >= 10000 then 'Platinum'
      when lifetime_value >= 5000 then 'Gold'
      when lifetime_value >= 1000 then 'Silver'
      else 'Bronze'
    end

- op: filter
  predicate: |
    status = 'active'
    AND created_at >= current_date - interval '30 days'
    AND (amount > 100 OR is_premium = true)
```

## Related

- [Filter Transform](../user-guide/transforms/filter.md)
- [Derive Column Transform](../user-guide/transforms/derive-column.md)
- [Aggregate Transform](../user-guide/transforms/aggregate.md)
