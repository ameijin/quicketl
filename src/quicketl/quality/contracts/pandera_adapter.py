"""Pandera adapter for QuickETL data contracts.

Provides schema validation using Pandera with Polars backend.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

try:
    import pandera.polars as pa
    from pandera.polars import Column, DataFrameSchema

    HAS_PANDERA = True
except ImportError:
    HAS_PANDERA = False
    pa = None  # type: ignore
    Column = None  # type: ignore
    DataFrameSchema = None  # type: ignore

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class ContractResult:
    """Result of contract validation."""

    passed: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    validated_rows: int = 0
    schema_name: str = ""


class PanderaContractValidator:
    """Validate Ibis tables against Pandera schemas.

    Example:
        >>> validator = PanderaContractValidator({
        ...     "columns": {
        ...         "id": {"dtype": "int64", "nullable": False, "unique": True},
        ...         "email": {"dtype": "str", "checks": ["str_matches('^[^@]+@[^@]+$')"]},
        ...         "amount": {"dtype": "float64", "checks": ["ge(0)"]},
        ...     },
        ...     "strict": False,
        ... })
        >>> result = validator.validate(table)
        >>> print(result.passed)
    """

    def __init__(self, schema_config: dict[str, Any]):
        """Initialize validator with schema configuration.

        Args:
            schema_config: Schema definition with columns and checks.

        Raises:
            ImportError: If pandera is not installed.
        """
        if not HAS_PANDERA:
            raise ImportError(
                "pandera is required for contract validation. "
                "Install with: pip install quicketl[contracts]"
            )
        self.schema = self._build_schema(schema_config)
        self.schema_name = schema_config.get("name", "")

    def _build_schema(self, config: dict[str, Any]) -> DataFrameSchema:
        """Build Pandera schema from config dict.

        Args:
            config: Schema configuration with columns and checks.

        Returns:
            Pandera DataFrameSchema.
        """
        columns = {}
        for col_name, col_config in config.get("columns", {}).items():
            if isinstance(col_config, dict):
                dtype = self._map_dtype(col_config.get("dtype", "str"))
                nullable = col_config.get("nullable", True)
                unique = col_config.get("unique", False)
                checks = self._parse_checks(col_config.get("checks", []))

                columns[col_name] = Column(
                    dtype=dtype,
                    nullable=nullable,
                    unique=unique,
                    checks=checks if checks else None,
                )
            else:
                # Simple dtype string
                columns[col_name] = Column(dtype=self._map_dtype(col_config))

        return DataFrameSchema(
            columns=columns,
            strict=config.get("strict", False),
        )

    def _map_dtype(self, dtype: str) -> Any:
        """Map dtype string to Polars/Pandera dtype.

        Args:
            dtype: String dtype like 'int64', 'float64', 'str'.

        Returns:
            Polars dtype.
        """
        import polars as pl

        dtype_map = {
            "int8": pl.Int8,
            "int16": pl.Int16,
            "int32": pl.Int32,
            "int64": pl.Int64,
            "uint8": pl.UInt8,
            "uint16": pl.UInt16,
            "uint32": pl.UInt32,
            "uint64": pl.UInt64,
            "float32": pl.Float32,
            "float64": pl.Float64,
            "str": pl.Utf8,
            "string": pl.Utf8,
            "bool": pl.Boolean,
            "boolean": pl.Boolean,
            "date": pl.Date,
            "datetime": pl.Datetime,
            "time": pl.Time,
        }
        return dtype_map.get(dtype.lower(), pl.Utf8)

    def _parse_checks(self, check_strs: list[str]) -> list[Any]:
        """Parse check strings into Pandera checks.

        Args:
            check_strs: List of check strings like 'ge(0)', 'le(100)'.

        Returns:
            List of Pandera Check objects.
        """
        checks = []
        for check_str in check_strs:
            check = self._parse_single_check(check_str)
            if check is not None:
                checks.append(check)
        return checks

    def _parse_single_check(self, check_str: str) -> Any:
        """Parse a single check string into a Pandera check.

        Args:
            check_str: Check string like 'ge(0)' or 'str_matches(...)'.

        Returns:
            Pandera Check object or None if not recognized.
        """
        check_str = check_str.strip()

        # Numeric comparisons
        if check_str.startswith("ge(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.ge(val)
        elif check_str.startswith("le(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.le(val)
        elif check_str.startswith("gt(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.gt(val)
        elif check_str.startswith("lt(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.lt(val)
        elif check_str.startswith("eq(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.eq(val)
        elif check_str.startswith("ne(") and check_str.endswith(")"):
            val = float(check_str[3:-1])
            return pa.Check.ne(val)

        # Between check
        elif check_str.startswith("between(") and check_str.endswith(")"):
            parts = check_str[8:-1].split(",")
            if len(parts) == 2:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return pa.Check.in_range(min_val, max_val)

        # String pattern matching
        elif check_str.startswith("str_matches(") and check_str.endswith(")"):
            # Extract pattern - handle quoted strings
            pattern = check_str[12:-1]
            # Remove surrounding quotes if present
            if (pattern.startswith("'") and pattern.endswith("'")) or \
               (pattern.startswith('"') and pattern.endswith('"')):
                pattern = pattern[1:-1]
            return pa.Check.str_matches(pattern)

        # String length
        elif check_str.startswith("str_length(") and check_str.endswith(")"):
            parts = check_str[11:-1].split(",")
            if len(parts) == 2:
                min_len = int(parts[0].strip())
                max_len = int(parts[1].strip())
                return pa.Check.str_length(min_len, max_len)

        # In set check
        elif check_str.startswith("isin(") and check_str.endswith(")"):
            # Parse list - e.g., isin(['a', 'b', 'c'])
            list_str = check_str[5:-1]
            try:
                values = ast.literal_eval(list_str)
                return pa.Check.isin(values)
            except (ValueError, SyntaxError):
                pass

        return None

    def validate(self, table: ir.Table) -> ContractResult:
        """Validate Ibis table against schema.

        Args:
            table: Ibis Table expression to validate.

        Returns:
            ContractResult with validation outcome.
        """
        # Convert to Polars for Pandera validation
        try:
            df = table.to_polars()
        except Exception as e:
            return ContractResult(
                passed=False,
                errors=[{"error": f"Failed to convert table to Polars: {e}"}],
                validated_rows=0,
                schema_name=self.schema_name,
            )

        row_count = len(df)

        try:
            self.schema.validate(df, lazy=True)
            return ContractResult(
                passed=True,
                validated_rows=row_count,
                schema_name=self.schema_name,
            )
        except pa.errors.SchemaErrors as e:
            # Extract failure cases
            errors = []
            if hasattr(e, "failure_cases") and e.failure_cases is not None:
                try:
                    errors = e.failure_cases.to_dicts()
                except Exception:
                    errors = [{"error": str(e)}]
            else:
                errors = [{"error": str(e)}]

            return ContractResult(
                passed=False,
                errors=errors,
                validated_rows=row_count,
                schema_name=self.schema_name,
            )
        except Exception as e:
            return ContractResult(
                passed=False,
                errors=[{"error": f"Validation error: {e}"}],
                validated_rows=row_count,
                schema_name=self.schema_name,
            )
