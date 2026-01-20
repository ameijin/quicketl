"""Quality check implementations using Ibis.

Each check returns a CheckResult with pass/fail status and details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis
    import ibis.expr.types as ir

from quicketl.config.checks import (
    AcceptedValuesCheck,
    CheckConfig,
    ContractCheck,
    ExpressionCheck,
    NotNullCheck,
    RowCountCheck,
    UniqueCheck,
)


@dataclass
class CheckResult:
    """Result of a quality check execution."""

    check_type: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.check_type}: {self.message}"


def run_not_null_check(table: ir.Table, config: NotNullCheck) -> CheckResult:
    """Check that specified columns contain no null values.

    Args:
        table: Ibis Table expression
        config: NotNullCheck configuration

    Returns:
        CheckResult with null counts per column
    """
    null_counts: dict[str, int] = {}
    total_nulls = 0

    for col in config.columns:
        if col not in table.columns:
            return CheckResult(
                check_type="not_null",
                passed=False,
                message=f"Column '{col}' not found in table",
                details={"missing_column": col, "available_columns": list(table.columns)},
            )

        null_count = table.filter(table[col].isnull()).count().execute()
        null_counts[col] = null_count
        total_nulls += null_count

    if total_nulls > 0:
        failed_cols = [col for col, count in null_counts.items() if count > 0]
        return CheckResult(
            check_type="not_null",
            passed=False,
            message=f"Found null values in columns: {failed_cols}",
            details={"null_counts": null_counts},
        )

    return CheckResult(
        check_type="not_null",
        passed=True,
        message=f"All {len(config.columns)} columns have no null values",
        details={"columns_checked": config.columns},
    )


def run_unique_check(table: ir.Table, config: UniqueCheck) -> CheckResult:
    """Check that specified columns are unique (no duplicates).

    Args:
        table: Ibis Table expression
        config: UniqueCheck configuration

    Returns:
        CheckResult with duplicate count
    """
    for col in config.columns:
        if col not in table.columns:
            return CheckResult(
                check_type="unique",
                passed=False,
                message=f"Column '{col}' not found in table",
                details={"missing_column": col, "available_columns": list(table.columns)},
            )

    total_rows = table.count().execute()

    # Count distinct combinations
    distinct_count = table.select(config.columns).distinct().count().execute()

    duplicate_count = total_rows - distinct_count

    if duplicate_count > 0:
        return CheckResult(
            check_type="unique",
            passed=False,
            message=f"Found {duplicate_count} duplicate rows",
            details={
                "columns": config.columns,
                "total_rows": total_rows,
                "distinct_rows": distinct_count,
                "duplicate_count": duplicate_count,
            },
        )

    return CheckResult(
        check_type="unique",
        passed=True,
        message=f"All {total_rows} rows are unique across {config.columns}",
        details={"columns": config.columns, "row_count": total_rows},
    )


def run_row_count_check(table: ir.Table, config: RowCountCheck) -> CheckResult:
    """Check that row count is within expected bounds.

    Args:
        table: Ibis Table expression
        config: RowCountCheck configuration

    Returns:
        CheckResult with actual row count
    """
    row_count = table.count().execute()

    # Check minimum
    if config.min is not None and row_count < config.min:
        return CheckResult(
            check_type="row_count",
            passed=False,
            message=f"Row count {row_count} is below minimum {config.min}",
            details={
                "actual": row_count,
                "min": config.min,
                "max": config.max,
            },
        )

    # Check maximum
    if config.max is not None and row_count > config.max:
        return CheckResult(
            check_type="row_count",
            passed=False,
            message=f"Row count {row_count} exceeds maximum {config.max}",
            details={
                "actual": row_count,
                "min": config.min,
                "max": config.max,
            },
        )

    bounds_str = ""
    if config.min is not None and config.max is not None:
        bounds_str = f" (expected {config.min}-{config.max})"
    elif config.min is not None:
        bounds_str = f" (min {config.min})"
    elif config.max is not None:
        bounds_str = f" (max {config.max})"

    return CheckResult(
        check_type="row_count",
        passed=True,
        message=f"Row count {row_count} is within bounds{bounds_str}",
        details={"actual": row_count, "min": config.min, "max": config.max},
    )


def run_accepted_values_check(table: ir.Table, config: AcceptedValuesCheck) -> CheckResult:
    """Check that a column contains only expected values.

    Args:
        table: Ibis Table expression
        config: AcceptedValuesCheck configuration

    Returns:
        CheckResult with unexpected values if any
    """
    if config.column not in table.columns:
        return CheckResult(
            check_type="accepted_values",
            passed=False,
            message=f"Column '{config.column}' not found in table",
            details={
                "missing_column": config.column,
                "available_columns": list(table.columns),
            },
        )

    # Find rows with values not in accepted list
    col = table[config.column]
    invalid_rows = table.filter(~col.isin(config.values))
    invalid_count = invalid_rows.count().execute()

    if invalid_count > 0:
        # Get sample of unexpected values (up to 10)
        unexpected_values = (
            invalid_rows.select(config.column)
            .distinct()
            .limit(10)
            .execute()[config.column]
            .tolist()
        )

        return CheckResult(
            check_type="accepted_values",
            passed=False,
            message=f"Found {invalid_count} rows with unexpected values in '{config.column}'",
            details={
                "column": config.column,
                "accepted_values": config.values,
                "unexpected_values": unexpected_values,
                "invalid_row_count": invalid_count,
            },
        )

    return CheckResult(
        check_type="accepted_values",
        passed=True,
        message=f"All values in '{config.column}' are in accepted list",
        details={"column": config.column, "accepted_values": config.values},
    )


def run_expression_check(table: ir.Table, config: ExpressionCheck) -> CheckResult:
    """Check that a custom SQL expression evaluates to true for all rows.

    Args:
        table: Ibis Table expression
        config: ExpressionCheck configuration

    Returns:
        CheckResult with failing row count
    """
    try:
        # Parse the expression into an Ibis expression
        expr = _parse_predicate(table, config.expr)

        # Count rows where expression is NOT true
        failing_rows = table.filter(~expr)
        failing_count = failing_rows.count().execute()
        total_rows = table.count().execute()

        if failing_count > 0:
            return CheckResult(
                check_type="expression",
                passed=False,
                message=f"{failing_count} of {total_rows} rows failed expression: {config.expr}",
                details={
                    "expression": config.expr,
                    "failing_rows": failing_count,
                    "total_rows": total_rows,
                    "pass_rate": (total_rows - failing_count) / total_rows if total_rows > 0 else 0,
                },
            )

        return CheckResult(
            check_type="expression",
            passed=True,
            message=f"All {total_rows} rows pass expression: {config.expr}",
            details={"expression": config.expr, "total_rows": total_rows},
        )

    except Exception as e:
        return CheckResult(
            check_type="expression",
            passed=False,
            message=f"Failed to evaluate expression: {config.expr}",
            details={"expression": config.expr, "error": str(e)},
        )


def _parse_predicate(table: ir.Table, predicate: str) -> ibis.Expr:
    """Parse a simple SQL-like predicate into an Ibis expression."""

    # Handle comparison operators
    for op_str, op_func in [
        (">=", lambda col, val: col >= val),
        ("<=", lambda col, val: col <= val),
        ("!=", lambda col, val: col != val),
        ("=", lambda col, val: col == val),
        (">", lambda col, val: col > val),
        ("<", lambda col, val: col < val),
    ]:
        if op_str in predicate:
            parts = predicate.split(op_str)
            if len(parts) == 2:
                col_name = parts[0].strip()
                val_str = parts[1].strip()

                # Parse the value
                val = _parse_value(val_str)
                return op_func(table[col_name], val)

    # Handle boolean column references (e.g., "active" or "NOT active")
    predicate_lower = predicate.strip().lower()
    if predicate_lower.startswith("not "):
        col_name = predicate.strip()[4:].strip()
        return ~table[col_name]
    elif predicate.strip() in table.columns:
        return table[predicate.strip()]

    raise ValueError(f"Unable to parse predicate: {predicate}")


def _parse_value(val_str: str) -> Any:
    """Parse a string value into the appropriate Python type."""
    val_str = val_str.strip()

    # Handle quoted strings
    if (val_str.startswith("'") and val_str.endswith("'")) or \
       (val_str.startswith('"') and val_str.endswith('"')):
        return val_str[1:-1]

    # Handle booleans
    if val_str.lower() in ("true", "false"):
        return val_str.lower() == "true"

    # Handle numbers
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


def run_contract_check(table: ir.Table, config: ContractCheck) -> CheckResult:
    """Run Pandera contract validation.

    Args:
        table: Ibis Table expression
        config: ContractCheck configuration

    Returns:
        CheckResult with validation details
    """
    try:
        from quicketl.quality.contracts.pandera_adapter import PanderaContractValidator

        # Merge schema config with strict setting
        schema_config = dict(config.contract_schema)
        if "strict" not in schema_config:
            schema_config["strict"] = config.strict

        validator = PanderaContractValidator(schema_config)
        result = validator.validate(table)

        if result.passed:
            return CheckResult(
                check_type="contract",
                passed=True,
                message=f"Contract validation passed for {result.validated_rows} rows",
                details={
                    "validated_rows": result.validated_rows,
                    "schema_name": result.schema_name,
                },
            )
        else:
            return CheckResult(
                check_type="contract",
                passed=False,
                message="Contract validation failed",
                details={
                    "validated_rows": result.validated_rows,
                    "errors": result.errors,
                    "schema_name": result.schema_name,
                },
            )
    except ImportError as e:
        return CheckResult(
            check_type="contract",
            passed=False,
            message=str(e),
            details={"error": "pandera_not_installed"},
        )
    except Exception as e:
        return CheckResult(
            check_type="contract",
            passed=False,
            message=f"Contract validation error: {e}",
            details={"error": str(e)},
        )


def run_check(table: ir.Table, config: CheckConfig) -> CheckResult:
    """Run a quality check based on its configuration.

    Args:
        table: Ibis Table expression
        config: CheckConfig (discriminated union)

    Returns:
        CheckResult
    """
    match config:
        case NotNullCheck():
            return run_not_null_check(table, config)
        case UniqueCheck():
            return run_unique_check(table, config)
        case RowCountCheck():
            return run_row_count_check(table, config)
        case AcceptedValuesCheck():
            return run_accepted_values_check(table, config)
        case ExpressionCheck():
            return run_expression_check(table, config)
        case ContractCheck():
            return run_contract_check(table, config)
        case _:
            return CheckResult(
                check_type="unknown",
                passed=False,
                message=f"Unknown check type: {type(config).__name__}",
                details={},
            )
