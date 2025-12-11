"""ETLX engine abstraction layer.

Provides a unified interface to Ibis backends (DuckDB, Polars, Spark, etc.).
"""

from etlx.engines.base import ETLXEngine
from etlx.engines.backends import get_backend, list_backends, BackendConfig

__all__ = [
    "ETLXEngine",
    "get_backend",
    "list_backends",
    "BackendConfig",
]
