"""ETLX Framework - Unified ETL/ELT for Python.

ETLX provides a simple, configuration-driven approach to building ETL pipelines
with support for 20+ backends via Ibis.

Example:
    >>> from etlx import Pipeline
    >>> pipeline = Pipeline.from_yaml("pipeline.yml")
    >>> result = pipeline.run()
"""

from etlx._version import __version__, __version_info__
from etlx.pipeline.pipeline import Pipeline
from etlx.pipeline.result import PipelineResult
from etlx.engines.base import ETLXEngine

__all__ = [
    "__version__",
    "__version_info__",
    "Pipeline",
    "PipelineResult",
    "ETLXEngine",
]
