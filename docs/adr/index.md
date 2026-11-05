# Decisions (ADRs)

An Architecture Decision Record (ADR) is a short page that records one design decision: why we made it, what we chose, and what it costs. Read these pages when you want to know why quicketl is built the way it is.

All records below were agreed on 2026-10-30. Records marked "planned for 2.0" describe the target design. The code does not do this yet.

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-single-repo-single-tool.md) | One repo, one tool: "quick data engineering" | Accepted (slim core, `[pipelines]` and the platform commands implemented on the 2.0 branch) |
| [0002](0002-platform-first-slim-core.md) | Platform-first default with a slim core and a `[pipelines]` extra | Accepted (implemented on the 2.0 branch) |
| [0003](0003-init-wizard.md) | `quicketl init` becomes a wizard | Accepted, amended (implemented on the 2.0 branch) |
| [0004](0004-airflow-on-mwaa.md) | Airflow on MWAA is the default orchestrator | Accepted |
| [0005](0005-first-reference-stack.md) | First reference stack: Snowflake, Terraform, dbt and Airflow | Accepted |
| [0006](0006-native-loaders-and-dbt-tests.md) | Generated projects use native loaders and dbt tests | Accepted (planned for 2.0, not yet implemented) |
| [0007](0007-assets-pulled-from-git-tags.md) | Templates, Terraform modules and the dbt package are pulled from git tags | Accepted (templates implemented on the 2.0 branch; Terraform modules and the dbt package planned) |
| [0008](0008-config-relative-paths.md) | Project-root relative paths with a `--base-dir` override | Accepted (ships in 1.7.0) |
| [0009](0009-release-plan.md) | Release plan: 1.7.0 and 2.0.0, released through a `dev` branch | Accepted |
| [0010](0010-platform-spec.md) | A small, strict platform spec (`platform.yml`) | Accepted (implemented on the 2.0 branch) |
| [0011](0011-copier-template-layout.md) | One Copier configuration picks the template from the spec | Accepted (implemented on the 2.0 branch) |
| [0012](0012-snowflake-template-design.md) | Snowflake template layout and role model | Accepted (implemented on the 2.0 branch; not yet planned against a live account) |

## Record format

Each record has a title, a status, a context, a decision, and the consequences (good and bad). A record is not edited once accepted. A later record supersedes it instead.
