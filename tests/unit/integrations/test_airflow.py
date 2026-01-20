"""Tests for Airflow integration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quicketl.integrations.airflow import quicketl_task, run_pipeline_task
from quicketl.pipeline.result import PipelineResult, PipelineStatus


@pytest.fixture
def mock_success_result() -> PipelineResult:
    """Create a successful pipeline result for testing."""
    return PipelineResult(
        pipeline_name="test_pipeline",
        status=PipelineStatus.SUCCESS,
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        duration_ms=100.0,
        rows_processed=1000,
        rows_written=1000,
        step_results=[],
        check_results={"all_passed": True, "total": 2, "passed": 2, "failed": 0},
        error=None,
        metadata={},
    )


@pytest.fixture
def mock_failed_result() -> PipelineResult:
    """Create a failed pipeline result for testing."""
    return PipelineResult(
        pipeline_name="test_pipeline",
        status=PipelineStatus.FAILED,
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        duration_ms=50.0,
        rows_processed=0,
        rows_written=0,
        step_results=[],
        check_results=None,
        error="Test error message",
        metadata={},
    )


class TestQuickETLTaskDecorator:
    """Tests for the @quicketl_task decorator."""

    def test_decorator_with_config_path_and_variables(
        self, mock_success_result: PipelineResult
    ):
        """Test decorator with config_path returning variables dict."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml")
            def my_task(**context):
                return {"DATE": "2024-01-01", "ENV": "prod"}

            result = my_task(ds="2024-01-01")

            # Should return dict from pipeline result
            assert isinstance(result, dict)
            assert result["pipeline_name"] == "test_pipeline"
            assert result["status"] == "success"
            assert result["rows_processed"] == 1000

    def test_decorator_with_pipeline_return(self, mock_success_result: PipelineResult):
        """Test decorator with function returning Pipeline object."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        @quicketl_task()
        def my_task(**context):
            return mock_pipeline

        result = my_task()

        assert isinstance(result, dict)
        assert result["status"] == "success"
        mock_pipeline.run.assert_called_once_with(fail_on_check_failure=True)

    def test_decorator_with_engine_override(self, mock_success_result: PipelineResult):
        """Test that engine override is applied."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml", engine="polars")
            def my_task():
                return {}

            my_task()

            # Should set engine_name
            assert mock_pipeline.engine_name == "polars"

    def test_decorator_with_fail_on_check_failure_false(
        self, mock_success_result: PipelineResult
    ):
        """Test fail_on_check_failure parameter is passed through."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml", fail_on_check_failure=False)
            def my_task():
                return {}

            my_task()

            mock_pipeline.run.assert_called_once_with(fail_on_check_failure=False)

    def test_decorator_raises_runtime_error_on_failure(
        self, mock_failed_result: PipelineResult
    ):
        """Test that RuntimeError is raised when pipeline fails."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_failed_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml")
            def my_task():
                return {}

            with pytest.raises(RuntimeError) as exc_info:
                my_task()

            assert "test_pipeline" in str(exc_info.value)
            assert "Test error message" in str(exc_info.value)

    def test_decorator_without_config_path_and_no_pipeline(self):
        """Test ValueError when no config_path and function doesn't return Pipeline."""

        @quicketl_task()
        def my_task():
            return {"some": "data"}

        with pytest.raises(ValueError) as exc_info:
            my_task()

        assert "config_path" in str(exc_info.value)
        assert "Pipeline object" in str(exc_info.value)

    def test_decorator_with_config_path_no_return(
        self, mock_success_result: PipelineResult
    ):
        """Test decorator with config_path but function returns None."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml")
            def my_task():
                pass  # Returns None

            result = my_task()

            assert result["status"] == "success"

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @quicketl_task(config_path="test.yml")
        def my_documented_task():
            """This is my task docstring."""
            return {}

        assert my_documented_task.__name__ == "my_documented_task"
        assert my_documented_task.__doc__ == "This is my task docstring."

    def test_xcom_return_format(self, mock_success_result: PipelineResult):
        """Test that XCom return dict has expected structure."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):

            @quicketl_task(config_path="test.yml")
            def my_task():
                return {}

            result = my_task()

            # Verify XCom dict structure
            assert "pipeline_name" in result
            assert "status" in result
            assert "start_time" in result
            assert "end_time" in result
            assert "duration_ms" in result
            assert "rows_processed" in result
            assert "rows_written" in result
            assert "steps_succeeded" in result
            assert "steps_failed" in result
            assert "check_results" in result


class TestRunPipelineTask:
    """Tests for run_pipeline_task function."""

    def test_run_pipeline_task_success(self, mock_success_result: PipelineResult):
        """Test successful pipeline execution."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):
            result = run_pipeline_task(config_path="test.yml")

            assert result["status"] == "success"
            assert result["rows_processed"] == 1000

    def test_run_pipeline_task_with_variables(self, mock_success_result: PipelineResult):
        """Test pipeline execution with variable substitution."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ) as mock_from_yaml:
            variables = {"DATE": "2024-01-01", "ENV": "staging"}
            run_pipeline_task(config_path="test.yml", variables=variables)

            mock_from_yaml.assert_called_once_with("test.yml", variables=variables)

    def test_run_pipeline_task_with_engine_override(
        self, mock_success_result: PipelineResult
    ):
        """Test engine override in run_pipeline_task."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):
            run_pipeline_task(config_path="test.yml", engine="spark")

            assert mock_pipeline.engine_name == "spark"

    def test_run_pipeline_task_failure(self, mock_failed_result: PipelineResult):
        """Test RuntimeError on pipeline failure."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_failed_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                run_pipeline_task(config_path="test.yml")

            assert "test_pipeline" in str(exc_info.value)
            assert "Test error message" in str(exc_info.value)

    def test_run_pipeline_task_fail_on_check_failure(
        self, mock_success_result: PipelineResult
    ):
        """Test fail_on_check_failure parameter."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ):
            run_pipeline_task(
                config_path="test.yml",
                fail_on_check_failure=False,
            )

            mock_pipeline.run.assert_called_once_with(fail_on_check_failure=False)

    def test_run_pipeline_task_accepts_path_object(
        self, mock_success_result: PipelineResult
    ):
        """Test that Path objects are accepted for config_path."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        with patch(
            "quicketl.integrations.airflow.Pipeline.from_yaml",
            return_value=mock_pipeline,
        ) as mock_from_yaml:
            config_path = Path("pipelines/test.yml")
            run_pipeline_task(config_path=config_path)

            mock_from_yaml.assert_called_once_with(config_path, variables=None)


class TestQuickETLTaskWithPipeline:
    """Tests for decorator with Pipeline builder pattern."""

    def test_decorator_with_pipeline_and_engine_override(
        self, mock_success_result: PipelineResult
    ):
        """Test engine override when function returns Pipeline."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result

        @quicketl_task(engine="duckdb")
        def my_task():
            return mock_pipeline

        my_task()

        assert mock_pipeline.engine_name == "duckdb"

    def test_decorator_with_pipeline_no_engine(
        self, mock_success_result: PipelineResult
    ):
        """Test that engine is not modified when not specified."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_success_result
        mock_pipeline.engine_name = "original_engine"

        @quicketl_task()
        def my_task():
            return mock_pipeline

        my_task()

        # engine_name should not be modified
        assert mock_pipeline.engine_name == "original_engine"
