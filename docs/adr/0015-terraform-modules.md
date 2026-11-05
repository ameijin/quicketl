# 0015: Terraform lives in modules that templates call

This record explains why the Snowflake Terraform moved into `terraform/modules/` and how generated projects use it. Read it before adding Terraform to a template or a module.

**Status:** Accepted (implemented on the 2.0 branch). Supersedes the "generated code is plain Terraform" part of [0012](0012-snowflake-template-design.md); the naming and role model in 0012 are unchanged. Date: 2026-10-31.

## Context

Phase 3 of the plan asks for Terraform building blocks that teams can use on their own, for example adding only the network policy to an existing platform. The Snowflake template already had that Terraform inline. Keeping both an inline copy and a module copy would mean two places to fix every bug.

[0007](0007-assets-pulled-from-git-tags.md) already says Terraform modules are pulled from git tags, not shipped in the wheel.

## Decision

- **One copy, in modules.** `terraform/modules/` holds `snowflake-platform` (databases, schemas, warehouses, roles, grants), `snowflake-network-policy`, `snowflake-s3-integration` and `snowflake-okta-sso`. Each has pinned provider versions, described variables with validation, outputs, a README and `examples/basic/`.
- **Templates call the modules from git**, pinned to the tag the project was scaffolded from: `git::https://github.com/ameijin/quicketl.git//terraform/modules/<name>?ref=<tag>`. `quicketl platform scaffold` and `update` pass that tag to Copier as `template_ref`, so `quicketl platform update --ref <newer tag>` moves the modules forward too.
- **The generated project keeps the data and the wiring:** `locals.tf` (from the spec), `variables.tf`, `providers.tf` (credentials and preview features stay with the caller) and one module block per part.
- **Modules never configure the provider.** Preview features such as network rules are turned on by the caller, and each module README says which ones it needs.
- **Checks:** `scripts/check_templates.py` validates each module's example and checks its attribute references against the provider schema. It checks rendered projects with their module sources pointed at this checkout, because the release tag may not exist yet.

## Consequences

Positive:

- A bug fix in a module reaches every project that moves to the new tag.
- Teams with an existing platform can use one module without a template.
- Generated projects are short and easy to read.

Negative:

- Teams cannot edit module code in place. To change it, they copy the module into their project and point `source` at the copy, and then they stop getting fixes for it.
- `terraform init` needs network access to GitHub, and the tag must exist. Projects scaffolded from an unreleased ref (for example a test tag) cannot run `terraform init` against GitHub.
- Moving resources into modules changes their Terraform addresses. Nothing was applied before this change, so no state needs moving; later changes to module internals must use `moved` blocks.
