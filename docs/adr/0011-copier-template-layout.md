# 0011: One Copier configuration picks the template from the spec

This record explains how `quicketl platform scaffold` finds and versions templates. Read it before adding a template or changing `copier.yml`.

**Status:** Accepted (implemented on the 2.0 branch). Date: 2026-10-30.

## Context

[0007](0007-assets-pulled-from-git-tags.md) keeps templates as folders in this repo, pulled from a git tag. We use Copier (version 9.19) to render them, because it can also update a generated project when the template changes.

Copier expects one template per git repo, because `copier update` follows the repo's tags. We want several templates (`snowflake-airflow` first, then Databricks and Redshift Serverless) in one repo.

Copier lets the `_subdirectory` setting in `copier.yml` use answers. We tested this with Copier 9.19.1 in a throwaway repo. A templated `_subdirectory` picked the right folder, a whole spec passed as one `yaml` answer rendered nested lists, and `copier update` to a newer tag applied template changes and recorded the new tag.

## Decision

- **One `copier.yml` at the repo root.** Its `_subdirectory` is `templates/{{ spec.warehouse.type }}-{{ spec.orchestrator.type }}`, so the spec chooses the template.
- **The spec is one answer.** `quicketl platform scaffold` validates `platform.yml` and passes it to Copier as the `spec` answer. Templates read `spec.name`, `spec.domains` and so on.
- **Templates are versioned by quicketl's release tags.** Scaffold and update default to the tag matching the installed quicketl (`v<version>`), so the CLI that checked the spec and the template that reads it come from the same release. `--ref` picks another tag.
- **Copier is a core dependency** (`copier>=9.19,<10`). It and its dependencies add about 8 MB. A core install of the built wheel measures about 33 MB in a clean Python 3.12 environment.
- **Templates never run Copier tasks.** quicketl passes `unsafe=False`, so a template cannot run commands on the user's machine.

## Consequences

Positive:

- One tag covers every template, the CLI and the spec format.
- Adding a template is adding a folder under `templates/` and its name to `AVAILABLE_TEMPLATES`.
- Generated projects can take template fixes with `quicketl platform update`.

Negative:

- Scaffolding and updating need `git` installed.
- `quicketl platform update` needs the project in git with everything committed. Copier refuses to update a project with uncommitted changes.
- Tags must be valid PEP 440 versions (`v2.0.0`, not `v2.0.0-test`). Copier reads the recorded tag as a version and cannot update from one it does not understand.
- A template change that only one template needs still creates a new tag for all of them.
- A spec for a warehouse without a template validates but cannot be scaffolded yet.
