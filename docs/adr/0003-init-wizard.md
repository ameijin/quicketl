# 0003: `quicketl init` becomes a wizard

This record explains the planned change to `quicketl init`. Read it to learn what the command will ask and what keeps working.

**Status:** Accepted (planned for 2.0, not yet implemented). Date: 2026-10-30.

## Context

The tool now covers three kinds of work: new platforms, migrations between warehouses, and pipeline or POC projects. A single `init` that only creates a pipeline project does not fit the platform-first default (see [0002](0002-platform-first-slim-core.md)).

## Decision

We will turn `quicketl init` into a wizard with three choices:

1. New platform (the default).
2. Migration.
3. Pipeline or POC project.

Existing `init` flags keep working without prompts, so scripts do not break. The current flag behavior in `cli/init.py` must be checked before any change is made.

## Consequences

Positive:

- New users reach the right starting point from one command.
- Scripts that pass flags are not affected.

Negative:

- The default result of a bare `quicketl init` changes from a pipeline project to a platform. The 2.0 upgrade guide must say so.
- The wizard adds an interactive path to test next to the flag path.
