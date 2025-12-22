"""Tests for OpenLineage integration.

This module tests:
- Job start/complete events
- Input/output dataset tracking
- Column lineage extraction
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestOpenLineageIntegration:
    """Tests for OpenLineage data lineage integration."""

    def test_job_start_event_emitted(self):
        """Job start event is emitted when pipeline begins."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.emit_start()

            mock_instance.emit.assert_called_once()
            call_args = mock_instance.emit.call_args[0][0]
            assert call_args.eventType.name == "START"

    def test_job_complete_event_emitted(self):
        """Job complete event is emitted when pipeline finishes."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.emit_complete()

            mock_instance.emit.assert_called_once()
            call_args = mock_instance.emit.call_args[0][0]
            assert call_args.eventType.name == "COMPLETE"

    def test_input_datasets_tracked(self):
        """Input datasets are included in lineage events."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.add_input_dataset(
                namespace="s3://my-bucket",
                name="raw_data.csv",
            )
            ctx.emit_start()

            call_args = mock_instance.emit.call_args[0][0]
            assert len(call_args.inputs) == 1
            assert call_args.inputs[0].name == "raw_data.csv"

    def test_output_datasets_tracked(self):
        """Output datasets are included in lineage events."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.add_output_dataset(
                namespace="postgres://localhost",
                name="processed_data",
            )
            ctx.emit_complete()

            call_args = mock_instance.emit.call_args[0][0]
            assert len(call_args.outputs) == 1
            assert call_args.outputs[0].name == "processed_data"

    def test_column_lineage_extracted(self):
        """Column-level lineage is tracked."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.add_output_dataset(
                namespace="postgres://localhost",
                name="processed_data",
                column_lineage={
                    "full_name": ["first_name", "last_name"],
                    "total": ["price", "quantity"],
                },
            )
            ctx.emit_complete()

            # Verify column lineage facet was added
            call_args = mock_instance.emit.call_args[0][0]
            assert len(call_args.outputs) == 1


class TestLineageModuleImport:
    """Tests for lineage module imports."""

    def test_lineage_module_exists(self):
        """Lineage module can be imported when openlineage is installed."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry import openlineage

        assert openlineage is not None


class TestLineageContextSetup:
    """Tests for lineage context initialization."""

    def test_lineage_context_initialization(self):
        """LineageContext initializes with namespace and job name."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient"):
            ctx = LineageContext(
                namespace="quicketl",
                job_name="my-pipeline",
            )
            assert ctx.namespace == "quicketl"
            assert ctx.job_name == "my-pipeline"

    def test_emit_fail_event(self):
        """Fail event is emitted on pipeline error."""
        pytest.importorskip("openlineage")

        from quicketl.telemetry.openlineage import LineageContext

        with patch("quicketl.telemetry.openlineage.OpenLineageClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            ctx = LineageContext(
                namespace="quicketl",
                job_name="test-pipeline",
            )
            ctx.emit_fail(error_message="Pipeline failed")

            call_args = mock_instance.emit.call_args[0][0]
            assert call_args.eventType.name == "FAIL"
