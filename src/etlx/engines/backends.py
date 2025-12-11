"""Backend configuration and factory functions.

Provides utilities for managing Ibis backend connections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from etlx.engines.base import ETLXEngine


@dataclass
class BackendConfig:
    """Configuration for a backend connection."""

    name: str
    connection_string: str | None = None
    options: dict[str, Any] | None = None

    def to_engine(self) -> ETLXEngine:
        """Create an ETLXEngine from this configuration."""
        return ETLXEngine(
            backend=self.name,
            connection_string=self.connection_string,
            **(self.options or {}),
        )


# Supported backends with their capabilities
BACKENDS = {
    # Local/embedded backends
    "duckdb": {
        "name": "DuckDB",
        "description": "Fast in-process analytical database",
        "supports_sql": True,
        "supports_file_io": True,
        "requires_connection": False,
    },
    "polars": {
        "name": "Polars",
        "description": "Rust-powered DataFrame library",
        "supports_sql": False,
        "supports_file_io": True,
        "requires_connection": False,
    },
    "datafusion": {
        "name": "DataFusion",
        "description": "Apache Arrow-native query engine",
        "supports_sql": True,
        "supports_file_io": True,
        "requires_connection": False,
    },
    "pandas": {
        "name": "pandas",
        "description": "Python DataFrame library",
        "supports_sql": False,
        "supports_file_io": True,
        "requires_connection": False,
    },
    # Distributed backends
    "spark": {
        "name": "Apache Spark",
        "description": "Distributed compute engine",
        "supports_sql": True,
        "supports_file_io": True,
        "requires_connection": True,
    },
    # Cloud data warehouses
    "bigquery": {
        "name": "Google BigQuery",
        "description": "Google Cloud data warehouse",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    "snowflake": {
        "name": "Snowflake",
        "description": "Cloud data platform",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    "trino": {
        "name": "Trino",
        "description": "Distributed SQL query engine",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    # Databases
    "postgres": {
        "name": "PostgreSQL",
        "description": "Open source relational database",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    "mysql": {
        "name": "MySQL",
        "description": "Open source relational database",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    "clickhouse": {
        "name": "ClickHouse",
        "description": "Column-oriented OLAP database",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": True,
    },
    "sqlite": {
        "name": "SQLite",
        "description": "Embedded relational database",
        "supports_sql": True,
        "supports_file_io": False,
        "requires_connection": False,
    },
}


def list_backends() -> list[dict[str, Any]]:
    """List all supported backends.

    Returns:
        List of backend info dictionaries
    """
    return [
        {"id": backend_id, **info}
        for backend_id, info in BACKENDS.items()
    ]


def get_backend(
    name: str,
    connection_string: str | None = None,
    **kwargs: Any,
) -> ETLXEngine:
    """Get an ETLXEngine for the specified backend.

    Args:
        name: Backend name (duckdb, polars, etc.)
        connection_string: Optional connection string
        **kwargs: Additional connection options

    Returns:
        Configured ETLXEngine

    Raises:
        ValueError: If backend is not supported

    Example:
        >>> engine = get_backend("duckdb")
        >>> engine = get_backend("postgres", "postgresql://user:pass@host/db")
    """
    if name not in BACKENDS:
        supported = ", ".join(BACKENDS.keys())
        raise ValueError(f"Unknown backend: {name}. Supported: {supported}")

    return ETLXEngine(
        backend=name,
        connection_string=connection_string,
        **kwargs,
    )


def get_backend_info(name: str) -> dict[str, Any]:
    """Get information about a specific backend.

    Args:
        name: Backend name

    Returns:
        Backend info dictionary

    Raises:
        ValueError: If backend is not supported
    """
    if name not in BACKENDS:
        supported = ", ".join(BACKENDS.keys())
        raise ValueError(f"Unknown backend: {name}. Supported: {supported}")

    return {"id": name, **BACKENDS[name]}
