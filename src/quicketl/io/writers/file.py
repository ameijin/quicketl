"""File writers for various formats."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import time

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class WriteResult:
    """Result of a write operation."""

    rows_written: int
    path: str
    format: str
    duration_ms: float


def write_file(
    table: ir.Table,
    path: str,
    format: str = "parquet",
    partition_by: list[str] | None = None,
    **options: Any,
) -> WriteResult:
    """Write data to a file.

    Args:
        table: Ibis Table expression
        path: Output path (local or cloud URI)
        format: Output format (parquet, csv)
        partition_by: Columns to partition by (if supported)
        **options: Format-specific write options

    Returns:
        WriteResult with operation details

    Examples:
        >>> write_file(table, "output.parquet")
        >>> write_file(table, "s3://bucket/output/", partition_by=["date"])
    """
    start = time.perf_counter()

    # Get row count before writing
    row_count = table.count().execute()

    match format.lower():
        case "parquet" | "pq":
            table.to_parquet(path, **options)
        case "csv":
            table.to_csv(path, **options)
        case _:
            raise ValueError(f"Unsupported output format: {format}")

    duration = (time.perf_counter() - start) * 1000

    return WriteResult(
        rows_written=row_count,
        path=path,
        format=format,
        duration_ms=duration,
    )


def write_parquet(
    table: ir.Table,
    path: str,
    partition_by: list[str] | None = None,
    **options: Any,
) -> WriteResult:
    """Write to Parquet format.

    Args:
        table: Ibis Table expression
        path: Output path
        partition_by: Partition columns
        **options: Write options

    Returns:
        WriteResult
    """
    return write_file(table, path, "parquet", partition_by, **options)


def write_csv(
    table: ir.Table,
    path: str,
    **options: Any,
) -> WriteResult:
    """Write to CSV format.

    Args:
        table: Ibis Table expression
        path: Output path
        **options: Write options

    Returns:
        WriteResult
    """
    return write_file(table, path, "csv", **options)
