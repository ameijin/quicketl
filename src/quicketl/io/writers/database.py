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
    upsert_keys: list[str] | None = None,
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
            - 'upsert': Delete matching rows by key, then insert
        upsert_keys: Primary key columns for upsert mode (required when mode='upsert')
        **options: Additional connection options

    Returns:
        DatabaseWriteResult with operation details

    Raises:
        ValueError: If mode is 'upsert' but upsert_keys not provided

    Examples:
        >>> write_database(table, "postgresql://localhost/db", "output_table")
        >>> write_database(table, conn, "table", mode="replace")
        >>> write_database(table, conn, "table", mode="upsert", upsert_keys=["id"])
    """
    if mode == "upsert" and not upsert_keys:
        raise ValueError("upsert_keys are required when mode is 'upsert'")

    start = time.perf_counter()

    # Materialize the data to PyArrow for cross-backend compatibility
    # This allows writing data from any Ibis backend to any database
    arrow_table = table.to_pyarrow()
    row_count = len(arrow_table)

    # Connect to database
    con = ibis.connect(connection, **options)

    try:
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

            case "upsert":
                # Delete matching rows by key columns, then insert all new data.
                # If the table doesn't exist yet, just create it.
                assert upsert_keys is not None  # validated above
                try:
                    con.table(target_table)
                    # Build delete condition: match on all upsert keys
                    # Load new data into a temp table, delete matches, then insert
                    _temp_name = f"_upsert_staging_{target_table}"
                    con.create_table(_temp_name, arrow_table, overwrite=True)
                    try:
                        # Delete rows from target where keys match the incoming data
                        key_conditions = " AND ".join(
                            f'"{target_table}"."{k}" = "{_temp_name}"."{k}"'
                            for k in upsert_keys
                        )
                        delete_sql = (
                            f"DELETE FROM \"{target_table}\" WHERE EXISTS "
                            f"(SELECT 1 FROM \"{_temp_name}\" WHERE {key_conditions})"
                        )
                        con.raw_sql(delete_sql)
                        # Insert all new rows
                        con.insert(target_table, arrow_table)
                    finally:
                        with contextlib.suppress(Exception):
                            con.drop_table(_temp_name, force=True)
                except Exception:
                    # Table doesn't exist yet, create it
                    con.create_table(target_table, arrow_table)

            case _:
                raise ValueError(f"Unsupported write mode: {mode}")
    finally:
        with contextlib.suppress(Exception):
            con.disconnect()

    duration = (time.perf_counter() - start) * 1000

    return DatabaseWriteResult(
        rows_written=row_count,
        table=target_table,
        mode=mode,
        duration_ms=duration,
    )
