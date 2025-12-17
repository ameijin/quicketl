"""Database writers."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import ibis

if TYPE_CHECKING:
    import ibis.expr.types as ir


@dataclass
class DatabaseWriteResult:
    """Result of a database write operation."""

    rows_written: int
    table: str
    mode: str
    duration_ms: float


def write_database(
    table: ir.Table,
    connection: str,
    target_table: str,
    mode: Literal["append", "truncate", "replace", "upsert"] = "append",
    **options: Any,
) -> DatabaseWriteResult:
    """Write data to a database table.

    Args:
        table: Ibis Table expression
        connection: Database connection string
        target_table: Target table name
        mode: Write mode
            - 'append': Add rows to existing table
            - 'truncate': Clear table and insert
            - 'replace': Drop and recreate table
        **options: Additional connection options

    Returns:
        DatabaseWriteResult with operation details

    Examples:
        >>> write_database(table, "postgresql://localhost/db", "output_table")
        >>> write_database(table, conn, "table", mode="replace")
    """
    start = time.perf_counter()

    # Materialize the data to PyArrow for cross-backend compatibility
    # This allows writing data from any Ibis backend to any database
    arrow_table = table.to_pyarrow()
    row_count = len(arrow_table)

    # Connect to database
    con = ibis.connect(connection, **options)

    # Handle different modes
    match mode:
        case "replace":
            # Drop existing table if exists, then create from Arrow
            with contextlib.suppress(Exception):
                con.drop_table(target_table, force=True)
            con.create_table(target_table, arrow_table)

        case "truncate":
            # Check if table exists first
            try:
                con.table(target_table)  # Raises if table doesn't exist
                # Table exists - use raw SQL to truncate since not all backends support truncate_table
                with contextlib.suppress(Exception):
                    con.raw_sql(f"DELETE FROM {target_table}")
                con.insert(target_table, arrow_table)
            except Exception:
                # Table doesn't exist, create it
                con.create_table(target_table, arrow_table)

        case "append":
            # Insert into existing table (create if not exists)
            try:
                con.insert(target_table, arrow_table)
            except Exception:
                # Table might not exist, create it
                con.create_table(target_table, arrow_table)

        case _:
            raise ValueError(f"Unsupported write mode: {mode}")

    duration = (time.perf_counter() - start) * 1000

    return DatabaseWriteResult(
        rows_written=row_count,
        table=target_table,
        mode=mode,
        duration_ms=duration,
    )
