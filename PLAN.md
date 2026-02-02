# QuickETL Cleanup & Improvement Plan

## Context

Comprehensive review of the quicketl package identified 23 issues across correctness,
architecture, testing, documentation, and production readiness. This plan addresses
all of them in 5 phases, ordered by severity.

**Standards applied**: KB `01-Standards/` (architecture, coding, testing)
**Conventions**: Conventional commits, >75% coverage target, PEP 8, type hints

---

## Phase 1: Critical Correctness Fixes

Issues that cause incorrect behavior, resource leaks, or runtime errors.

### 1.1 Fix version desync

`_version.py` says `1.3.0`, `pyproject.toml` says `1.5.0`. Semantic release updates
`pyproject.toml` but Hatch reads from `_version.py`. Runtime `__version__` is wrong.

**Fix**: Configure semantic release to also update `_version.py`, and sync the
current value to `1.5.0`.

- **Modify**: `src/quicketl/_version.py` — set `__version__ = "1.5.0"`
- **Modify**: `pyproject.toml` — add `_version.py` path to `[tool.semantic_release]`
  so both files stay in sync on release
- **Test**: `uv run python -c "from quicketl import __version__; print(__version__)"` → `1.5.0`
- **Commit**: `fix: sync _version.py with pyproject.toml (was 1.3.0, should be 1.5.0)`

### 1.2 Remove or implement `upsert` mode

`DatabaseSink` accepts `mode: "upsert"` + `upsert_keys`, but `write_database()`
raises `ValueError` at runtime. Violates fail-fast principle — should fail at
validation or work.

**Fix**: Remove `upsert` from the `DatabaseSink.mode` Literal and remove the
`upsert_keys` field. Add it back when actually implemented.

- **Modify**: `src/quicketl/config/models.py` — remove `"upsert"` from mode Literal,
  remove `upsert_keys` field
- **Test**: Existing config validation tests (verify `mode: upsert` now raises
  ValidationError)
- **Add test**: `tests/unit/config/test_models.py` — test that `upsert` mode is rejected
- **Commit**: `fix: remove unimplemented upsert mode from DatabaseSink`

### 1.3 Fix database connection leaks

`read_database()` and `write_database()` both call `ibis.connect()` without cleanup.

**Fix**: Use context managers / explicit cleanup. Since Ibis connections don't support
`with`, add cleanup in `finally` blocks, or store and reuse connections.

- **Modify**: `src/quicketl/engines/base.py` — `read_database()`: store connection
  ref so it can be cleaned up; add `close()` method to `ETLXEngine`
- **Modify**: `src/quicketl/io/writers/database.py` — add try/finally to close
  the connection after write
- **Test**: Verify connections are cleaned up (mock `ibis.connect` and assert disconnect)
- **Add test**: `tests/unit/io/test_database_writer.py` — connection lifecycle tests
- **Commit**: `fix: close database connections after read/write operations`

### 1.4 Fix `hash_key` temp table leak + SQL construction

`hash_key()` creates `_hash_result_` temp table but never cleans it up. Also
constructs SQL from column names without sanitization.

**Fix**:
- Clean up both temp tables in `finally` block
- Validate column names against `table.columns` before SQL construction
- Quote identifiers properly

- **Modify**: `src/quicketl/engines/base.py` — `hash_key()` method: add cleanup
  for result table, validate column names, quote identifiers
- **Test**: `tests/unit/engines/test_engine_transforms.py` — hash_key creates and
  cleans up temp tables; rejects invalid column names
- **Commit**: `fix: hash_key temp table leak and SQL injection surface`

### 1.5 Wire up `ExecutionContext`

`pipeline.py:234` creates `ExecutionContext(variables=self._variables)` but never
assigns it. The context should be stored and passed to transform/check steps.

**Fix**: Store context and use it to pass variables/tables through pipeline execution.
Use the context's `tables` dict as the `table_context` for join/union transforms.

- **Modify**: `src/quicketl/pipeline/pipeline.py` — assign context, use
  `context.tables` for multi-source table context, expose context on result
- **Test**: Existing pipeline tests should still pass; add test that context
  variables are accessible during execution
- **Commit**: `fix: wire ExecutionContext into pipeline execution`

---

## Phase 2: Structural & Design Cleanup

Code organization, API consistency, and config hygiene.

### 2.1 Extract shared predicate parser

`_parse_predicate` and `_parse_value` are duplicated between `engines/base.py`
and `quality/checks.py`. The checks version also has a bug (checks `=` before `==`).

**Note**: `engines/expressions.py` already has `parse_expression()` / `parse_predicate()`
using `ibis._.sql()` — a much cleaner approach. However, the `ibis._.sql()` deferred
expression API may not work in all contexts (needs a table binding). Assess whether
to adopt it or extract the hand-rolled parser to a shared module.

**Fix**: Create `src/quicketl/engines/parsing.py` that consolidates the hand-rolled
parser. Both `engines/base.py` and `quality/checks.py` import from it. Fix the
operator ordering bug.

- **Create**: `src/quicketl/engines/parsing.py` — shared `parse_predicate()`,
  `parse_value()`, `parse_expression()` functions
- **Modify**: `src/quicketl/engines/base.py` — import from `parsing.py`,
  remove duplicate methods
- **Modify**: `src/quicketl/quality/checks.py` — import from `parsing.py`,
  remove duplicate functions
- **Delete or update**: `src/quicketl/engines/expressions.py` — evaluate if it
  should remain as a higher-level alternative or be removed (currently dead code at
  0% coverage)
- **Test**: `tests/unit/engines/test_parsing.py` — comprehensive predicate/expression tests
- **Commit**: `refactor: extract shared predicate parser, fix operator ordering bug`

### 2.2 Handle `IcebergSource` properly

`IcebergSource` is in the `SourceConfig` union but `read_source()` raises
`NotImplementedError`. Users see a confusing runtime error.

**Fix**: Remove from union and add a clear validation error, or move to a separate
"planned" section. Since Iceberg is medium-priority in the backlog, remove from the
union for now and document as planned.

- **Modify**: `src/quicketl/config/models.py` — remove `IcebergSource` from
  `SourceConfig` union; keep the class for future use
- **Modify**: `src/quicketl/engines/base.py` — remove Iceberg case from `read_source`
- **Test**: Config validation should reject `type: iceberg` until implemented
- **Commit**: `refactor: remove unimplemented IcebergSource from SourceConfig union`

### 2.3 Make `PipelineConfig.sink` optional

Currently required, but `Pipeline.run(dry_run=True)` and `quicketl validate`
don't need a sink. Users can't write validation-only YAML.

**Fix**: Make `sink` optional with `None` default.

- **Modify**: `src/quicketl/config/models.py` — `sink: SinkConfig | None = Field(default=None, ...)`
- **Modify**: `src/quicketl/pipeline/pipeline.py` — adjust validation (sink required
  only when not dry_run)
- **Test**: `tests/unit/config/test_config.py` — YAML without sink parses successfully
- **Test**: `tests/unit/pipeline/test_pipeline.py` — dry_run works without sink
- **Commit**: `feat: make pipeline sink optional for dry-run and validation workflows`

### 2.4 Clean up duplicate dev dependency groups

Both `[project.optional-dependencies] dev` and `[dependency-groups] dev` exist with
conflicting versions.

**Fix**: Keep `[dependency-groups] dev` (the modern PEP 735 approach for dev tooling)
and remove `[project.optional-dependencies] dev`. Update CI to use `uv sync --group dev`.

- **Modify**: `pyproject.toml` — remove `dev` from `[project.optional-dependencies]`,
  consolidate into `[dependency-groups]`, ensure versions align
- **Modify**: `.github/workflows/ci.yml` — use `uv sync --group dev` if not already
- **Commit**: `chore: consolidate dev dependencies into dependency-groups`

### 2.5 Update development status classifier

At v1.5.0 with a working core, `Alpha` is inaccurate.

**Fix**: Change to `Development Status :: 4 - Beta`.

- **Modify**: `pyproject.toml` — update classifier
- **Commit**: `chore: update development status to Beta`

### 2.6 Rename `ETLXEngine` to `QuickETLEngine`

The primary class should match the package name. Keep `ETLXEngine` as a
deprecated alias for one release cycle.

**Decision needed**: This is a public API change. Consider an ADR.

- **Modify**: `src/quicketl/engines/base.py` — rename class to `QuickETLEngine`,
  add `ETLXEngine = QuickETLEngine` alias with deprecation warning
- **Modify**: `src/quicketl/__init__.py` — update exports
- **Modify**: All internal imports that reference `ETLXEngine`
- **Test**: Both names work, `ETLXEngine` emits DeprecationWarning
- **Commit**: `refactor: rename ETLXEngine to QuickETLEngine with deprecation alias`
- **ADR**: Yes — documents the naming change and deprecation strategy

---

## Phase 3: Test Coverage Improvements

Target: >75% overall, >80% for core modules (engine, pipeline, config, quality).

### 3.1 Add contracts module tests

Currently 0% coverage. The module is implemented but untested at runtime.

- **Create**: `tests/unit/quality/test_contracts.py` — test PanderaContractValidator,
  DataContract, ColumnContract, ContractRegistry
- **Create**: `tests/unit/quality/test_contract_check.py` — test `run_contract_check()`
  integration with the quality runner
- **Note**: These tests need `pandera[polars]` — add to dev dependency group or
  mark with `@pytest.mark.skipif`
- **Commit**: `test: add contracts module tests`

### 3.2 Add parity tests across backends

Critical gap for a multi-backend framework. Users need confidence that switching
backends produces the same results.

- **Create**: `tests/parity/test_transform_parity.py` — run each transform operation
  on DuckDB and Polars, compare results
- **Create**: `tests/parity/test_pipeline_parity.py` — run a representative pipeline
  on each available backend, compare output
- **Commit**: `test: add backend parity tests for DuckDB and Polars`

### 3.3 Improve core module coverage

Focus on the modules that are core to the pipeline execution path.

- **Add tests**: `tests/unit/engines/test_engine_base.py` — window, pivot, unpivot,
  hash_key, coalesce transforms (many currently untested)
- **Add tests**: `tests/unit/io/test_database_writer.py` — write modes (append,
  truncate, replace), error handling
- **Add tests**: `tests/unit/io/test_database_reader.py` — query vs table mode,
  connection handling
- **Add tests**: `tests/unit/pipeline/test_pipeline_execution.py` — multi-source
  pipelines, dry_run, check failure modes
- **Commit**: `test: improve coverage for engine, I/O, and pipeline modules`

### 3.4 Remove or test dead code

`engines/expressions.py` is at 0% coverage and not imported anywhere in production
code. Either wire it in or remove it.

**Fix**: Evaluate if `ibis._.sql()` is a better parsing approach. If so, plan
migration for a future phase. For now, remove the dead module.

- **Delete**: `src/quicketl/engines/expressions.py` (or mark as experimental)
- **Commit**: `refactor: remove unused expressions module`

---

## Phase 4: Documentation & Polish

### 4.1 Update README

Current README mentions "12 Transforms" and is missing all major features added
in v1.1-1.5.

**Fix**: Update to reflect actual capabilities: 16+ transforms, data contracts,
secrets, AI/ML, telemetry, Airflow, workflows, builder API.

- **Modify**: `README.md` — update feature list, add sections for contracts
  and workflows, update transform count
- **Commit**: `docs: update README with current feature set`

### 4.2 Add runnable examples

Empty `examples/` directory. For a framework targeting quick pipeline creation,
this is critical. Focus on the local-to-cloud story.

- **Create**: `examples/01_local_csv_to_parquet/` — simplest possible pipeline
- **Create**: `examples/02_multi_source_join/` — join two files
- **Create**: `examples/03_quality_checks/` — pipeline with checks and contracts
- **Create**: `examples/04_local_to_cloud/` — DuckDB local → database/S3 sink
  (with instructions for swapping engine/sink for production)
- **Create**: `examples/05_workflow/` — multi-stage medallion workflow
- Each example: `pipeline.yml`, `README.md` explaining it, sample data (small)
- **Commit**: `docs: add runnable pipeline examples`

### 4.3 Clean up BACKLOG.md

Multiple items marked "Not implemented" are actually done (secrets, telemetry,
parallel execution).

- **Modify**: `BACKLOG.md` — update status markers to reflect reality
- **Commit**: `docs: update backlog status markers`

### 4.4 Fix CHANGELOG duplication

v1.1.0-1.3.0 all describe the same features. This is a semantic-release config issue.

**Fix**: Clean up the existing changelog manually. Investigate semantic-release
config to prevent future duplicates (likely caused by repeated force-pushes to main).

- **Modify**: `CHANGELOG.md` — deduplicate entries
- **Commit**: `docs: clean up duplicate changelog entries`

### 4.5 Track or remove `ENHANCEMENT_PLAN.md`

Currently untracked in git. Either commit it (it has useful context) or move
the relevant items into BACKLOG.md and delete.

- **Decision**: Commit it as a planning artifact, or extract actionable items
  into BACKLOG.md
- **Commit**: `docs: commit enhancement plan` or `docs: merge enhancement plan into backlog`

---

## Phase 5: Production Readiness (Local-to-Cloud Story)

### 5.1 Add `--env` and `--profile` CLI flags

The environments and profiles modules exist but aren't wired into the CLI.
This is the key gap for the local-to-cloud developer experience.

- **Modify**: `src/quicketl/cli/run.py` — add `--env` and `--profile` options,
  load profiles from `quicketl.yml` project config
- **Modify**: `src/quicketl/cli/workflow.py` — same flags
- **Test**: CLI tests with env/profile flags
- **Commit**: `feat: add --env and --profile CLI flags for connection management`

### 5.2 Add JSON output format to file sinks

Input supports csv/parquet/json. Output only csv/parquet. Asymmetric.

- **Modify**: `src/quicketl/config/models.py` — add `"json"` to `FileSink.format` Literal
- **Modify**: `src/quicketl/io/writers/file.py` — add `"json"` case
- **Test**: Write JSON output, verify format
- **Commit**: `feat: add JSON output format for file sinks`

### 5.3 Add retry logic for cloud I/O

For production pipelines, cloud operations need resilience.

**Fix**: Add a lightweight retry wrapper for `read_file` and `write_file` when
paths are cloud URIs (s3://, gs://, az://).

- **Create**: `src/quicketl/io/retry.py` — configurable retry with exponential backoff
- **Modify**: `src/quicketl/io/readers/file.py` — wrap cloud reads with retry
- **Modify**: `src/quicketl/io/writers/file.py` — wrap cloud writes with retry
- **Test**: Mock failures, verify retry behavior
- **Commit**: `feat: add retry with backoff for cloud storage operations`

---

## ADR Decisions Needed

| Decision | Phase | Reason |
|----------|-------|--------|
| Rename `ETLXEngine` → `QuickETLEngine` | 2.6 | Public API change with deprecation path |
| Shared parser strategy (hand-rolled vs ibis._.sql()) | 2.1 | Architecture choice affecting expression handling |

---

## Files Summary

### Files to Create
| File | Phase |
|------|-------|
| `src/quicketl/engines/parsing.py` | 2.1 |
| `src/quicketl/io/retry.py` | 5.3 |
| `tests/unit/engines/test_parsing.py` | 2.1 |
| `tests/unit/quality/test_contracts.py` | 3.1 |
| `tests/unit/quality/test_contract_check.py` | 3.1 |
| `tests/parity/test_transform_parity.py` | 3.2 |
| `tests/parity/test_pipeline_parity.py` | 3.2 |
| `tests/unit/io/test_database_writer.py` | 3.3 |
| `tests/unit/io/test_database_reader.py` | 3.3 |
| `examples/01_local_csv_to_parquet/` | 4.2 |
| `examples/02_multi_source_join/` | 4.2 |
| `examples/03_quality_checks/` | 4.2 |
| `examples/04_local_to_cloud/` | 4.2 |
| `examples/05_workflow/` | 4.2 |

### Files to Modify
| File | Phases |
|------|--------|
| `src/quicketl/_version.py` | 1.1 |
| `pyproject.toml` | 1.1, 2.4, 2.5 |
| `src/quicketl/config/models.py` | 1.2, 2.2, 2.3, 5.2 |
| `src/quicketl/engines/base.py` | 1.3, 1.4, 2.1, 2.2, 2.6 |
| `src/quicketl/io/writers/database.py` | 1.3 |
| `src/quicketl/pipeline/pipeline.py` | 1.5, 2.3 |
| `src/quicketl/quality/checks.py` | 2.1 |
| `src/quicketl/__init__.py` | 2.6 |
| `src/quicketl/cli/run.py` | 5.1 |
| `src/quicketl/cli/workflow.py` | 5.1 |
| `src/quicketl/io/writers/file.py` | 5.2, 5.3 |
| `src/quicketl/io/readers/file.py` | 5.3 |
| `README.md` | 4.1 |
| `BACKLOG.md` | 4.3 |
| `CHANGELOG.md` | 4.4 |

### Files to Delete
| File | Phase | Reason |
|------|-------|--------|
| `src/quicketl/engines/expressions.py` | 3.4 | Dead code, 0% coverage, not imported |

---

## Execution Order

Phases are designed to be executed sequentially. Within each phase, items can
generally be done in order listed. Each item gets its own conventional commit.

**Branch strategy**: `fix/quicketl-cleanup` for phases 1-2, then `feature/quicketl-tests`
for phase 3, `docs/quicketl-polish` for phase 4, `feature/quicketl-production` for
phase 5. Or a single branch if preferred.
