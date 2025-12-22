"""Telemetry modules for QuickETL.

Provides OpenTelemetry tracing and metrics, and OpenLineage
data lineage integration.
"""

from quicketl.telemetry.context import get_correlation_id

__all__ = [
    "get_correlation_id",
]

# Conditional imports for optional dependencies
try:
    from quicketl.telemetry.opentelemetry import MetricsContext, TracingContext

    __all__.extend(["TracingContext", "MetricsContext"])
except ImportError:
    pass

try:
    from quicketl.telemetry import openlineage

    __all__.append("openlineage")
except ImportError:
    pass
