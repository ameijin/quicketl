# 0009: Release plan for 1.6.1, 1.7.0 and 2.0.0

This record sets the order of the next three releases. Read it to learn which release holds which change.

**Status:** Accepted. Date: 2026-10-30.

## Context

Some work fixes trust problems in the current code. Some changes behavior. The platform-first restructure ([0002](0002-platform-first-slim-core.md)) breaks installs. Mixing them would make upgrades hard to reason about.

## Decision

We will release in three steps:

| Release | Contents |
|---------|----------|
| 1.6.1 | Trust fixes |
| 1.7.0 | Config-relative paths ([0008](0008-config-relative-paths.md)) and the Ibis 12 upgrade |
| 2.0.0 | Platform-first restructure |

2.0.0 is breaking because a plain `pip install quicketl` no longer includes pipelines.

## Consequences

Positive:

- Each release has one theme, so upgrade notes stay short.
- Users get fixes before the large change.

Negative:

- Platform features wait for 2.0.0.
- We maintain three releases in a row, each with its own CHANGELOG entry and checks.
