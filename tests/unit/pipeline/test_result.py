"""Tests for pipeline result module."""

from __future__ import annotations

from datetime import UTC, datetime

from quicketl.pipeline.result import (
    PipelineResult,
    PipelineResultBuilder,
    PipelineStatus,
    StageResult,
    StepResult,
    WorkflowResult,
    WorkflowStatus,
)


class TestStepResult:
    """Tests for StepResult."""

    def test_succeeded(self):
        step = StepResult(step_name="read", step_type="file", status="success", duration_ms=10.0)
        assert step.succeeded is True

    def test_not_succeeded(self):
        step = StepResult(step_name="read", step_type="file", status="failed", duration_ms=10.0)
        assert step.succeeded is False

    def test_with_error(self):
        step = StepResult(
            step_name="transform",
            step_type="filter",
            status="failed",
            duration_ms=5.0,
            error="column not found",
        )
        assert step.error == "column not found"


class TestPipelineResult:
    """Tests for PipelineResult."""

    def _make_result(self, **kwargs):
        defaults = {
            "pipeline_name": "test",
            "status": PipelineStatus.SUCCESS,
            "start_time": datetime(2025, 1, 1, tzinfo=UTC),
            "end_time": datetime(2025, 1, 1, 0, 0, 1, tzinfo=UTC),
            "duration_ms": 1000.0,
        }
        defaults.update(kwargs)
        return PipelineResult(**defaults)

    def test_succeeded_property(self):
        result = self._make_result(status=PipelineStatus.SUCCESS)
        assert result.succeeded is True
        assert result.failed is False

    def test_failed_property(self):
        result = self._make_result(status=PipelineStatus.FAILED)
        assert result.succeeded is False
        assert result.failed is True

    def test_steps_succeeded_count(self):
        steps = [
            StepResult(step_name="a", step_type="t", status="success", duration_ms=1.0),
            StepResult(step_name="b", step_type="t", status="failed", duration_ms=1.0),
            StepResult(step_name="c", step_type="t", status="success", duration_ms=1.0),
        ]
        result = self._make_result(step_results=steps)
        assert result.steps_succeeded == 2
        assert result.steps_failed == 1

    def test_summary_includes_key_info(self):
        result = self._make_result(
            rows_processed=100,
            rows_written=50,
        )
        s = result.summary()
        assert "test" in s
        assert "100" in s
        assert "50" in s

    def test_summary_with_error(self):
        result = self._make_result(
            status=PipelineStatus.FAILED,
            error="something broke",
        )
        s = result.summary()
        assert "something broke" in s

    def test_to_dict(self):
        result = self._make_result(rows_processed=10)
        d = result.to_dict()
        assert d["pipeline_name"] == "test"
        assert d["status"] == "success"
        assert d["rows_processed"] == 10
        assert "step_results" in d

    def test_str_is_summary(self):
        result = self._make_result()
        assert str(result) == result.summary()


class TestPipelineResultBuilder:
    """Tests for PipelineResultBuilder."""

    def test_build_success(self):
        builder = PipelineResultBuilder(pipeline_name="p1")
        builder.add_step(
            StepResult(step_name="read", step_type="file", status="success", duration_ms=5.0)
        )
        builder.rows_processed = 42
        result = builder.build()

        assert result.status == PipelineStatus.SUCCESS
        assert result.pipeline_name == "p1"
        assert result.rows_processed == 42
        assert len(result.step_results) == 1

    def test_build_failed_on_error(self):
        builder = PipelineResultBuilder(pipeline_name="p2")
        builder.set_error("boom")
        result = builder.build()

        assert result.status == PipelineStatus.FAILED
        assert result.error == "boom"

    def test_build_partial_on_step_failure(self):
        builder = PipelineResultBuilder(pipeline_name="p3")
        builder.add_step(
            StepResult(step_name="ok", step_type="t", status="success", duration_ms=1.0)
        )
        builder.add_step(
            StepResult(step_name="bad", step_type="t", status="failed", duration_ms=1.0)
        )
        result = builder.build()

        assert result.status == PipelineStatus.PARTIAL

    def test_set_check_results(self):
        builder = PipelineResultBuilder(pipeline_name="p4")
        builder.set_check_results({"all_passed": True, "total": 3})
        result = builder.build()

        assert result.check_results == {"all_passed": True, "total": 3}

    def test_metadata(self):
        builder = PipelineResultBuilder(
            pipeline_name="p5",
            metadata={"engine": "duckdb", "run_id": "abc"},
        )
        result = builder.build()
        assert result.metadata["engine"] == "duckdb"


class TestStageResult:
    """Tests for StageResult."""

    def test_succeeded(self):
        stage = StageResult(
            stage_name="extract",
            status="success",
            start_time=datetime(2025, 1, 1, tzinfo=UTC),
            end_time=datetime(2025, 1, 1, 0, 0, 1, tzinfo=UTC),
            duration_ms=1000.0,
        )
        assert stage.succeeded is True

    def test_pipeline_counts(self):
        pr_ok = PipelineResult(
            pipeline_name="a",
            status=PipelineStatus.SUCCESS,
            start_time=datetime(2025, 1, 1, tzinfo=UTC),
            end_time=datetime(2025, 1, 1, tzinfo=UTC),
            duration_ms=0,
        )
        pr_fail = PipelineResult(
            pipeline_name="b",
            status=PipelineStatus.FAILED,
            start_time=datetime(2025, 1, 1, tzinfo=UTC),
            end_time=datetime(2025, 1, 1, tzinfo=UTC),
            duration_ms=0,
        )
        stage = StageResult(
            stage_name="load",
            status="partial",
            start_time=datetime(2025, 1, 1, tzinfo=UTC),
            end_time=datetime(2025, 1, 1, tzinfo=UTC),
            duration_ms=0,
            pipeline_results=[pr_ok, pr_fail],
        )
        assert stage.pipelines_succeeded == 1
        assert stage.pipelines_failed == 1


class TestWorkflowResult:
    """Tests for WorkflowResult."""

    def _make_result(self, **kwargs):
        defaults = {
            "workflow_name": "daily_etl",
            "status": WorkflowStatus.SUCCESS,
            "start_time": datetime(2025, 1, 1, tzinfo=UTC),
            "end_time": datetime(2025, 1, 1, 0, 1, 0, tzinfo=UTC),
            "duration_ms": 60000.0,
            "total_pipelines": 3,
            "pipelines_succeeded": 3,
            "pipelines_failed": 0,
        }
        defaults.update(kwargs)
        return WorkflowResult(**defaults)

    def test_succeeded(self):
        result = self._make_result()
        assert result.succeeded is True
        assert result.failed is False

    def test_failed(self):
        result = self._make_result(status=WorkflowStatus.FAILED)
        assert result.failed is True
        assert result.succeeded is False

    def test_summary(self):
        result = self._make_result()
        s = result.summary()
        assert "daily_etl" in s
        assert "3/3" in s

    def test_summary_with_error(self):
        result = self._make_result(
            status=WorkflowStatus.FAILED,
            error="stage failed",
        )
        s = result.summary()
        assert "stage failed" in s

    def test_to_dict(self):
        result = self._make_result()
        d = result.to_dict()
        assert d["workflow_name"] == "daily_etl"
        assert d["status"] == "success"
        assert d["total_pipelines"] == 3

    def test_str_is_summary(self):
        result = self._make_result()
        assert str(result) == result.summary()

    def test_to_dict_with_stages(self):
        stage = StageResult(
            stage_name="extract",
            status="success",
            start_time=datetime(2025, 1, 1, tzinfo=UTC),
            end_time=datetime(2025, 1, 1, tzinfo=UTC),
            duration_ms=0,
        )
        result = self._make_result(stage_results=[stage])
        d = result.to_dict()
        assert len(d["stage_results"]) == 1
        assert d["stage_results"][0]["stage_name"] == "extract"
