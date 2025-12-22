"""OpenTelemetry integration for QuickETL.

Provides tracing and metrics for pipeline execution.
Requires: quicketl[opentelemetry]
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from opentelemetry import metrics, trace

if TYPE_CHECKING:
    from collections.abc import Iterator


class TracingContext:
    """OpenTelemetry tracing context for pipelines.

    Manages span creation and propagation across pipeline steps.

    Attributes:
        service_name: Name of the service for tracing.
    """

    def __init__(
        self,
        service_name: str = "quicketl",
        tracer_provider: Any = None,
    ) -> None:
        """Initialize tracing context.

        Args:
            service_name: Service name for spans.
            tracer_provider: Optional custom tracer provider.
        """
        self.service_name = service_name
        self._tracer = trace.get_tracer(
            service_name,
            tracer_provider=tracer_provider,
        )

    @contextmanager
    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Create a span for an operation.

        Args:
            name: Span name.
            attributes: Optional span attributes.

        Yields:
            The active span.
        """
        with self._tracer.start_as_current_span(
            name,
            attributes=attributes or {},
        ) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                raise


class MetricsContext:
    """OpenTelemetry metrics context for pipelines.

    Manages counters and histograms for pipeline metrics.

    Attributes:
        service_name: Name of the service for metrics.
    """

    def __init__(
        self,
        service_name: str = "quicketl",
        meter_provider: Any = None,
    ) -> None:
        """Initialize metrics context.

        Args:
            service_name: Service name for metrics.
            meter_provider: Optional custom meter provider.
        """
        self.service_name = service_name
        self._meter = metrics.get_meter(
            service_name,
            meter_provider=meter_provider,
        )
        self._rows_counter = self._meter.create_counter(
            "quicketl.rows.processed",
            description="Number of rows processed",
            unit="rows",
        )
        self._duration_histogram = self._meter.create_histogram(
            "quicketl.transform.duration",
            description="Transform execution duration",
            unit="s",
        )

    def record_rows_processed(
        self,
        count: int,
        transform_type: str | None = None,
    ) -> None:
        """Record rows processed count.

        Args:
            count: Number of rows processed.
            transform_type: Optional transform type label.
        """
        attributes = {}
        if transform_type:
            attributes["transform.type"] = transform_type
        self._rows_counter.add(count, attributes=attributes)

    def record_transform_duration(
        self,
        duration: float,
        transform_type: str | None = None,
    ) -> None:
        """Record transform execution duration.

        Args:
            duration: Duration in seconds.
            transform_type: Optional transform type label.
        """
        attributes = {}
        if transform_type:
            attributes["transform.type"] = transform_type
        self._duration_histogram.record(duration, attributes=attributes)
