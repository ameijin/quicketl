"""Tests for OpenTelemetry integration.

This module tests:
- Span creation per transform
- Span attributes (transform type, row count)
- Pipeline trace propagation
- Error recording in spans
- Metrics (rows processed, duration)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestOpenTelemetryIntegration:
    """Tests for OpenTelemetry tracing integration."""

    def test_span_created_per_transform(self):
        """Each transform operation creates a span."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            ctx = TracingContext(service_name="quicketl-test")

            with ctx.span("filter_transform"):
                pass

            mock_tracer.start_as_current_span.assert_called_once()
            call_name = mock_tracer.start_as_current_span.call_args[0][0]
            assert "filter_transform" in call_name

    def test_span_attributes_include_transform_type(self):
        """Spans include transform type as attribute."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            ctx = TracingContext(service_name="quicketl-test")

            with ctx.span("transform", attributes={"transform.type": "filter"}):
                pass

            # Verify attributes were passed
            call_kwargs = mock_tracer.start_as_current_span.call_args[1]
            assert "attributes" in call_kwargs
            assert call_kwargs["attributes"]["transform.type"] == "filter"

    def test_span_attributes_include_row_count(self):
        """Spans can include row count as attribute."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            ctx = TracingContext(service_name="quicketl-test")

            with ctx.span("transform", attributes={"rows.count": 1000}):
                pass

            call_kwargs = mock_tracer.start_as_current_span.call_args[1]
            assert call_kwargs["attributes"]["rows.count"] == 1000

    def test_pipeline_trace_propagation(self):
        """Trace context propagates across pipeline steps."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            ctx = TracingContext(service_name="quicketl-test")

            # Nested spans should propagate context
            with ctx.span("pipeline"):
                with ctx.span("step1"):
                    pass
                with ctx.span("step2"):
                    pass

            # Should have created 3 spans
            assert mock_tracer.start_as_current_span.call_count == 3

    def test_error_recorded_in_span(self):
        """Errors are recorded in the span."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace") as mock_trace:
            mock_tracer = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            ctx = TracingContext(service_name="quicketl-test")

            with pytest.raises(ValueError), ctx.span("failing_transform"):
                raise ValueError("Test error")

            # Verify error was recorded
            mock_span.record_exception.assert_called_once()


class TestMetrics:
    """Tests for OpenTelemetry metrics."""

    def test_rows_processed_counter(self):
        """Rows processed counter increments correctly."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import MetricsContext

        with patch("quicketl.telemetry.opentelemetry.metrics") as mock_metrics:
            mock_meter = MagicMock()
            mock_metrics.get_meter.return_value = mock_meter
            mock_counter = MagicMock()
            mock_meter.create_counter.return_value = mock_counter

            ctx = MetricsContext(service_name="quicketl-test")
            ctx.record_rows_processed(1000, transform_type="filter")

            mock_counter.add.assert_called_once()
            call_args = mock_counter.add.call_args
            assert call_args[0][0] == 1000

    def test_transform_duration_histogram(self):
        """Transform duration is recorded as histogram."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import MetricsContext

        with patch("quicketl.telemetry.opentelemetry.metrics") as mock_metrics:
            mock_meter = MagicMock()
            mock_metrics.get_meter.return_value = mock_meter
            mock_histogram = MagicMock()
            mock_meter.create_histogram.return_value = mock_histogram

            ctx = MetricsContext(service_name="quicketl-test")
            ctx.record_transform_duration(0.5, transform_type="filter")

            mock_histogram.record.assert_called_once()
            call_args = mock_histogram.record.call_args
            assert call_args[0][0] == 0.5


class TestTracingContextSetup:
    """Tests for tracing context initialization."""

    def test_tracing_context_initialization(self):
        """TracingContext initializes with service name."""
        pytest.importorskip("opentelemetry")

        from quicketl.telemetry.opentelemetry import TracingContext

        with patch("quicketl.telemetry.opentelemetry.trace"):
            ctx = TracingContext(service_name="my-pipeline")
            assert ctx.service_name == "my-pipeline"


class TestCorrelationId:
    """Tests for correlation ID generation (no OTel required)."""

    def test_get_correlation_id(self):
        """Correlation ID is generated without OTel."""
        from quicketl.telemetry.context import get_correlation_id

        correlation_id = get_correlation_id()
        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_correlation_id_is_unique_after_reset(self):
        """Each reset generates a unique correlation ID."""
        from quicketl.telemetry.context import get_correlation_id, reset_correlation_id

        id1 = get_correlation_id()
        reset_correlation_id()
        id2 = get_correlation_id()
        assert id1 != id2

    def test_correlation_id_is_consistent_within_context(self):
        """Same correlation ID is returned within a context."""
        from quicketl.telemetry.context import get_correlation_id

        id1 = get_correlation_id()
        id2 = get_correlation_id()
        assert id1 == id2
