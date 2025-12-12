# Changelog

All notable changes to ETLX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation site with MkDocs Material
- API reference auto-generation from docstrings
- Runnable examples with sample data

## [0.1.0] - 2025-12-11

### Added

#### Core Framework
- Pipeline execution engine with Ibis backend abstraction
- YAML configuration with Pydantic v2 validation
- Variable substitution with `${VAR}` and `${VAR:-default}` syntax
- Structured logging with structlog
- JSON Schema generation for IDE support

#### Transform Operations (12)
- `select` - Choose and reorder columns
- `rename` - Rename columns with mapping syntax
- `filter` - Row filtering with SQL-like predicates
- `derive_column` - Create computed columns
- `cast` - Type conversion
- `fill_null` - Replace null values
- `dedup` - Remove duplicate rows
- `sort` - Order rows by columns
- `join` - Join multiple datasets (inner, left, right, outer)
- `aggregate` - Group by with aggregation functions
- `union` - Vertical concatenation
- `limit` - Limit row count

#### Quality Checks (5)
- `not_null` - Ensure no null values in columns
- `unique` - Check uniqueness constraints
- `row_count` - Validate row count bounds
- `accepted_values` - Whitelist validation
- `expression` - Custom SQL predicate validation

#### CLI Commands
- `etlx run` - Execute pipelines with variable injection
- `etlx validate` - Validate configuration without running
- `etlx init` - Initialize new projects with sample data
- `etlx info` - Display version and backend availability
- `etlx schema` - Output JSON schema for IDE support

#### Python API
- `Pipeline` class with builder pattern
- `Pipeline.from_yaml()` for configuration-driven pipelines
- `ETLXEngine` for direct engine access
- `PipelineResult` with step-by-step execution details

#### Backend Support
- DuckDB (default, included)
- Polars (included)
- DataFusion (optional)
- Spark (optional)
- pandas (optional)
- PostgreSQL, MySQL, ClickHouse (optional)
- Snowflake, BigQuery, Trino (optional)

#### Integrations
- Airflow `@etlx_task` decorator
- Cloud storage via fsspec (S3, GCS, Azure ADLS)

#### File Formats
- Input: CSV, Parquet, JSON
- Output: CSV, Parquet (with partitioning)

[Unreleased]: https://github.com/etlx/etlx/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/etlx/etlx/releases/tag/v0.1.0
