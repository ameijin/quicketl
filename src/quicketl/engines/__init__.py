"""ETLX engine abstraction layer.

Provides a unified interface to Ibis backends (DuckDB, Polars, Spark, etc.).
"""

from quicketl.engines.base import ETLXEngine
from quicketl.engines.backends import get_backend, list_backends, BackendConfig

__all__ = [
    "ETLXEngine",
    "get_backend",
    "list_backends",
    "BackendConfig",
]
