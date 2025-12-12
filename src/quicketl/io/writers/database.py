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
    mode: Literal["append", "truncate", "replace"] = "append",
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

    # Get row count
    row_count = table.count().execute()

    # Connect to database
    con = ibis.connect(connection, **options)

    # Handle different modes
    match mode:
        case "replace":
            # Drop existing table if exists, then create
            with contextlib.suppress(Exception):
                con.drop_table(target_table, force=True)
            con.create_table(target_table, table)

        case "truncate":
            # Truncate existing table, then insert
            with contextlib.suppress(Exception):
                con.truncate_table(target_table)
            con.insert(target_table, table)

        case "append":
            # Insert into existing table (create if not exists)
            try:
                con.insert(target_table, table)
            except Exception:
                # Table might not exist, create it
                con.create_table(target_table, table)

        case _:
            raise ValueError(f"Unsupported write mode: {mode}")

    duration = (time.perf_counter() - start) * 1000

    return DatabaseWriteResult(
        rows_written=row_count,
        table=target_table,
        mode=mode,
        duration_ms=duration,
    )
