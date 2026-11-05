# 0013: dbt project layout in the Snowflake template

This record explains how the generated dbt project decides where models build, and which dbt version it targets. Read it before changing `templates/snowflake-airflow/dbt/`.

**Status:** Accepted (implemented on the 2.0 branch; not yet built against a live account). Date: 2026-10-31.

## Context

The Terraform in [0012](0012-snowflake-template-design.md) creates one database per environment and layer and one schema per domain, and grants write access only on those domain schemas. dbt models must build in exactly those places.

Copier renders one template file to at most one output file. It cannot write one model per source or one folder per domain from a list in the spec.

On 2026-10-31, dbt printed that "dbt v2 is available, and is the default for new installations". On PyPI, the latest stable `dbt-core` is 1.12.6; 2.0 is a release candidate (2.0.0rc9). `dbt-snowflake` 1.12.4 requires `dbt-core<2.0`.

## Decision

- **Folders decide placement.** A model in `models/<layer>/<domain>/` builds in database `<PREFIX>_<TARGET>_<LAYER>`, schema `<DOMAIN>`. The `generate_database_name` and `generate_schema_name` macros do this, reading the layout from `vars` in `dbt_project.yml`, which Copier renders from the spec. An explicit `+database` or `+schema` config still wins.
- **dbt target names are the spec's environments,** so `--target prod` builds in the prod databases.
- **Generate sources, not models.** One `_sources.yml` lists every spec source, grouped by domain, pointing at the landing layer. One example model shows the pattern. Teams write the rest.
- **Target dbt Core 1.12 with `dbt-snowflake` 1.12 from PyPI.** It is the stable line the Snowflake adapter supports and installs with pip, which is how MWAA installs packages. We revisit dbt v2 once `dbt-snowflake` supports it.
- **Credentials only from environment variables,** with key-pair auth (`private_key`).

## Consequences

Positive:

- Teams create folders as they need them; no per-folder config to keep in step with the spec.
- A spec change (new domain or layer) only changes `vars`, which `quicketl platform update` rewrites.

Negative:

- A model outside `models/<layer>/<domain>/` builds in `PUBLIC` and fails, because Terraform grants nothing there. The check script fails if a generated model lands there, but a team's own misplaced model fails only when it runs.
- An empty project (no sources) prints one dbt warning about an unused `models.<name>` config path until the first model exists.
- Moving to dbt v2 later will need its own change and testing.
