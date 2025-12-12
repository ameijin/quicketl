"""QuickETL - Fast & Flexible Python ETL Framework.

QuickETL provides a simple, configuration-driven approach to building ETL pipelines
with support for 20+ backends via Ibis.

Example:
    >>> from quicketl import Pipeline
    >>> pipeline = Pipeline.from_yaml("pipeline.yml")
    >>> result = pipeline.run()
"""

from quicketl._version import __version__, __version_info__
from quicketl.pipeline.pipeline import Pipeline
from quicketl.pipeline.result import PipelineResult
from quicketl.engines.base import ETLXEngine

# Alias for the new package name
QuickETLEngine = ETLXEngine

__all__ = [
    "__version__",
    "__version_info__",
    "Pipeline",
    "PipelineResult",
    "ETLXEngine",
    "QuickETLEngine",
]
