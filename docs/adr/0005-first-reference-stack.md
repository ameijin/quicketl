# 0005: First reference stack is Snowflake, Terraform, dbt and Airflow

This record explains which platform template is built first. Read it to learn the order of templates.

**Status:** Accepted. Date: 2026-10-30.

## Context

We need one complete template to prove the design before building more. A recent engagement moved a Redshift Serverless warehouse to Snowflake and gives a real model to follow.

## Decision

We will build the first template for Snowflake with Terraform (infrastructure), dbt (transforms and tests) and Airflow (orchestration, see [0004](0004-airflow-on-mwaa.md)), modeled on that engagement. Databricks and Redshift Serverless templates follow.

## Consequences

Positive:

- The first template is based on proven real work.
- Later templates can reuse its structure.

Negative:

- Databricks and Redshift teams wait for their templates.
- The first design may lean toward Snowflake choices and need changes when other warehouses arrive.
