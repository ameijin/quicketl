# Changelog

All notable changes to QuickETL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation site

## [0.1.0] - 2025-01-15

### Added

#### Core Features
- YAML-based pipeline configuration
- Multiple compute backends via Ibis (DuckDB, Polars, Spark, Snowflake, BigQuery, PostgreSQL, MySQL, ClickHouse, DataFusion, Pandas)
- 12 transform operations:
  - `select` - Column selection
  - `rename` - Column renaming
  - `filter` - Row filtering
  - `derive_column` - Calculated columns
  - `cast` - Type conversion
  - `fill_null` - NULL handling
  - `dedup` - Deduplication
  - `sort` - Row ordering
  - `join` - Data combining
  - `aggregate` - Grouping and summarization
  - `union` - Dataset concatenation
  - `limit` - Row limiting

#### Quality Checks
- `not_null` - NULL value detection
- `unique` - Uniqueness validation
- `row_count` - Row count bounds
- `accepted_values` - Value enumeration
- `expression` - Custom SQL expressions with thresholds

#### I/O Support
- File sources: CSV, Parquet, JSON, Excel
- Database sources: PostgreSQL, MySQL, Snowflake, BigQuery
- Cloud storage: S3, GCS, Azure Blob
- All sources supported as sinks

#### CLI
- `quicketl run` - Execute pipelines
- `quicketl validate` - Configuration validation
- `quicketl init` - Project scaffolding
- `quicketl info` - Version and backend information
- `quicketl schema` - JSON schema generation

#### Python API
- `Pipeline` class for programmatic execution
- `QuickETLEngine` for low-level control
- Pydantic configuration models
- Quality check classes

#### Integrations
- Apache Airflow operator and decorator
- Environment variable substitution
- JSON output for monitoring

### Developer Experience
- JSON Schema for IDE autocomplete
- Verbose logging mode
- Dry run support
- Sample project generation

## Future Roadmap

### Planned for 0.2.0
- [ ] Prefect integration
- [ ] Dagster integration
- [ ] Additional backends (Trino, Presto)
- [ ] Pipeline composition (includes/extends)
- [ ] Parallel transform execution

### Planned for 0.3.0
- [ ] Web UI for pipeline management
- [ ] Pipeline versioning
- [ ] Lineage tracking
- [ ] Metric collection

[Unreleased]: https://github.com/your-org/quicketl/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/quicketl/releases/tag/v0.1.0
