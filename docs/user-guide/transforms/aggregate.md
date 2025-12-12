# aggregate

Group data and compute summary statistics.

## Usage

```yaml
- op: aggregate
  group_by: [region]
  aggs:
    total_sales: sum(amount)
    order_count: count(*)
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `group_by` | Yes | `list[str]` | Columns to group by |
| `aggs` | Yes | `dict[str, str]` | Output column → aggregation expression |

## Examples

### Basic Aggregation

```yaml
- op: aggregate
  group_by: [category]
  aggs:
    total_sales: sum(amount)
```

### Multiple Aggregations

```yaml
- op: aggregate
  group_by: [region]
  aggs:
    total_sales: sum(amount)
    avg_order: avg(amount)
    min_order: min(amount)
    max_order: max(amount)
    order_count: count(*)
```

### Multiple Group Columns

```yaml
- op: aggregate
  group_by: [region, category, year]
  aggs:
    total: sum(amount)
```

### Count Distinct

```yaml
- op: aggregate
  group_by: [region]
  aggs:
    unique_customers: count(customer_id)
    total_orders: count(*)
```

## Input/Output Example

**Input Data:**

| id | region | category | amount |
|----|--------|----------|--------|
| 1 | North | Electronics | 100 |
| 2 | North | Electronics | 200 |
| 3 | North | Home | 50 |
| 4 | South | Electronics | 150 |
| 5 | South | Home | 75 |

**Transform:**

```yaml
- op: aggregate
  group_by: [region, category]
  aggs:
    total_sales: sum(amount)
    order_count: count(*)
    avg_order: avg(amount)
```

**Output Data:**

| region | category | total_sales | order_count | avg_order |
|--------|----------|-------------|-------------|-----------|
| North | Electronics | 300 | 2 | 150.0 |
| North | Home | 50 | 1 | 50.0 |
| South | Electronics | 150 | 1 | 150.0 |
| South | Home | 75 | 1 | 75.0 |

## Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sum(col)` | Sum of values | `sum(amount)` |
| `avg(col)` | Average (mean) | `avg(amount)` |
| `mean(col)` | Same as avg | `mean(amount)` |
| `min(col)` | Minimum value | `min(amount)` |
| `max(col)` | Maximum value | `max(amount)` |
| `count(*)` | Count all rows | `count(*)` |
| `count(col)` | Count non-null | `count(customer_id)` |

## Python API

```python
from etlx.config.transforms import AggregateTransform

transform = AggregateTransform(
    group_by=["region", "category"],
    aggs={
        "total_sales": "sum(amount)",
        "order_count": "count(*)",
        "avg_order": "avg(amount)",
    }
)
```

## Common Patterns

### Daily Summary

```yaml
transforms:
  - op: derive_column
    name: date
    expr: date_trunc('day', created_at)

  - op: aggregate
    group_by: [date]
    aggs:
      daily_sales: sum(amount)
      daily_orders: count(*)
```

### Regional Breakdown

```yaml
- op: aggregate
  group_by: [region]
  aggs:
    total_sales: sum(amount)
    avg_order_value: avg(amount)
    customer_count: count(customer_id)
    order_count: count(*)
```

### Product Performance

```yaml
- op: aggregate
  group_by: [product_id, product_name]
  aggs:
    units_sold: sum(quantity)
    revenue: sum(amount)
    orders: count(*)
```

### Time Series Aggregation

```yaml
transforms:
  # Extract time components
  - op: derive_column
    name: year
    expr: extract(year from date)

  - op: derive_column
    name: month
    expr: extract(month from date)

  # Aggregate by time period
  - op: aggregate
    group_by: [year, month]
    aggs:
      monthly_sales: sum(amount)
```

## Pre-Aggregation Transforms

Often you need to prepare data before aggregating:

```yaml
transforms:
  # 1. Clean data
  - op: filter
    predicate: amount > 0 AND status != 'cancelled'

  # 2. Create metrics
  - op: derive_column
    name: net_amount
    expr: amount - COALESCE(discount, 0)

  # 3. Aggregate
  - op: aggregate
    group_by: [region]
    aggs:
      gross_sales: sum(amount)
      net_sales: sum(net_amount)
      total_discount: sum(COALESCE(discount, 0))
```

## Tips

### Aggregating Derived Columns

Create columns before aggregating them:

```yaml
transforms:
  - op: derive_column
    name: revenue
    expr: quantity * unit_price

  - op: aggregate
    group_by: [category]
    aggs:
      total_revenue: sum(revenue)
```

### Handling Nulls

Aggregation functions ignore nulls by default:

```yaml
# If some amounts are null:
# sum() ignores nulls
# count(amount) counts non-null only
# count(*) counts all rows
```

To include nulls:

```yaml
transforms:
  - op: fill_null
    columns:
      amount: 0

  - op: aggregate
    group_by: [region]
    aggs:
      total: sum(amount)
```

### Output Column Names

Choose descriptive names:

```yaml
aggs:
  total_revenue_usd: sum(amount)      # Good
  avg_order_value: avg(amount)        # Good
  sum_amount: sum(amount)             # Less descriptive
```

## Performance

### Reduce Data First

Filter and select before aggregating:

```yaml
transforms:
  - op: filter
    predicate: date >= '2025-01-01'

  - op: select
    columns: [region, amount]

  - op: aggregate
    group_by: [region]
    aggs:
      total: sum(amount)
```

### Group Cardinality

Be mindful of unique group combinations:

- Low cardinality (region: 5 values) → Fast
- High cardinality (customer_id: 1M values) → Slower, more memory

## Errors

### Invalid Aggregation Function

```
Error: Unknown aggregation function 'median'
```

Use supported functions: `sum`, `avg`, `mean`, `min`, `max`, `count`.

### Column Not in Group By

```
Error: Column 'name' must appear in GROUP BY or be aggregated
```

Every non-aggregated column must be in `group_by`.

## Related

- [derive_column](derive-column.md) - Create columns before aggregating
- [filter](filter.md) - Filter before aggregating
- [sort](sort.md) - Sort aggregated results
