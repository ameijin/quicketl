"""QuickETL - Fast & Flexible Python ETL Framework.

QuickETL provides a simple, configuration-driven approach to building ETL pipelines
across many compute backends via Ibis.

Example:
    >>> from quicketl import Pipeline
    >>> pipeline = Pipeline.from_yaml("pipeline.yml")
    >>> result = pipeline.run()

The pipeline classes load lazily, on first use, so importing `quicketl` does not
import Ibis or the rest of the data stack.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from quicketl._version import __version__, __version_info__

if TYPE_CHECKING:
    from quicketl.engines.base import ETLXEngine, QuickETLEngine
    from quicketl.pipeline.pipeline import Pipeline
    from quicketl.pipeline.result import PipelineResult

# Top-level packages installed by the pipelines extra
_PIPELINE_STACK = {"ibis", "pyarrow", "pandas", "polars", "duckdb", "fsspec"}

# Public name -> module that defines it. Loaded on first attribute access.
_LAZY_EXPORTS = {
    "Pipeline": "quicketl.pipeline.pipeline",
    "PipelineResult": "quicketl.pipeline.result",
    "QuickETLEngine": "quicketl.engines.base",
    "ETLXEngine": "quicketl.engines.base",
}

__all__ = [
    "__version__",
    "__version_info__",
    "Pipeline",
    "PipelineResult",
    "QuickETLEngine",
    "ETLXEngine",  # Deprecated alias
]


def __getattr__(name: str) -> Any:
    """Import a pipeline class the first time it is used."""
    module = _LAZY_EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module 'quicketl' has no attribute {name!r}")
    try:
        loaded = importlib.import_module(module)
    except ModuleNotFoundError as e:
        # A missing data stack means the pipelines extra is not installed.
        if (e.name or "").split(".")[0] in _PIPELINE_STACK:
            from quicketl.cli._extras import PIPELINES_INSTALL_HINT

            raise ImportError(f"quicketl.{name}: {PIPELINES_INSTALL_HINT}") from e
        raise
    value = getattr(loaded, name)
    globals()[name] = value
    return value
