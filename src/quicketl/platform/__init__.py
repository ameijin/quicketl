"""Platform scaffolding: the platform spec and the commands built on it.

This package is part of the core install and must not import the pipeline
data stack (Ibis, pyarrow, pandas, Polars, DuckDB, fsspec).
"""

from __future__ import annotations

from quicketl.platform.spec import (
    PLATFORM_FILE,
    PlatformSpec,
    PlatformSpecError,
    load_platform_spec,
)

__all__ = ["PLATFORM_FILE", "PlatformSpec", "PlatformSpecError", "load_platform_spec"]
