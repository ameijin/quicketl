"""Tests for Pipeline class and execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quicketl.config.checks import NotNullCheck, RowCountCheck
from quicketl.config.models import FileSink, FileSource
from quicketl.config.transforms import FilterTransform, SelectTransform
from quicketl.pipeline import Pipeline, PipelineResult, PipelineStatus

if TYPE_CHECKING:
    from pathlib import Path


class TestPipelineBuilder:
    """Tests for Pipeline builder pattern."""

    def test_create_pipeline(self):
        """Create a basic pipeline."""
        pipeline = Pipeline("test_pipeline")

        assert pipeline.name == "test_pipeline"
        assert pipeline.engine_name == "duckdb"  # default

    def test_pipeline_with_source(self):
        """Add source to pipeline."""
        pipeline = Pipeline("test").source(
            FileSource(path="data.parquet", format="parquet")
        )

        assert pipeline._source is not None
        assert pipeline._source.path == "data.parquet"

    def test_pipeline_with_transforms(self):
        """Add transforms to pipeline."""
        pipeline = (
            Pipeline("test")
            .transform(FilterTransform(predicate="amount > 0"))
            .transform(SelectTransform(columns=["id", "name"]))
        )

        assert len(pipeline._transforms) == 2

    def test_pipeline_with_checks(self):
        """Add quality checks to pipeline."""
        pipeline = (
            Pipeline("test")
            .check(NotNullCheck(columns=["id"]))
            .check(RowCountCheck(min=1))
        )

        assert len(pipeline._checks) == 2

    def test_pipeline_with_sink(self):
        """Add sink to pipeline."""
        pipeline = Pipeline("test").sink(
            FileSink(path="output.parquet", format="parquet")
        )

        assert pipeline._sink is not None
        assert pipeline._sink.path == "output.parquet"

    def test_pipeline_chaining(self):
        """Full pipeline builder chain."""
        pipeline = (
            Pipeline("full_pipeline", engine="polars")
            .source(FileSource(path="input.parquet"))
            .transform(FilterTransform(predicate="amount > 0"))
            .transform(SelectTransform(columns=["id", "amount"]))
            .check(NotNullCheck(columns=["id"]))
            .sink(FileSink(path="output.parquet"))
        )

        assert pipeline.name == "full_pipeline"
        assert pipeline.engine_name == "polars"
        assert pipeline._source is not None
        assert len(pipeline._transforms) == 2
        assert len(pipeline._checks) == 1
        assert pipeline._sink is not None


class TestPipelineFromYAML:
    """Tests for loading pipeline from YAML."""

    def test_load_from_yaml(self, sample_pipeline_yaml: Path):
        """Load pipeline from YAML file."""
        pipeline = Pipeline.from_yaml(sample_pipeline_yaml)

        assert pipeline.name == "test_pipeline"
        assert pipeline._source is not None
        assert len(pipeline._transforms) == 2
        assert len(pipeline._checks) == 2

    def test_load_with_variables(self, temp_dir: Path):
        """Load pipeline with variable substitution."""
        yaml_content = """
name: var_test
engine: duckdb
source:
  type: file
  path: ${INPUT_PATH}
  format: parquet
sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
"""
        yaml_path = temp_dir / "var_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(
            yaml_path,
            variables={
                "INPUT_PATH": "/data/input.parquet",
                "OUTPUT_PATH": "/data/output.parquet",
            },
        )

        assert pipeline._source.path == "/data/input.parquet"
        assert pipeline._sink.path == "/data/output.parquet"


class TestPipelineExecution:
    """Tests for pipeline execution."""

    def test_run_pipeline_dry_run(self, sample_pipeline_yaml: Path):
        """Run pipeline in dry-run mode (no output written)."""
        pipeline = Pipeline.from_yaml(sample_pipeline_yaml)
        result = pipeline.run(dry_run=True)

        assert isinstance(result, PipelineResult)
        assert result.status in [PipelineStatus.SUCCESS, PipelineStatus.PARTIAL]
        assert result.rows_written == 0  # No output in dry run

    def test_run_pipeline_full(self, sample_pipeline_yaml: Path, temp_dir: Path):
        """Run full pipeline with output."""
        pipeline = Pipeline.from_yaml(sample_pipeline_yaml)
        result = pipeline.run()

        assert result.status == PipelineStatus.SUCCESS
        assert result.rows_processed > 0

        # Check output file exists
        output_path = temp_dir / "output.parquet"
        assert output_path.exists()

    def test_run_pipeline_check_failure(self, temp_dir: Path, sample_parquet: Path):
        """Pipeline fails when checks fail."""
        yaml_content = f"""
name: failing_checks
engine: duckdb
source:
  type: file
  path: {sample_parquet}
  format: parquet
checks:
  - type: row_count
    min: 100  # Will fail, only 5 rows
sink:
  type: file
  path: {temp_dir / "output.parquet"}
  format: parquet
"""
        yaml_path = temp_dir / "fail_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run(fail_on_check_failure=True)

        assert result.status == PipelineStatus.FAILED
        assert "checks failed" in result.error.lower()

    def test_run_pipeline_ignore_check_failure(self, temp_dir: Path, sample_parquet: Path):
        """Pipeline continues when checks fail but fail_on_check_failure=False."""
        yaml_content = f"""
name: continue_on_fail
engine: duckdb
source:
  type: file
  path: {sample_parquet}
  format: parquet
checks:
  - type: row_count
    min: 100  # Will fail
sink:
  type: file
  path: {temp_dir / "output.parquet"}
  format: parquet
"""
        yaml_path = temp_dir / "continue_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run(fail_on_check_failure=False)

        # Should succeed despite check failure
        assert result.status == PipelineStatus.SUCCESS
        assert result.check_results["all_passed"] is False


class TestPipelineResult:
    """Tests for PipelineResult."""

    def test_result_to_dict(self, sample_pipeline_yaml: Path):
        """Result can be serialized to dict."""
        pipeline = Pipeline.from_yaml(sample_pipeline_yaml)
        result = pipeline.run(dry_run=True)

        result_dict = result.to_dict()

        assert "pipeline_name" in result_dict
        assert "status" in result_dict
        assert "duration_ms" in result_dict
        assert "step_results" in result_dict

    def test_result_summary(self, sample_pipeline_yaml: Path):
        """Result has human-readable summary."""
        pipeline = Pipeline.from_yaml(sample_pipeline_yaml)
        result = pipeline.run(dry_run=True)

        summary = result.summary()

        assert "test_pipeline" in summary
        assert "Duration" in summary


class TestPipelineBuilderExtended:
    """Tests for additional builder methods."""

    def test_transforms_batch(self):
        """Add multiple transforms at once."""
        pipeline = Pipeline("test").transforms([
            FilterTransform(predicate="amount > 0"),
            SelectTransform(columns=["id"]),
        ])
        assert len(pipeline._transforms) == 2

    def test_checks_batch(self):
        """Add multiple checks at once."""
        pipeline = Pipeline("test").checks([
            NotNullCheck(columns=["id"]),
            RowCountCheck(min=1),
        ])
        assert len(pipeline._checks) == 2

    def test_with_variables(self):
        """Set runtime variables."""
        pipeline = Pipeline("test").with_variables({"A": "1", "B": "2"})
        assert pipeline._variables == {"A": "1", "B": "2"}

    def test_with_variables_merges(self):
        """Variables merge rather than replace."""
        pipeline = Pipeline("test").with_variables({"A": "1"}).with_variables({"B": "2"})
        assert pipeline._variables == {"A": "1", "B": "2"}

    def test_run_no_source_raises(self):
        """Pipeline without source raises ValueError."""
        pipeline = Pipeline("test").sink(FileSink(path="out.parquet", format="parquet"))
        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED
        assert "source not configured" in result.error.lower()

    def test_run_no_sink_raises(self):
        """Pipeline without sink raises ValueError (non-dry-run)."""
        pipeline = Pipeline("test").source(FileSource(path="in.parquet", format="parquet"))
        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED
        assert "sink not configured" in result.error.lower()

    def test_run_no_sink_ok_dry_run(self, sample_parquet):
        """Pipeline without sink succeeds in dry-run mode."""
        pipeline = Pipeline("test").source(
            FileSource(path=str(sample_parquet), format="parquet")
        )
        result = pipeline.run(dry_run=True)
        assert result.status == PipelineStatus.SUCCESS


class TestRunPipelineFunction:
    """Tests for run_pipeline convenience function."""

    def test_run_pipeline(self, sample_pipeline_yaml):
        from quicketl.pipeline.pipeline import run_pipeline

        result = run_pipeline(sample_pipeline_yaml, dry_run=True)
        assert isinstance(result, PipelineResult)
        assert result.status in [PipelineStatus.SUCCESS, PipelineStatus.PARTIAL]

    def test_run_pipeline_with_engine_override(self, sample_pipeline_yaml):
        from quicketl.pipeline.pipeline import run_pipeline

        result = run_pipeline(sample_pipeline_yaml, engine="duckdb", dry_run=True)
        assert result.metadata.get("engine") == "duckdb"


class TestPipelineInfo:
    """Tests for pipeline inspection."""

    def test_pipeline_info(self, pipeline_config):
        """Get pipeline information."""
        pipeline = Pipeline.from_config(pipeline_config)
        info = pipeline.info()

        assert info["name"] == "test_pipeline"
        assert info["engine"] == "duckdb"
        assert len(info["transforms"]) == 2
        assert len(info["checks"]) == 2

    def test_pipeline_repr(self, pipeline_config):
        """Pipeline has useful repr."""
        pipeline = Pipeline.from_config(pipeline_config)
        repr_str = repr(pipeline)

        assert "test_pipeline" in repr_str
        assert "duckdb" in repr_str
