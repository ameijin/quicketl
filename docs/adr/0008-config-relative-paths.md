# 0008: Project-root relative paths with a `--base-dir` override

This record explains how relative paths in pipeline YAML files are resolved. Read it if a pipeline works from one folder and fails from another.

**Status:** Accepted (ships in 1.7.0). Date: 2026-10-30.

## Context

Relative paths in pipeline YAML depend on the folder you run the command from. The same file can work in one folder and fail in another.

## Decision

We will resolve relative file paths in this order:

1. The `--base-dir` value, if given.
2. The folder of the nearest `quicketl.yml` found by searching up from the pipeline file's folder (the project root).
3. Otherwise, leave paths alone, so they resolve against the current working directory.

Absolute paths, remote URIs that contain `://`, and database connection strings are never changed. This ships in 1.7.0.

## Consequences

Positive:

- A pipeline in a project with a `quicketl.yml` behaves the same from any working folder.
- Projects without a `quicketl.yml` behave exactly as before. This is not a breaking change.
- `quicketl init` writes a `quicketl.yml`, so new projects get the stable behavior by default.

Negative:

- Behavior depends on whether a `quicketl.yml` exists up the folder tree. A stray `quicketl.yml` in a parent folder changes where paths resolve.
- Database connection strings are not rewritten, so a relative SQLite path still depends on the working folder.

## Amendment (2026-10-30)

The first version of this record said relative paths would resolve against the config file's own folder, with `--base-dir` to restore the old behavior. That was a breaking change.

We changed the decision before release. Resolving against the pipeline file's own folder breaks the standard layout, where `pipelines/` sits next to `data/` (as created by `quicketl init`), because `data/sales.csv` would then be looked up inside `pipelines/`. It also breaks the workflow example in `examples/05-workflow`. The project owner chose the project-root rule above instead. It fixes the same problem and does not break existing projects.
