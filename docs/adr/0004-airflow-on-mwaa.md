# 0004: Airflow on MWAA as the default orchestrator

This record explains which orchestrator generated platforms use by default. Read it if you wonder why Dagster is not offered first.

**Status:** Accepted. Date: 2026-10-30.

## Context

Target teams run on AWS. A generated platform needs a scheduler to load data and run dbt. Amazon Managed Workflows for Apache Airflow (MWAA) is the managed Airflow service on AWS. quicketl already has Airflow DAG generation.

## Decision

We will use Airflow on MWAA as the default orchestrator. We will add Dagster only when a team needs it.

## Consequences

Positive:

- One orchestrator to template, test and document.
- It matches the AWS-based teams we serve and reuses existing Airflow generation code.

Negative:

- Teams that use another orchestrator get no template at first.
- MWAA ties the default stack to AWS.
