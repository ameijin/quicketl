"""QuickETL engine abstraction layer.

Provides a unified interface to Ibis backends (DuckDB, Polars, Spark, etc.).
"""

from quicketl.engines.backends import BackendConfig, get_backend, list_backends
from quicketl.engines.base import ETLXEngine, QuickETLEngine

__all__ = [
    "QuickETLEngine",
    "ETLXEngine",  # Deprecated alias
    "get_backend",
    "list_backends",
    "BackendConfig",
]
