# CHANGELOG

<!-- version list -->

## v1.6.0 (2026-02-02)

### Bug Fixes

- Add None guards for optional sink in CLI commands
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Close database connections after use to prevent resource leaks
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Close database connections after use to prevent resource leaks
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Comprehensive cleanup and production readiness improvements
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Prevent hash_key temp table leak and SQL injection
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Prevent hash_key temp table leak and SQL injection
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Resolve ruff lint errors ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Sync _version.py with pyproject.toml (was 1.3.0, should be 1.5.0)
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Sync _version.py with pyproject.toml (was 1.3.0, should be 1.5.0)
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Wire ExecutionContext into pipeline execution ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Wire ExecutionContext into pipeline execution ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- **ci**: Use --group dev instead of --extra dev for dependency groups
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

### Chores

- Add *.csv and *.parquet to .gitignore, untrack data files
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Consolidate dev dependencies into dependency-groups
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Consolidate dev dependencies into dependency-groups
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Update development status classifier to Beta ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Update development status classifier to Beta ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

### Documentation

- Deduplicate CHANGELOG, merge ENHANCEMENT_PLAN into BACKLOG
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Deduplicate CHANGELOG, merge ENHANCEMENT_PLAN into BACKLOG
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Update README, add examples, and clean up BACKLOG status markers
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Update README, add examples, and clean up BACKLOG status markers
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

### Features

- Add --env and --profile CLI flags ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Add --env and --profile CLI flags ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Add JSON output format for file sinks ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Add JSON output format for file sinks ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Add retry with backoff for cloud storage operations
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Add retry with backoff for cloud storage operations
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Implement upsert mode for DatabaseSink ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Implement upsert mode for DatabaseSink ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

### Refactoring

- Extract shared predicate parser into engines/parsing.py
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Extract shared predicate parser into engines/parsing.py
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Remove dead engines/expressions.py module ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Remove dead engines/expressions.py module ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Remove IcebergSource from union and make sink optional
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Remove IcebergSource from union and make sink optional
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Rename ETLXEngine to QuickETLEngine ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Rename ETLXEngine to QuickETLEngine ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

### Testing

- Add contracts module tests for schema, registry, and pandera adapter
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Add contracts module tests for schema, registry, and pandera adapter
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Add parity tests for cast, fill_null, and dedup transforms
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Add parity tests for cast, fill_null, and dedup transforms
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))

- Improve core module coverage for context, backends, and results
  ([#7](https://github.com/ameijin/quicketl/pull/7),
  [`72ab5b9`](https://github.com/ameijin/quicketl/commit/72ab5b9496538e079272bc32b577887fb64a27b7))

- Improve core module coverage for context, backends, and results
  ([#6](https://github.com/ameijin/quicketl/pull/6),
  [`6342674`](https://github.com/ameijin/quicketl/commit/634267422ae9ddef36a69b218d8ba1003cc7dabd))


## v1.5.0 (2026-01-20)

### Bug Fixes

- Remove unused type ignore comments in pandera_adapter
  ([`6409749`](https://github.com/ameijin/quicketl/commit/6409749e73cc9752b8dc55c64694e13bd139432b))


## v1.4.0 (2026-01-20)

### Features

- **ai**: Add text chunking and embeddings transforms
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

- **ai**: Add vector store sinks for RAG pipelines
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

- **config**: Add environment inheritance and connection profiles
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

- **telemetry**: Add OpenTelemetry and OpenLineage integration
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

- **transforms**: Add window, pivot, unpivot, hash_key, coalesce transforms
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

### Bug Fixes

- Resolve correctness blockers for release readiness
  ([#5](https://github.com/ameijin/quicketl/pull/5),
  [`b93f874`](https://github.com/ameijin/quicketl/commit/b93f874f5e3e0ff56ca39c181654099592d49c5a))

- Resolve infinite loop in chunking strategies
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

- Fix mypy type checking errors and ruff linting errors
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

### Documentation

- Add guides for secrets, AI data prep, and observability
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))

### Testing

- Add unit test infrastructure and additional test coverage
  ([#4](https://github.com/ameijin/quicketl/pull/4),
  [`4e57e18`](https://github.com/ameijin/quicketl/commit/4e57e18b3c647ff86faed6596ce84f6ff0d73aa1))


## v1.3.0 (2025-12-22)

### Features

- **secrets**: Add pluggable secrets provider system
  ([#3](https://github.com/ameijin/quicketl/pull/3),
  [`7a6805c`](https://github.com/ameijin/quicketl/commit/7a6805cd98a7389ac8e2e43d6c4e8d2ec7856fc8))

### Bug Fixes

- Fix mypy type checking and ruff linting errors
  ([#3](https://github.com/ameijin/quicketl/pull/3),
  [`7a6805c`](https://github.com/ameijin/quicketl/commit/7a6805cd98a7389ac8e2e43d6c4e8d2ec7856fc8))


## v1.2.0 (2025-12-17)

### Bug Fixes

- Cleanup docs for most recent additions
  ([#2](https://github.com/ameijin/quicketl/pull/2),
  [`ad76647`](https://github.com/ameijin/quicketl/commit/ad766479d3c9224e7b9a257d2795417345c3284e))


## v1.1.0 (2025-12-17)

### Features

- Add multi-source pipelines (join/union), database sink, partitioned writes, and enhanced
  expressions
  ([#1](https://github.com/ameijin/quicketl/pull/1),
  [`870077f`](https://github.com/ameijin/quicketl/commit/870077fa49a0785e1eeb32bc0d7b00c2f02c6e53))


## v1.0.3 (2025-12-16)


## v1.0.2 (2025-12-16)

### Bug Fixes

- Add auto changelog
  ([`f5e942b`](https://github.com/ameijin/quicketl/commit/f5e942bd1574be1edd8a3c6bad1b62e5a3112458))


## v1.0.1 (2025-12-16)

### Documentation

- Update readme
  ([`aef6b31`](https://github.com/ameijin/quicketl/commit/aef6b3186b3dcec09b1e807c04b4eab557030b8d))


## v1.0.0 (2025-12-16)

- Initial Release
