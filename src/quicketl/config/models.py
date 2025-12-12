"""Core Pydantic configuration models for ETLX.

This module defines the configuration schema for sources, sinks, and pipelines
using Pydantic v2 discriminated unions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from quicketl.config.checks import CheckConfig
    from quicketl.config.transforms import TransformStep

# =============================================================================
# Source Configurations
# =============================================================================


class FileSource(BaseModel):
    """File-based data source configuration.

    Supports CSV, Parquet, and JSON files from local filesystem or cloud storage
    (S3, GCS, Azure) via fsspec.

    Example YAML:
        source:
          type: file
          path: s3://bucket/data.parquet
          format: parquet
    """

    type: Literal["file"] = "file"
    path: str = Field(..., description="File path (local or cloud URI)")
    format: Literal["csv", "parquet", "json"] = Field(
        default="parquet",
        description="File format",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Format-specific read options",
    )


class DatabaseSource(BaseModel):
    """Database data source configuration.

    Supports PostgreSQL, MySQL, SQL Server, and other databases via Ibis.

    Example YAML:
        source:
          type: database
          connection: ${POSTGRES_URI}
          query: SELECT * FROM users WHERE active = true
    """

    type: Literal["database"] = "database"
    connection: str = Field(
        ...,
        description="Connection string or environment variable reference",
    )
    query: str | None = Field(
        default=None,
        description="SQL query to execute",
    )
    table: str | None = Field(
        default=None,
        description="Table name (alternative to query)",
    )


class IcebergSource(BaseModel):
    """Apache Iceberg table source configuration.

    Note: Full Iceberg support planned for v0.2.

    Example YAML:
        source:
          type: iceberg
          catalog: my_catalog
          database: analytics
          table: events
    """

    type: Literal["iceberg"] = "iceberg"
    catalog: str = Field(..., description="Iceberg catalog name")
    database: str = Field(..., description="Database/namespace name")
    table: str = Field(..., description="Table name")
    snapshot_id: int | None = Field(
        default=None,
        description="Optional snapshot ID for time travel",
    )


# Discriminated union for all source types
SourceConfig = Annotated[
    FileSource | DatabaseSource | IcebergSource,
    Field(discriminator="type"),
]


# =============================================================================
# Sink Configurations
# =============================================================================


class FileSink(BaseModel):
    """File-based data sink configuration.

    Example YAML:
        sink:
          type: file
          path: s3://bucket/output/
          format: parquet
          partition_by: [date, region]
    """

    type: Literal["file"] = "file"
    path: str = Field(..., description="Output path (local or cloud URI)")
    format: Literal["parquet", "csv"] = Field(
        default="parquet",
        description="Output format",
    )
    partition_by: list[str] = Field(
        default_factory=list,
        description="Columns to partition output by",
    )
    mode: Literal["overwrite", "append"] = Field(
        default="overwrite",
        description="Write mode",
    )


class DatabaseSink(BaseModel):
    """Database data sink configuration.

    Example YAML:
        sink:
          type: database
          connection: ${POSTGRES_URI}
          table: processed_data
          mode: upsert
          upsert_keys: [id]
    """

    type: Literal["database"] = "database"
    connection: str = Field(
        ...,
        description="Connection string or environment variable reference",
    )
    table: str = Field(..., description="Target table name")
    mode: Literal["append", "truncate", "upsert"] = Field(
        default="append",
        description="Write mode",
    )
    upsert_keys: list[str] = Field(
        default_factory=list,
        description="Primary key columns for upsert mode",
    )


# Discriminated union for all sink types
SinkConfig = Annotated[
    FileSink | DatabaseSink,
    Field(discriminator="type"),
]


# =============================================================================
# Pipeline Configuration
# =============================================================================


class PipelineConfig(BaseModel):
    """Complete pipeline configuration.

    Example YAML:
        name: daily_sales_etl
        description: Extract sales, compute revenue, aggregate by region
        engine: duckdb

        source:
          type: file
          path: s3://bucket/sales.parquet

        transforms:
          - op: filter
            predicate: amount > 0
          - op: aggregate
            group_by: [region]
            aggs:
              total: sum(amount)

        checks:
          - type: not_null
            columns: [region, total]

        sink:
          type: file
          path: s3://bucket/output/
    """

    name: str = Field(..., description="Pipeline name")
    description: str = Field(default="", description="Pipeline description")
    engine: Literal["duckdb", "polars", "datafusion", "spark", "pandas"] = Field(
        default="duckdb",
        description="Compute engine to use",
    )
    source: SourceConfig = Field(..., description="Data source configuration")
    transforms: list[TransformStep] = Field(
        default_factory=list,
        description="Transform steps to apply",
    )
    checks: list[CheckConfig] = Field(
        default_factory=list,
        description="Quality checks to run",
    )
    sink: SinkConfig = Field(..., description="Data sink configuration")

    model_config = {
        "extra": "forbid",
    }
