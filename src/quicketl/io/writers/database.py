"""Database writers."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import ibis
import sqlglot as sg
from ibis.common.exceptions import TableNotFound

if TYPE_CHECKING:
    import ibis.expr.types as ir
    import pyarrow as pa


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
            - 'upsert': Update rows whose key matches, insert the rest
            For 'append', 'truncate' and 'upsert', a missing table is created.
            'truncate' runs its delete and insert in one transaction, so a
            failure leaves the original rows in place. 'upsert' uses the
            database's MERGE statement on DuckDB, Snowflake and BigQuery
            when there is a single key column. In every other case
            it deletes matching rows and inserts the new ones in one
            transaction. Either way, a failure leaves the original rows.
        upsert_keys: Primary key columns for upsert mode (required when mode='upsert')
        **options: Additional connection options

    Returns:
        DatabaseWriteResult with operation details

    Raises:
        ValueError: If mode is 'upsert' but upsert_keys not provided
        RuntimeError: If 'truncate' or 'upsert' runs on a backend that
            cannot start a transaction

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
                # overwrite=True swaps in the new table instead of dropping first
                con.create_table(target_table, arrow_table, overwrite=True)

            case "append" | "truncate" | "upsert" if not _table_exists(con, target_table):
                # Nothing to append to, clear, or match against yet
                con.create_table(target_table, arrow_table)

            case "append":
                con.insert(target_table, arrow_table)

            case "truncate":
                _replace_rows(con, target_table, arrow_table, keys=None)

            case "upsert":
                assert upsert_keys is not None  # validated above
                if _supports_native_upsert(con, upsert_keys, arrow_table.column_names):
                    con.upsert(target_table, ibis.memtable(arrow_table), on=upsert_keys[0])
                else:
                    _replace_rows(con, target_table, arrow_table, keys=upsert_keys)

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


# Backends where Ibis `upsert()` (MERGE INTO) is known to work. Other backends
# either lack MERGE (SQLite, MySQL, ClickHouse, Trino, ...) or have not been
# checked, so they keep the transaction based path. PostgreSQL is left out on
# purpose: MERGE needs PostgreSQL 15 or newer, and the transaction path works
# on every version.
_NATIVE_UPSERT_BACKENDS = frozenset({"duckdb", "snowflake", "bigquery"})


def _supports_native_upsert(con: Any, keys: list[str], columns: list[str]) -> bool:
    """Return True if this upsert can use the backend's MERGE statement.

    Ibis `upsert()` takes one key column and updates every other column, so
    it needs exactly one key and at least one non-key column.
    """
    return (
        con.name in _NATIVE_UPSERT_BACKENDS
        and hasattr(con, "upsert")
        and len(keys) == 1
        and any(c != keys[0] for c in columns)
    )


def _table_exists(con: Any, name: str) -> bool:
    """Return True if the table exists. Any error other than "not found" is raised."""
    try:
        con.table(name)
    except TableNotFound:
        return False
    return True


def _execute(con: Any, sql: str) -> None:
    """Run one SQL statement and close its cursor if the backend returns one.

    DuckDB returns its own connection from ``raw_sql`` instead of a cursor.
    Closing that would close the backend, so it is left open.
    """
    result = con.raw_sql(sql)
    if hasattr(result, "close") and result is not getattr(con, "con", None):
        result.close()


def _replace_rows(
    con: Any,
    target_table: str,
    arrow_table: pa.Table,
    keys: list[str] | None,
) -> None:
    """Delete rows from the target and insert the new rows in one transaction.

    The new rows are first copied into a staging table, outside the
    transaction. Only plain DELETE and INSERT statements run inside it,
    because some backends commit automatically on DDL such as CREATE TABLE.
    If anything fails, the transaction is rolled back, so the target keeps
    its original rows and the original error is raised.

    Args:
        con: Open Ibis backend connection.
        target_table: Table to write to. Must already exist.
        arrow_table: The new rows.
        keys: Key columns for upsert. Only target rows whose keys match an
            incoming row are deleted. None deletes every row (truncate).

    Raises:
        RuntimeError: If the backend does not support transactions.
    """
    dialect = con.dialect

    def q(name: str) -> str:
        return sg.to_identifier(name, quoted=True).sql(dialect)

    target, staging = q(target_table), q(f"_quicketl_staging_{target_table}")
    columns = ", ".join(q(c) for c in arrow_table.column_names)

    delete_sql = f"DELETE FROM {target}"
    if keys:
        matches = " AND ".join(f"{target}.{q(k)} = {staging}.{q(k)}" for k in keys)
        delete_sql += f" WHERE EXISTS (SELECT 1 FROM {staging} WHERE {matches})"
    insert_sql = f"INSERT INTO {target} ({columns}) SELECT {columns} FROM {staging}"

    con.create_table(f"_quicketl_staging_{target_table}", arrow_table, overwrite=True)
    try:
        try:
            _execute(con, "BEGIN")
        except Exception as e:
            raise RuntimeError(
                f"Write mode needs transaction support to avoid losing rows, "
                f"and the '{con.name}' backend could not start a transaction: {e}"
            ) from e
        try:
            _execute(con, delete_sql)
            _execute(con, insert_sql)
        except Exception:
            # Keep the original error; a failed rollback must not replace it
            with contextlib.suppress(Exception):
                _execute(con, "ROLLBACK")
            raise
        _execute(con, "COMMIT")
    finally:
        with contextlib.suppress(Exception):
            con.drop_table(f"_quicketl_staging_{target_table}", force=True)
