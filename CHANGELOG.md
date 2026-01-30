# CHANGELOG

<!-- version list -->

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
