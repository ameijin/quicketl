# Pipeline Design Best Practices

Guidelines for designing clean, maintainable, and efficient ETLX pipelines.

## Naming Conventions

### Pipeline Names

Use descriptive, action-oriented names:

```yaml
# Good
name: extract_daily_orders
name: transform_sales_metrics
name: load_customer_warehouse

# Avoid
name: pipeline1
name: test
name: data
```

### File Organization

```
pipelines/
├── extract/
│   ├── orders.yml
│   ├── products.yml
│   └── customers.yml
├── transform/
│   ├── daily_metrics.yml
│   └── weekly_rollup.yml
├── load/
│   └── warehouse.yml
└── quality/
    └── data_validation.yml
```

### Variable Names

Use SCREAMING_SNAKE_CASE for variables:

```yaml
source:
  type: file
  path: data/sales_${DATE}.csv
  format: csv

# Run with: --var DATE=2025-01-15
```

## Single Responsibility

Each pipeline should do one thing well.

### Don't: Monolithic Pipeline

```yaml
# Avoid: Too many responsibilities
name: do_everything
transforms:
  # Extract from multiple sources
  - op: join ...
  - op: join ...
  # Transform
  - op: filter ...
  - op: aggregate ...
  - op: aggregate ...
  # Multiple outputs (not supported)
```

### Do: Focused Pipelines

```yaml
# Pipeline 1: Extract and stage
name: extract_orders
source:
  type: database
  connection: postgres
  table: orders
sink:
  type: file
  path: staging/orders.parquet
```

```yaml
# Pipeline 2: Transform
name: transform_metrics
source:
  type: file
  path: staging/orders.parquet
transforms:
  - op: aggregate ...
sink:
  type: file
  path: processed/metrics.parquet
```

```yaml
# Pipeline 3: Load
name: load_warehouse
source:
  type: file
  path: processed/metrics.parquet
sink:
  type: database
  connection: snowflake
  table: analytics.metrics
```

## Documentation

### Pipeline-Level Documentation

```yaml
name: daily_revenue_report
description: |
  Generates daily revenue metrics by region and category.

  Data Sources:
  - orders: Transactional order data from PostgreSQL
  - products: Product catalog from S3

  Output:
  - Aggregated revenue metrics for dashboard consumption

  Schedule: Daily at 6 AM UTC
  Owner: data-team@company.com
```

### Transform Comments

YAML supports comments - use them:

```yaml
transforms:
  # Remove test orders (order_id starting with 'TEST')
  - op: filter
    predicate: NOT order_id LIKE 'TEST%'

  # Calculate gross margin
  # Formula: (revenue - cost) / revenue
  - op: derive_column
    name: gross_margin
    expr: (amount - cost) / amount

  # Aggregate to daily level for dashboard
  - op: aggregate
    group_by: [date, region]
    aggregations:
      revenue: sum(amount)
```

## Transform Ordering

### Filter Early

Reduce data volume before expensive operations:

```yaml
transforms:
  # Good: Filter first
  - op: filter
    predicate: status = 'completed' AND date >= '2025-01-01'

  - op: join
    right: ...  # Joins fewer rows

  - op: aggregate  # Aggregates fewer rows
    group_by: ...
```

### Select Early

Only keep columns you need:

```yaml
transforms:
  - op: select
    columns: [id, date, amount, category]

  # Subsequent operations work with fewer columns
  - op: aggregate
    group_by: [category]
    aggregations:
      total: sum(amount)
```

### Logical Order

1. **Filter** - Remove unwanted rows
2. **Select** - Keep only needed columns
3. **Derive** - Create calculated columns
4. **Join** - Combine with other data
5. **Aggregate** - Summarize
6. **Sort** - Order results
7. **Limit** - Truncate if needed

## Quality Gates

### Critical vs Warning Checks

```yaml
checks:
  # Critical: Pipeline fails if these don't pass
  - check: not_null
    columns: [id, amount]

  - check: unique
    columns: [id]

  # Warning: Log but don't fail (95% threshold)
  - check: expression
    expr: amount > 0
    threshold: 0.95
```

### Meaningful Checks

```yaml
checks:
  # Check data freshness
  - check: expression
    expr: date >= current_date - interval '2 days'

  # Check referential integrity
  - check: expression
    expr: customer_id IS NOT NULL

  # Check business rules
  - check: expression
    expr: quantity > 0 AND quantity < 1000

  # Check for expected volume
  - check: row_count
    min: 100
    max: 1000000
```

## Configuration Patterns

### Environment Variables

Externalize environment-specific values:

```yaml
name: ${PIPELINE_NAME:-default_pipeline}
engine: ${ENGINE:-duckdb}

source:
  type: file
  path: ${INPUT_PATH}
  format: parquet

sink:
  type: database
  connection: ${DB_CONNECTION}
  table: ${SCHEMA}.${TABLE}
```

### Defaults

Use defaults for optional values:

```yaml
source:
  type: file
  path: ${INPUT_PATH:-data/default.parquet}
  format: ${FORMAT:-parquet}
```

### Modular Configuration

Split large pipelines into includes (future feature):

```yaml
# base.yml
name: base_pipeline
engine: duckdb

# pipeline.yml
extends: base.yml
source: ...
transforms: ...
```

## Anti-Patterns

### Avoid: Wide SELECT *

```yaml
# Bad: Selects all columns
transforms:
  - op: select
    columns: ["*"]

# Good: Explicit columns
transforms:
  - op: select
    columns: [id, name, amount, date]
```

### Avoid: Late Filtering

```yaml
# Bad: Filter after expensive operations
transforms:
  - op: aggregate
    group_by: [region, date]
    aggregations:
      total: sum(amount)
  - op: filter
    predicate: date >= '2025-01-01'  # Should be first!

# Good: Filter early
transforms:
  - op: filter
    predicate: date >= '2025-01-01'
  - op: aggregate
    group_by: [region, date]
    aggregations:
      total: sum(amount)
```

### Avoid: Hardcoded Values

```yaml
# Bad: Hardcoded
source:
  type: file
  path: /home/user/data/sales_2025-01-15.csv

# Good: Parameterized
source:
  type: file
  path: ${DATA_DIR}/sales_${DATE}.csv
```

### Avoid: No Quality Checks

```yaml
# Bad: No validation
sink:
  type: database
  connection: postgres
  table: production.critical_table

# Good: Validate before writing
checks:
  - check: not_null
    columns: [id]
  - check: row_count
    min: 1
sink:
  type: database
  connection: postgres
  table: production.critical_table
```

## Related

- [Error Handling](error-handling.md) - Handling failures
- [Performance](performance.md) - Optimization tips
- [Examples](../examples/index.md) - Complete examples
