# Best Practices

This section covers best practices for building reliable, maintainable, and performant ETLX pipelines.

## Overview

| Guide | Description |
|-------|-------------|
| [Pipeline Design](pipeline-design.md) | Structuring and organizing pipelines |
| [Error Handling](error-handling.md) | Dealing with failures gracefully |
| [Performance](performance.md) | Optimizing pipeline execution |
| [Testing](testing.md) | Testing strategies for data pipelines |
| [Production](production.md) | Running pipelines in production |

## Quick Tips

### Pipeline Design

- **Keep pipelines focused**: One pipeline = one responsibility
- **Use descriptive names**: `daily_sales_by_region` not `pipeline1`
- **Add descriptions**: Document what the pipeline does and why
- **Filter early**: Reduce data volume before expensive operations

### Error Handling

- **Use quality checks**: Validate data before writing
- **Set appropriate thresholds**: Not all checks need 100% pass rate
- **Log context**: Include dates, row counts, durations
- **Alert on failures**: Don't let failures go unnoticed

### Performance

- **Choose the right backend**: DuckDB for local, Spark for distributed
- **Use Parquet format**: Columnar, compressed, fast
- **Select only needed columns**: Reduce memory usage
- **Batch operations**: Minimize I/O overhead

### Testing

- **Test with sample data**: Create representative test datasets
- **Validate schemas**: Ensure output matches expectations
- **Test edge cases**: Empty files, NULLs, duplicates
- **Use CI/CD**: Automate validation on every change

### Production

- **Use environment variables**: Never hardcode credentials
- **Monitor pipelines**: Track duration, row counts, errors
- **Set up alerting**: Get notified of failures
- **Document runbooks**: Know how to recover from failures

## Common Patterns

### Idempotent Pipelines

Pipelines that can be safely re-run:

```yaml
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: replace  # Replaces existing data for the partition

# Or use merge for upsert behavior
sink:
  type: database
  connection: postgres
  table: analytics.daily_metrics
  mode: merge
  merge_keys: [date, region]  # Unique identifier
```

### Incremental Loading

Process only new data:

```yaml
name: incremental_load
source:
  type: database
  connection: postgres
  query: |
    SELECT * FROM events
    WHERE created_at >= '${LAST_RUN}'
      AND created_at < '${CURRENT_RUN}'
```

### Data Validation Gates

Ensure data quality before loading:

```yaml
transforms:
  - op: derive_column
    name: total
    expr: quantity * price

checks:
  # Critical checks - must pass
  - check: not_null
    columns: [id, customer_id, total]

  - check: unique
    columns: [id]

  # Warning checks - log but don't fail
  - check: expression
    expr: email LIKE '%@%.%'
    threshold: 0.95  # 95% must pass

sink:
  # Only write if checks pass
  type: file
  path: output/validated_data.parquet
```

### Environment-Specific Configuration

Use variables for environment differences:

```yaml
name: env_aware_pipeline
source:
  type: file
  path: ${DATA_PATH}/input/*.parquet
  format: parquet

sink:
  type: database
  connection: ${DATABASE_CONNECTION}
  table: ${SCHEMA}.output_table
```

```bash
# Development
DATA_PATH=./data DATABASE_CONNECTION=postgres_dev SCHEMA=dev \
  quicketl run pipeline.yml

# Production
DATA_PATH=s3://bucket DATABASE_CONNECTION=postgres_prod SCHEMA=prod \
  quicketl run pipeline.yml
```

## Anti-Patterns to Avoid

### Don't

```yaml
# Avoid: No description
name: p1

# Avoid: SELECT * when you don't need all columns
transforms:
  - op: select
    columns: ["*"]

# Avoid: Filtering after expensive operations
transforms:
  - op: aggregate
    group_by: [region]
    aggregations:
      total: sum(amount)
  - op: filter  # Should be BEFORE aggregate
    predicate: date >= '2025-01-01'
```

### Do

```yaml
# Good: Descriptive name and documentation
name: daily_regional_sales_summary
description: |
  Aggregates daily sales by region for the analytics dashboard.
  Runs daily at 6 AM UTC.

# Good: Select only what you need
transforms:
  - op: select
    columns: [id, date, region, amount]

# Good: Filter early
transforms:
  - op: filter
    predicate: date >= '2025-01-01'
  - op: aggregate
    group_by: [region]
    aggregations:
      total: sum(amount)
```

## Related

- [Pipeline Design](pipeline-design.md) - Detailed design guidance
- [Examples](../examples/index.md) - Complete working examples
- [Troubleshooting](../reference/troubleshooting.md) - Common issues
