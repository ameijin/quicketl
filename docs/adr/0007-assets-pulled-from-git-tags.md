# 0007: Templates, Terraform modules and the dbt package are pulled from git tags

This record explains how platform assets reach a user. Read it to learn why they are not inside the Python package.

**Status:** Accepted. Templates are implemented on the 2.0 branch (see [0011](0011-copier-template-layout.md)), and the wheel only packages `src/quicketl`, so they stay out of it. Terraform modules and the dbt package are still planned. Date: 2026-10-30.

## Context

Templates, Terraform modules and the dbt package are folders of files. The Python wheel (the installable package file) should stay small (see [0002](0002-platform-first-slim-core.md)). Terraform and dbt already know how to fetch code from git.

## Decision

We will keep these assets as folders in the repo and not ship them in the wheel. Copier, Terraform and dbt pull them from a git tag.

- `templates/` is read by Copier.
- `terraform/modules/` is used by Terraform.
- `dbt/quicketl_toolkit/` is used by dbt (git plus subdirectory).

## Consequences

Positive:

- The wheel stays small.
- Users pin assets to a tag and choose when to upgrade.
- A team can use one Terraform module or the dbt package without the template.

Negative:

- Scaffolding needs network access to the git host.
- Releases need tags that stay stable.
- We must check whether the build backend can exclude these folders from the wheel.
