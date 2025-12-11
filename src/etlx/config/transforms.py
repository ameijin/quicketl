"""Transform step configuration models.

Defines the 12 core transform operations as a Pydantic discriminated union.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


class SelectTransform(BaseModel):
    """Select specific columns from the data.

    Example YAML:
        - op: select
          columns: [id, name, amount]
    """

    op: Literal["select"] = "select"
    columns: list[str] = Field(..., description="Columns to select")


class RenameTransform(BaseModel):
    """Rename columns.

    Example YAML:
        - op: rename
          mapping:
            old_name: new_name
            another_old: another_new
    """

    op: Literal["rename"] = "rename"
    mapping: dict[str, str] = Field(
        ...,
        description="Mapping of old column names to new names",
    )


class FilterTransform(BaseModel):
    """Filter rows using a SQL-like predicate.

    Example YAML:
        - op: filter
          predicate: amount > 100 AND status = 'active'
    """

    op: Literal["filter"] = "filter"
    predicate: str = Field(..., description="SQL-like filter predicate")


class DeriveColumnTransform(BaseModel):
    """Create a new computed column.

    Example YAML:
        - op: derive_column
          name: revenue
          expr: quantity * unit_price
    """

    op: Literal["derive_column"] = "derive_column"
    name: str = Field(..., description="Name for the new column")
    expr: str = Field(..., description="SQL-like expression for the column value")


class CastTransform(BaseModel):
    """Cast column types.

    Example YAML:
        - op: cast
          columns:
            id: string
            amount: float64
            created_at: datetime
    """

    op: Literal["cast"] = "cast"
    columns: dict[str, str] = Field(
        ...,
        description="Mapping of column names to target types",
    )


class FillNullTransform(BaseModel):
    """Replace null values with defaults.

    Example YAML:
        - op: fill_null
          columns:
            discount: 0
            notes: "N/A"
    """

    op: Literal["fill_null"] = "fill_null"
    columns: dict[str, Any] = Field(
        ...,
        description="Mapping of column names to fill values",
    )


class DedupTransform(BaseModel):
    """Remove duplicate rows.

    Example YAML:
        - op: dedup
          columns: [id]  # Dedupe based on id column

        # Or dedupe on all columns:
        - op: dedup
    """

    op: Literal["dedup"] = "dedup"
    columns: list[str] | None = Field(
        default=None,
        description="Columns to consider for deduplication (None = all)",
    )


class SortTransform(BaseModel):
    """Sort rows by specified columns.

    Example YAML:
        - op: sort
          by: [created_at, id]
          descending: true
    """

    op: Literal["sort"] = "sort"
    by: list[str] = Field(..., description="Columns to sort by")
    descending: bool = Field(default=False, description="Sort in descending order")


class JoinTransform(BaseModel):
    """Join with another data source.

    Example YAML:
        - op: join
          right: customers  # Reference to another source
          on: [customer_id]
          how: left
    """

    op: Literal["join"] = "join"
    right: str = Field(..., description="Reference to the right dataset")
    on: list[str] = Field(..., description="Join key columns")
    how: Literal["inner", "left", "right", "outer"] = Field(
        default="inner",
        description="Join type",
    )


class AggregateTransform(BaseModel):
    """Group and aggregate data.

    Example YAML:
        - op: aggregate
          group_by: [region, category]
          aggs:
            total_revenue: sum(amount)
            order_count: count(*)
            avg_order: mean(amount)
    """

    op: Literal["aggregate"] = "aggregate"
    group_by: list[str] = Field(..., description="Columns to group by")
    aggs: dict[str, str] = Field(
        ...,
        description="Mapping of output column names to aggregation expressions",
    )


class UnionTransform(BaseModel):
    """Vertically concatenate multiple datasets.

    Example YAML:
        - op: union
          sources: [dataset1, dataset2]
    """

    op: Literal["union"] = "union"
    sources: list[str] = Field(
        ...,
        description="References to datasets to union",
    )


class LimitTransform(BaseModel):
    """Limit to first N rows.

    Example YAML:
        - op: limit
          n: 1000
    """

    op: Literal["limit"] = "limit"
    n: int = Field(..., description="Maximum number of rows", gt=0)


# Discriminated union for all transform types
TransformStep = Annotated[
    Union[
        SelectTransform,
        RenameTransform,
        FilterTransform,
        DeriveColumnTransform,
        CastTransform,
        FillNullTransform,
        DedupTransform,
        SortTransform,
        JoinTransform,
        AggregateTransform,
        UnionTransform,
        LimitTransform,
    ],
    Field(discriminator="op"),
]
