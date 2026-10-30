# 0001: Single repo, single tool

This record explains why quicketl is one repository and one tool, now described as "quick data engineering". Read it to understand why platform features live next to the ETL code.

**Status:** Accepted (planned for 2.0, not yet implemented). Date: 2026-10-30.

This record supersedes the earlier idea of a separate `quickplatform` repository.

## Context

The main user is a senior data engineer who sets up and standardizes data platforms for enterprise teams on Snowflake, Databricks and Redshift on AWS. Most of that work is infrastructure, roles, orchestration and dbt. Local data review, ETL and proofs of concept (POCs) come up only now and then.

One idea was to put platform work in a sibling repo called `quickplatform`. That means two tools to install, version and document.

## Decision

We will keep everything in the `quicketl` repo. The PyPI package name stays `quicketl`. The README and docs will describe it as a "quick data engineering toolkit". ETL is one capability inside it.

## Consequences

Positive:

- One install, one version number and one docs site.
- Platform and pipeline features can share code, such as config loading and the command line.

Negative:

- The repo grows to hold Python code, Copier templates, Terraform modules and a dbt package.
- The name `quicketl` no longer describes the whole tool. We accept this to keep the existing PyPI package and its users.
