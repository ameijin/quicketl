# 0012: Snowflake template layout and role model

This record explains how the Snowflake template names objects and grants access. Read it before changing `templates/snowflake-airflow/terraform/`.

**Status:** Accepted (implemented on the 2.0 branch; not yet planned against a live account). Date: 2026-10-30.

## Context

The first template ([0005](0005-first-reference-stack.md)) must turn a [platform spec](0010-platform-spec.md) into Snowflake objects and grants. Teams will edit the generated Terraform, and `quicketl platform update` will merge template changes into it, so the code must be easy to read and change.

## Decision

- **The spec becomes data, not code.** Copier renders the spec into one `locals.tf`. Every other file is plain Terraform that loops over those locals with `for_each`. Spec changes touch one file, and template changes do not clash with spec changes.
- **One database per environment and layer** (`<PREFIX>_<ENV>_<LAYER>`), **one schema per domain** in each. Environments and layers are the main access boundaries, and a database boundary makes them hard to cross by mistake.
- **Access roles per schema, functional roles per environment.** `_R` and `_W` access roles hold privileges on one schema, and `_W` includes `_R`. Functional roles from the spec get access roles and their environment's warehouse, and roll up to `SYSADMIN`. People and services only get functional roles.
- **Managed access schemas,** so all grants stay in Terraform.
- **One warehouse per environment,** XSMALL unless `warehouse_sizes` says otherwise. Sizes stay out of the spec ([0010](0010-platform-spec.md)).
- **The network policy is created but not attached.** Attaching it to the account can lock out other teams and the person running Terraform. Attaching is a manual, deliberate step.
- **Preview features are turned on only when used.** In provider 2.22, network rules and the AWS storage integration are preview features.
- **Credentials only from environment variables.** The provider block holds no account names or keys.

## Consequences

Positive:

- Grants follow one pattern, so audits and changes are predictable.
- The generated code is ordinary Terraform that teams can read without knowing quicketl.

Negative:

- Many roles: two per schema. A spec with 2 environments, 3 layers and 4 domains creates 48 access roles.
- Account roles are used instead of database roles, which are scoped more tightly but are harder to grant across databases. This may change after the reference engagement is compared.
- `OKTA_PROVISIONER` is an account-wide name. Two platforms in one account would both try to manage it.
- Checked with `terraform validate` and a schema reference check only. `terraform plan` against a sandbox account is still needed.
