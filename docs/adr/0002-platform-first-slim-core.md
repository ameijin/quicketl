# 0002: Platform-first default with a slim core

This record explains the 2.0 install layout: a small default install for platform work, with pipelines as an opt-in extra. Read it to learn why `pip install quicketl` changes in 2.0.

**Status:** Accepted. The slim core and the `[pipelines]` extra are implemented on the 2.0 branch (unreleased). The Copier and platform commands are still planned. Date: 2026-10-30.

## Context

Most use is standing up platforms, not running pipelines. Today a plain install pulls in the whole pipeline data stack. Sizes measured in this repo's virtual environment:

| Group | Approximate size |
|-------|------------------|
| Platform-side libraries | 10 MB |
| Pipeline data stack (pyarrow 117 MB, pandas 48 MB, numpy 22 MB, ibis 15 MB) | 200 MB |

The size of Copier (the template tool) has not been measured yet.

## Decision

We will make the platform experience the default and move pipelines into an extra.

```text
pip install quicketl              # core: CLI, init, validate, schema, platform scaffolding, migrate convert
pip install quicketl[pipelines]   # adds Ibis, DuckDB, Polars, pyarrow, fsspec: run, workflow, profile, checks, migrate reconcile
pip install quicketl[snowflake]   # backend extras include [pipelines]
pip install quicketl[all]         # everything
```

- Core dependencies: pydantic, pyyaml, structlog, typer, rich, copier and sqlglot. We pin sqlglot explicitly because Ibis will no longer bring it in for core installs.
- The separate `[migrate]` extra is dropped. sqlglot is small enough for core. `migrate reconcile` needs warehouse connections, which come from backend extras.
- Backend extras include the package itself, for example `snowflake = ["quicketl[pipelines]", "ibis-framework[snowflake]"]`.
- Running `quicketl run` without `[pipelines]` prints one line, "Pipelines need `pip install quicketl[pipelines]`", and exits with a non-zero code.
- Core commands must not import Ibis. Top-level exports become lazy, so `from quicketl import Pipeline` still works when `[pipelines]` is installed.

## Consequences

Positive:

- A platform-only install is about 20 times smaller than one with the data stack (10 MB against 200 MB, before Copier is counted).
- Platform commands start faster and install in more places, such as CI jobs.

Negative:

- This is a breaking change. A plain `pip install quicketl` no longer includes pipelines, so it needs a major version (see [0009](0009-release-plan.md)) and an upgrade guide.
- We must audit imports and add lazy exports. A CI job must install the plain package in a clean environment and check that `quicketl run` prints the hint and that pyarrow and ibis are absent.
- The final core size is not known until Copier is measured.
