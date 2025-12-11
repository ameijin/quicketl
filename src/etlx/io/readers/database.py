"""Database readers.

Wraps Ibis database connection and query capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import ibis.expr.types as ir


def read_database(
    connection: str,
    query: str | None = None,
    table: str | None = None,
    **options: Any,
) -> ir.Table:
    """Read data from a database.

    Args:
        connection: Connection string (e.g., postgresql://user:pass@host/db)
        query: SQL query to execute
        table: Table name (alternative to query)
        **options: Additional connection options

    Returns:
        Ibis Table expression

    Raises:
        ValueError: If neither query nor table is provided

    Examples:
        >>> table = read_database("postgresql://localhost/mydb", query="SELECT * FROM users")
        >>> table = read_database("postgresql://localhost/mydb", table="users")
    """
    if query is None and table is None:
        raise ValueError("Either 'query' or 'table' must be provided")

    # Connect to database
    con = ibis.connect(connection, **options)

    if query:
        return con.sql(query)
    else:
        return con.table(table)


def read_sql(
    connection: str,
    query: str,
    **options: Any,
) -> ir.Table:
    """Execute a SQL query and return results.

    Args:
        connection: Connection string
        query: SQL query
        **options: Additional connection options

    Returns:
        Ibis Table expression
    """
    return read_database(connection, query=query, **options)


def read_table(
    connection: str,
    table: str,
    **options: Any,
) -> ir.Table:
    """Read an entire table.

    Args:
        connection: Connection string
        table: Table name
        **options: Additional connection options

    Returns:
        Ibis Table expression
    """
    return read_database(connection, table=table, **options)
