# 0006: Native loaders and dbt tests by default

This record explains how generated projects load and test data. Read it to learn why generated projects do not need quicketl when they run.

**Status:** Accepted (implemented for Snowflake on the 2.0 branch: `COPY INTO` from an Airflow DAG, then `dbt build`; see [0014](0014-airflow-on-mwaa-template.md). Databricks and Redshift come with their templates). Date: 2026-10-30.

## Context

Mature tools already load and test data well. A generated project that needs quicketl at runtime adds a dependency and a new thing to operate.

## Decision

We will have generated projects use native loaders and dbt tests by default:

| Warehouse | Loader |
|-----------|--------|
| Snowflake | `COPY INTO` or Snowpipe |
| Databricks | Auto Loader |
| Redshift | `COPY` |

A quicketl pipeline task is an option, never a requirement. Generated projects have no runtime dependency on quicketl.

## Consequences

Positive:

- Loading runs inside the warehouse, close to the data.
- Teams can drop quicketl after scaffolding and the project keeps working.

Negative:

- We must write and maintain templates for each warehouse's loader.
- Teams that want quicketl features at runtime must opt in.
