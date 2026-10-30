# 0009: Release plan for 1.7.0 and 2.0.0

This record sets the order of the next releases and how changes reach `main`. Read it to learn which release holds which change.

**Status:** Accepted. Date: 2026-10-30.

## Context

Some work fixes trust problems in the current code. Some changes behavior. The platform-first restructure ([0002](0002-platform-first-slim-core.md)) breaks installs. Mixing them would make upgrades hard to reason about.

## Decision

We will release in two steps:

| Release | Contents |
|---------|----------|
| 1.7.0 | Trust fixes, project-root relative paths with `--base-dir` ([0008](0008-config-relative-paths.md)), and the Ibis 12 upgrade |
| 2.0.0 | Platform-first restructure |

Changes reach `main` through a `dev` branch:

1. Each fix or feature gets its own pull request into `dev`. CI runs on it.
2. `dev` is kept linear, because `main` requires linear history.
3. When a release is ready, one pull request moves `dev` into `main` with a rebase merge, so every conventional commit stays visible.
4. The release workflow runs only for `main`. semantic-release reads those commits, picks the version and writes the CHANGELOG.

2.0.0 is breaking because a plain `pip install quicketl` no longer includes pipelines.

## Consequences

Positive:

- 1.7.0 has no breaking changes, so users get the fixes before the large change.
- One review per release instead of one per pull request.
- The CHANGELOG keeps one line per fix or feature.

Negative:

- Platform features wait for 2.0.0.
- Fixes wait in `dev` until the release pull request is merged.

## Amendment (2026-10-30)

The first version of this record planned a separate 1.6.1 patch for the trust fixes. The user chose to collect all work in a `dev` branch and release it together. Because the batch contains new features, semantic-release versions it as 1.7.0, so 1.6.1 is skipped.
