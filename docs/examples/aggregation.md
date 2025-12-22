# Aggregation Pipeline Example

This example demonstrates how to compute metrics, summaries, and roll-ups from transactional data using QuickETL aggregations.

## Overview

**Goal**: Create a sales analytics report with:

- Revenue by region and category
- Order counts and averages
- Top products by revenue

## Sample Data

Create `data/transactions.csv`:

```csv
transaction_id,date,region,category,product,quantity,unit_price,customer_id
T001,2025-01-15,North,Electronics,Widget A,2,29.99,C001
T002,2025-01-15,South,Electronics,Gadget B,1,49.99,C002
T003,2025-01-15,North,Services,Service C,1,99.99,C003
T004,2025-01-16,East,Electronics,Widget A,3,29.99,C004
T005,2025-01-16,West,Hardware,Tool D,2,39.99,C005
T006,2025-01-16,North,Electronics,Gadget B,1,49.99,C001
T007,2025-01-17,South,Services,Service C,2,99.99,C002
T008,2025-01-17,East,Electronics,Widget A,1,29.99,C006
T009,2025-01-17,North,Hardware,Tool D,1,39.99,C003
T010,2025-01-18,West,Electronics,Widget A,4,29.99,C007
T011,2025-01-18,South,Electronics,Gadget B,2,49.99,C008
T012,2025-01-18,North,Services,Service C,1,99.99,C001
```

## Pipeline 1: Regional Summary

Create `pipelines/regional_summary.yml`:

```yaml
name: regional_sales_summary
description: Aggregate sales metrics by region
engine: duckdb

source:
  type: file
  path: data/transactions.csv
  format: csv

transforms:
  # Calculate line totals
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  # Aggregate by region
  - op: aggregate
    group_by: [region]
    aggregations:
      total_revenue: sum(line_total)
      total_orders: count(*)
      total_quantity: sum(quantity)
      avg_order_value: avg(line_total)
      unique_customers: count(distinct customer_id)
      unique_products: count(distinct product)

  # Sort by revenue descending
  - op: sort
    by:
      - column: total_revenue
        order: desc

checks:
  - type: not_null
    columns: [region, total_revenue]
  - type: row_count
    min: 1

sink:
  type: file
  path: output/regional_summary.parquet
  format: parquet
```

### Expected Output

| region | total_revenue | total_orders | total_quantity | avg_order_value | unique_customers | unique_products |
|--------|---------------|--------------|----------------|-----------------|------------------|-----------------|
| North | 319.94 | 5 | 6 | 63.99 | 3 | 4 |
| South | 349.95 | 3 | 5 | 116.65 | 3 | 3 |
| East | 119.96 | 2 | 4 | 59.98 | 2 | 1 |
| West | 199.94 | 2 | 6 | 99.97 | 2 | 2 |

## Pipeline 2: Category by Region

Create `pipelines/category_region.yml`:

```yaml
name: category_region_analysis
description: Cross-tabulation of categories by region
engine: duckdb

source:
  type: file
  path: data/transactions.csv
  format: csv

transforms:
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  # Multi-level grouping
  - op: aggregate
    group_by: [region, category]
    aggregations:
      revenue: sum(line_total)
      orders: count(*)
      avg_quantity: avg(quantity)

  # Sort for readability
  - op: sort
    by:
      - column: region
        order: asc
      - column: revenue
        order: desc

sink:
  type: file
  path: output/category_region.parquet
  format: parquet
```

## Pipeline 3: Time Series Aggregation

Create `pipelines/daily_metrics.yml`:

```yaml
name: daily_sales_metrics
description: Daily aggregated metrics
engine: duckdb

source:
  type: file
  path: data/transactions.csv
  format: csv

transforms:
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  # Aggregate by date
  - op: aggregate
    group_by: [date]
    aggregations:
      daily_revenue: sum(line_total)
      daily_orders: count(*)
      daily_items: sum(quantity)

  # Calculate running total (requires window function support)
  - op: derive_column
    name: cumulative_revenue
    expr: sum(daily_revenue) over (order by date)

  - op: sort
    by:
      - column: date
        order: asc

sink:
  type: file
  path: output/daily_metrics.parquet
  format: parquet
```

## Pipeline 4: Top Products

Create `pipelines/top_products.yml`:

```yaml
name: top_products_analysis
description: Identify best-selling products
engine: duckdb

source:
  type: file
  path: data/transactions.csv
  format: csv

transforms:
  - op: derive_column
    name: line_total
    expr: quantity * unit_price

  - op: aggregate
    group_by: [product, category]
    aggregations:
      total_revenue: sum(line_total)
      units_sold: sum(quantity)
      order_count: count(*)
      avg_unit_price: avg(unit_price)

  # Rank by revenue
  - op: sort
    by:
      - column: total_revenue
        order: desc

  # Keep top 10
  - op: limit
    n: 10

sink:
  type: file
  path: output/top_products.parquet
  format: parquet
```

## Available Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `count(*)` | Count all rows | `orders: count(*)` |
| `count(column)` | Count non-null values | `valid_emails: count(email)` |
| `count(distinct column)` | Count unique values | `customers: count(distinct customer_id)` |
| `sum(column)` | Sum values | `revenue: sum(amount)` |
| `avg(column)` | Average | `avg_order: avg(amount)` |
| `min(column)` | Minimum | `first_order: min(date)` |
| `max(column)` | Maximum | `last_order: max(date)` |
| `stddev(column)` | Standard deviation | `volatility: stddev(price)` |
| `variance(column)` | Variance | `var: variance(returns)` |

## Conditional Aggregation

Use expressions for conditional counting:

```yaml
- op: aggregate
  group_by: [region]
  aggregations:
    total_orders: count(*)
    completed_orders: sum(case when status = 'completed' then 1 else 0 end)
    pending_orders: sum(case when status = 'pending' then 1 else 0 end)
    completion_rate: avg(case when status = 'completed' then 1.0 else 0.0 end)
```

## Percentile Calculations

```yaml
- op: aggregate
  group_by: [category]
  aggregations:
    median_price: percentile_cont(0.5) within group (order by unit_price)
    p95_price: percentile_cont(0.95) within group (order by unit_price)
```

## Running All Pipelines

```bash
# Run all aggregation pipelines
for f in pipelines/*.yml; do
  echo "Running $f..."
  quicketl run "$f"
done
```

## Combining with Joins

Aggregate after enriching with joins:

```yaml
transforms:
  # Join first
  - op: join
    right:
      type: file
      path: data/products.csv
      format: csv
    on: [product_id]
    how: left

  # Then aggregate with joined data
  - op: aggregate
    group_by: [category, subcategory]  # From products table
    aggregations:
      revenue: sum(quantity * unit_price)
      margin: avg((unit_price - cost) / unit_price)
```

## Performance Tips

### 1. Filter Before Aggregating

```yaml
transforms:
  # Filter first
  - op: filter
    predicate: date >= '2025-01-01' AND status = 'completed'

  # Then aggregate (fewer rows)
  - op: aggregate
    group_by: [region]
    aggregations:
      revenue: sum(amount)
```

### 2. Aggregate in Stages

For complex aggregations, break into steps:

```yaml
transforms:
  # First aggregation: daily by region
  - op: aggregate
    group_by: [date, region]
    aggregations:
      daily_revenue: sum(amount)

  # Second aggregation: monthly summary
  - op: derive_column
    name: month
    expr: date_trunc('month', date)

  - op: aggregate
    group_by: [month, region]
    aggregations:
      monthly_revenue: sum(daily_revenue)
```

## Next Steps

- [Cloud ETL Example](cloud-etl.md) - Production cloud pipelines
- [Aggregate Transform Reference](../guides/transforms/operations.md#aggregate)
- [Performance Best Practices](../best-practices/performance.md)
