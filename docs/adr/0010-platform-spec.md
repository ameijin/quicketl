# 0010: A small, strict platform spec

This record explains what `platform.yml` holds and why it is kept small. Read it before adding a field to the spec.

**Status:** Accepted (the spec, `quicketl platform init` and `quicketl platform validate` are implemented on the 2.0 branch; scaffolding from it is planned). Date: 2026-10-30.

## Context

Platform templates need one input that describes the platform a team wants (see [0002](0002-platform-first-slim-core.md) and [0005](0005-first-reference-stack.md)). A large spec that mirrors every Terraform and Airflow setting would be hard to learn, would need a change for every new template option, and would duplicate what the generated project already holds.

## Decision

The spec holds only the choices that shape the whole platform:

- the warehouse and environments;
- the data layers, in order, with sources loading into the first one;
- business domains;
- functional roles, as a map of layer to `read` or `write`, optionally limited to some domains;
- the SSO provider and allowed IP ranges;
- raw sources in S3;
- the orchestrator and its default schedule.

Everything else (warehouse sizes, provider settings, account identifiers, DAG details) lives in the generated project.

The spec is strict:

- Unknown keys are errors, so typos are caught.
- Names must be lowercase identifiers, because they become warehouse object names.
- Every reference between sections must point at something the spec defines.

The spec has a `version` field, starting at `"1"`, so the format can change later without guessing.

## Consequences

Positive:

- A new user can read and write a spec in minutes.
- Mistakes are found by `quicketl platform validate` before anything is generated or applied.
- Templates can change their internals without changing the spec.

Negative:

- Teams that want a setting the spec does not hold edit the generated project instead, and `copier update` may then need them to resolve conflicts.
- Strict names may not match an existing naming scheme. Teams with one can rename objects in the generated project.
- Sources only support S3 for now, matching the AWS focus in [0004](0004-airflow-on-mwaa.md).
