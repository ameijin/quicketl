"""Quality check configuration models.

Defines the 5 core quality checks as a Pydantic discriminated union.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


class NotNullCheck(BaseModel):
    """Check that specified columns contain no null values.

    Example YAML:
        - type: not_null
          columns: [id, name, email]
    """

    type: Literal["not_null"] = "not_null"
    columns: list[str] = Field(
        ...,
        description="Columns that must not contain null values",
    )


class UniqueCheck(BaseModel):
    """Check that specified columns are unique (no duplicates).

    Example YAML:
        - type: unique
          columns: [id]

        # Or for composite uniqueness:
        - type: unique
          columns: [date, customer_id, product_id]
    """

    type: Literal["unique"] = "unique"
    columns: list[str] = Field(
        ...,
        description="Columns that must be unique (composite if multiple)",
    )


class RowCountCheck(BaseModel):
    """Check that row count is within expected bounds.

    Example YAML:
        - type: row_count
          min: 1
          max: 1000000

        # Or just minimum:
        - type: row_count
          min: 1
    """

    type: Literal["row_count"] = "row_count"
    min: int | None = Field(
        default=None,
        description="Minimum expected row count",
        ge=0,
    )
    max: int | None = Field(
        default=None,
        description="Maximum expected row count",
        ge=0,
    )


class AcceptedValuesCheck(BaseModel):
    """Check that a column contains only expected values.

    Example YAML:
        - type: accepted_values
          column: status
          values: [pending, active, completed, cancelled]
    """

    type: Literal["accepted_values"] = "accepted_values"
    column: str = Field(..., description="Column to check")
    values: list[Any] = Field(
        ...,
        description="List of accepted values",
    )


class ExpressionCheck(BaseModel):
    """Check that a custom SQL expression evaluates to true for all rows.

    Example YAML:
        - type: expression
          expr: amount >= 0

        # Or more complex:
        - type: expression
          expr: end_date >= start_date
    """

    type: Literal["expression"] = "expression"
    expr: str = Field(
        ...,
        description="SQL-like expression that must be true for all rows",
    )


# Discriminated union for all check types
CheckConfig = Annotated[
    Union[
        NotNullCheck,
        UniqueCheck,
        RowCountCheck,
        AcceptedValuesCheck,
        ExpressionCheck,
    ],
    Field(discriminator="type"),
]
