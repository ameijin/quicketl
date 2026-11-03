# 0016: Generated projects ship GitHub Actions CI/CD and S3 state

This record explains why platform projects come with GitHub Actions workflows, why their Terraform state must live in S3, and how plans are reviewed before they are applied. Read it before changing the workflows in a template.

**Status:** Accepted (implemented on the 2.0 branch for the Snowflake template; not yet run against a live account or MWAA environment). Date: 2026-11-02.

## Context

Before this, a team that ran `quicketl platform scaffold` got Terraform, dbt and DAGs, but nothing to check or deploy them. Every team would write that pipeline by hand, and differently. The checks quicketl already runs on its own templates (`terraform validate`, `dbt parse`, loading the DAGs) are the same checks a team needs on every pull request.

A deploy pipeline needs shared Terraform state. Without it, each run starts from nothing and tries to create every object again. The template's README told teams to add a backend, but nothing enforced it.

The teams quicketl serves run on AWS, and usually host their code on GitHub.

## Decision

- **Workflows are part of the template.** `.github/workflows/ci.yml` and `deploy.yml` are rendered from the spec (the environments, and the Terraform variables the spec needs), with a Dependabot file for the actions.
- **`ci.yml`, on every pull request:** `terraform fmt`, `init -backend=false` and `validate`; `dbt parse` with the dbt versions MWAA installs; and loading the DAGs with Airflow 3.3.1 and the generated `requirements.txt`. Once the state bucket is configured, it also runs `terraform plan` and shows it in the run summary.
- **`deploy.yml`, on every push to `main`:**
  1. Plan, and save the plan with its provider lock file as a one-day artifact.
  2. If the plan has changes, apply that saved plan in the `terraform` GitHub environment, which the team protects with required reviewers. Applying the saved plan, not a new one, means what runs is what the reviewer read.
  3. Copy `dags/` and `dbt/` to each environment's MWAA bucket, one environment at a time in spec order, each in its own GitHub environment.
- **State lives in S3.** The template declares `backend "s3" {}`. The bucket, region and lock setting come from `backend.hcl` locally and from repository variables in CI. The key is fixed at `<name>/terraform.tfstate`. Locking uses S3 lock files (`use_lockfile`), not DynamoDB, which the Terraform docs mark as deprecated. Terraform 1.11 or later is required.
- **No long-lived cloud keys in GitHub.** AWS access uses OIDC roles scoped to a GitHub environment. Snowflake uses key-pair authentication (`SNOWFLAKE_JWT`), with the private key as an environment secret.
- **Actions are pinned to commit SHAs**, as in quicketl's own workflows.
- **Not automated:** MWAA's `requirements.txt` and startup script. MWAA reads them only when the environment is updated, and an update takes a long time and restarts the environment, so it stays a deliberate manual step.

## Consequences

Positive:

- A new project has the same pull request checks quicketl runs on its templates, from its first commit.
- Every Terraform change is planned on the pull request and applied only after a person approves the same plan.
- `scripts/check_templates.py` lints the rendered workflows with actionlint, so a broken workflow fails quicketl's CI, not a team's first deploy.

Negative:

- `terraform init` now needs `-backend-config=backend.hcl`, even for one person working alone.
- The plan credentials are usable from any pull request branch, because GitHub cannot restrict an environment to pull requests. Teams should give the plan user the least access a plan needs and keep the repository private.
- The saved plan artifact holds every value in plain text, including secrets such as the Okta certificate, for one day.
- The workflows are GitHub Actions only. Teams on GitLab or another CI system get the checks' commands from the README, not a pipeline.
- The workflows have only been linted and rendered, not run against a live Snowflake account, AWS account or MWAA environment.
