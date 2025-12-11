"""File readers for various formats.

Wraps Ibis file reading capabilities with additional options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import ibis.expr.types as ir


def read_file(
    path: str,
    format: str,
    backend: ibis.BaseBackend | None = None,
    **options: Any,
) -> ir.Table:
    """Read data from a file.

    Args:
        path: File path (local or cloud URI like s3://, gs://, abfss://)
        format: File format (parquet, csv, json)
        backend: Optional Ibis backend (creates DuckDB if not provided)
        **options: Format-specific read options

    Returns:
        Ibis Table expression

    Examples:
        >>> table = read_file("data.parquet", "parquet")
        >>> table = read_file("s3://bucket/data.csv", "csv", header=True)
    """
    if backend is None:
        backend = ibis.duckdb.connect()

    match format.lower():
        case "parquet" | "pq":
            return backend.read_parquet(path, **options)
        case "csv":
            return backend.read_csv(path, **options)
        case "json" | "jsonl" | "ndjson":
            return backend.read_json(path, **options)
        case _:
            raise ValueError(f"Unsupported file format: {format}")


def read_parquet(
    path: str,
    backend: ibis.BaseBackend | None = None,
    **options: Any,
) -> ir.Table:
    """Read a Parquet file.

    Args:
        path: File path
        backend: Optional Ibis backend
        **options: Read options

    Returns:
        Ibis Table expression
    """
    return read_file(path, "parquet", backend, **options)


def read_csv(
    path: str,
    backend: ibis.BaseBackend | None = None,
    **options: Any,
) -> ir.Table:
    """Read a CSV file.

    Args:
        path: File path
        backend: Optional Ibis backend
        **options: Read options (header, delimiter, etc.)

    Returns:
        Ibis Table expression
    """
    return read_file(path, "csv", backend, **options)


def read_json(
    path: str,
    backend: ibis.BaseBackend | None = None,
    **options: Any,
) -> ir.Table:
    """Read a JSON/JSONL file.

    Args:
        path: File path
        backend: Optional Ibis backend
        **options: Read options

    Returns:
        Ibis Table expression
    """
    return read_file(path, "json", backend, **options)
