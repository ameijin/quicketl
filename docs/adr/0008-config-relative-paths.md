# 0008: Config-relative paths with a `--base-dir` override

This record explains how relative paths in pipeline YAML files are resolved. Read it if a pipeline works from one folder and fails from another.

**Status:** Accepted (ships in 1.7.0). Date: 2026-10-30.

## Context

Relative paths in pipeline YAML currently depend on the folder you run the command from. The same file can work in one folder and fail in another.

## Decision

We will resolve relative paths against the folder that holds the config file. A `--base-dir` flag keeps the old behavior. This ships in 1.7.0.

## Consequences

Positive:

- A pipeline behaves the same from any working folder.
- Example pipelines run from the repo root.

Negative:

- Pipelines that relied on the working folder may break. The CHANGELOG needs an upgrade note, and `--base-dir` is the workaround.
