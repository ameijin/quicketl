"""Data contract schema definitions.

Provides Pydantic models for defining data contracts that can be
validated using Pandera.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ColumnContract(BaseModel):
    """Contract specification for a single column.

    Defines the expected data type, nullability, uniqueness, and
    validation checks for a column.

    Example:
        >>> col = ColumnContract(
        ...     name="order_id",
        ...     dtype="int64",
        ...     nullable=False,
        ...     unique=True,
        ...     description="Primary key for orders",
        ... )
    """

    name: str = Field(..., description="Column name")
    dtype: str = Field(
        ...,
        description="Expected data type (int64, float64, str, bool, datetime, date)",
    )
    nullable: bool = Field(default=True, description="Whether nulls are allowed")
    unique: bool = Field(default=False, description="Whether values must be unique")
    checks: list[str] = Field(
        default_factory=list,
        description="Validation checks (e.g., 'ge(0)', 'le(100)', 'str_matches(...)')",
    )
    description: str = Field(default="", description="Column documentation")


class DataContract(BaseModel):
    """Complete data contract definition.

    Defines the expected schema for a dataset including column specifications,
    versioning, and ownership information.

    Example YAML file (contracts/orders_v1.yml):
        name: orders
        version: "1.0.0"
        owner: data-team
        description: Order transaction data
        columns:
          - name: order_id
            dtype: int64
            nullable: false
            unique: true
          - name: amount
            dtype: float64
            checks: ["ge(0)"]
          - name: status
            dtype: str
            checks: ["isin(['pending', 'completed', 'cancelled'])"]

    Example:
        >>> contract = DataContract(
        ...     name="orders",
        ...     version="1.0.0",
        ...     owner="data-team",
        ...     columns=[
        ...         ColumnContract(name="order_id", dtype="int64", nullable=False, unique=True),
        ...         ColumnContract(name="amount", dtype="float64", checks=["ge(0)"]),
        ...     ],
        ... )
        >>> pandera_config = contract.to_pandera_config()
    """

    name: str = Field(..., description="Contract name")
    version: str = Field(default="1.0.0", description="Semantic version")
    owner: str = Field(default="", description="Team or person responsible")
    description: str = Field(default="", description="Contract documentation")
    columns: list[ColumnContract] = Field(..., description="Column specifications")
    strict: bool = Field(
        default=False,
        description="Reject columns not in contract (default: allow extra columns)",
    )

    def to_pandera_config(self) -> dict[str, Any]:
        """Convert to Pandera-compatible configuration dict.

        Returns:
            Dict that can be passed to PanderaContractValidator.
        """
        columns: dict[str, dict[str, Any]] = {}
        for col in self.columns:
            columns[col.name] = {
                "dtype": col.dtype,
                "nullable": col.nullable,
                "unique": col.unique,
                "checks": col.checks,
            }
        return {
            "name": self.name,
            "columns": columns,
            "strict": self.strict,
        }

    def get_column(self, name: str) -> ColumnContract | None:
        """Get a column contract by name.

        Args:
            name: Column name to find.

        Returns:
            ColumnContract if found, None otherwise.
        """
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def column_names(self) -> list[str]:
        """Get list of all column names in contract.

        Returns:
            List of column names.
        """
        return [col.name for col in self.columns]

    def required_columns(self) -> list[str]:
        """Get list of required (non-nullable) column names.

        Returns:
            List of column names that cannot be null.
        """
        return [col.name for col in self.columns if not col.nullable]

    def unique_columns(self) -> list[str]:
        """Get list of unique column names.

        Returns:
            List of column names that must be unique.
        """
        return [col.name for col in self.columns if col.unique]
