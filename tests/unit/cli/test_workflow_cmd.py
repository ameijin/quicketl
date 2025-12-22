"""Tests for the 'quicketl workflow' CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from quicketl.cli.workflow import app, parse_variables


class TestParseWorkflowVariables:
    """Tests for the parse_variables helper function."""

    def test_parse_single_variable(self):
        """Test parsing a single KEY=VALUE variable."""
        result = parse_variables(["DATE=2025-01-01"])
        assert result == {"DATE": "2025-01-01"}

    def test_parse_multiple_variables(self):
        """Test parsing multiple variables."""
        result = parse_variables(["VAR1=value1", "VAR2=value2"])
        assert result == {"VAR1": "value1", "VAR2": "value2"}

    def test_parse_empty_list(self):
        """Test parsing empty variable list."""
        result = parse_variables([])
        assert result == {}

    def test_parse_value_with_equals(self):
        """Test parsing variable where value contains '='."""
        result = parse_variables(["QUERY=a=1&b=2"])
        assert result == {"QUERY": "a=1&b=2"}

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises typer.BadParameter."""
        import typer

        with pytest.raises(typer.BadParameter) as exc_info:
            parse_variables(["INVALID"])

        assert "Invalid variable format" in str(exc_info.value)


class TestWorkflowRunCommand:
    """Tests for the 'quicketl workflow run' command."""

    def test_run_valid_workflow(self, cli_runner: CliRunner, tmp_path: Path):
        """Test running a valid workflow."""
        # Create a simple workflow YAML
        pipeline_content = """
name: test_pipeline
engine: duckdb
source:
  type: file
  path: /dev/null
  format: csv
sink:
  type: file
  path: /tmp/out.parquet
  format: parquet
"""
        pipeline_file = tmp_path / "pipeline.yml"
        pipeline_file.write_text(pipeline_content)

        workflow_content = f"""
name: test_workflow
stages:
  - name: stage1
    pipelines:
      - path: {pipeline_file.name}
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.cli.workflow.Workflow") as mock_workflow:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.status.value = "success"
            mock_result.pipelines_succeeded = 1
            mock_result.pipelines_failed = 0
            mock_result.total_pipelines = 1
            mock_result.duration_ms = 100.0
            mock_result.stage_results = []
            mock_result.error = None
            mock_instance.run.return_value = mock_result
            mock_instance.name = "test_workflow"
            mock_instance.description = ""
            mock_instance._stages = []
            mock_workflow.from_yaml.return_value = mock_instance

            result = cli_runner.invoke(app, ["run", str(workflow_file)])

            # Should not error
            assert "Error" not in result.output or result.exit_code == 0

    def test_run_with_dry_run(self, cli_runner: CliRunner, tmp_path: Path):
        """Test running workflow with --dry-run."""
        workflow_content = """
name: dry_run_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.cli.workflow.Workflow") as mock_workflow:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.status.value = "success"
            mock_result.pipelines_succeeded = 1
            mock_result.total_pipelines = 1
            mock_result.duration_ms = 50.0
            mock_result.stage_results = []
            mock_result.error = None
            mock_instance.run.return_value = mock_result
            mock_instance.name = "dry_run_test"
            mock_instance.description = ""
            mock_instance._stages = []
            mock_workflow.from_yaml.return_value = mock_instance

            _result = cli_runner.invoke(app, ["run", str(workflow_file), "--dry-run"])

            mock_instance.run.assert_called_with(dry_run=True, max_workers=None)

    def test_run_with_variables(self, cli_runner: CliRunner, tmp_path: Path):
        """Test running workflow with --var option."""
        workflow_content = """
name: var_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.cli.workflow.Workflow") as mock_workflow:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.status.value = "success"
            mock_result.pipelines_succeeded = 1
            mock_result.total_pipelines = 1
            mock_result.duration_ms = 50.0
            mock_result.stage_results = []
            mock_result.error = None
            mock_instance.run.return_value = mock_result
            mock_instance.name = "var_test"
            mock_instance.description = ""
            mock_instance._stages = []
            mock_workflow.from_yaml.return_value = mock_instance

            _result = cli_runner.invoke(
                app, ["run", str(workflow_file), "--var", "KEY=value"]
            )

            mock_workflow.from_yaml.assert_called_with(
                workflow_file, variables={"KEY": "value"}
            )

    def test_run_with_json_output(self, cli_runner: CliRunner, tmp_path: Path):
        """Test running workflow with --json output."""
        workflow_content = """
name: json_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.cli.workflow.Workflow") as mock_workflow:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.status.value = "success"
            mock_result.to_dict.return_value = {"status": "success", "pipelines": 1}
            mock_instance.run.return_value = mock_result
            mock_instance.name = "json_test"
            mock_instance.description = ""
            mock_instance._stages = []
            mock_workflow.from_yaml.return_value = mock_instance

            result = cli_runner.invoke(app, ["run", str(workflow_file), "--json"])

            assert "status" in result.output

    def test_run_missing_file_fails(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that running with missing file fails."""
        result = cli_runner.invoke(app, ["run", str(tmp_path / "nonexistent.yml")])

        assert result.exit_code != 0


class TestWorkflowValidateCommand:
    """Tests for the 'quicketl workflow validate' command."""

    def test_validate_valid_workflow(self, cli_runner: CliRunner, tmp_path: Path):
        """Test validating a valid workflow."""
        # Create pipeline file
        pipeline_file = tmp_path / "pipeline.yml"
        pipeline_file.write_text("name: test\nengine: duckdb\nsource:\n  type: file\n  path: x\n  format: csv\nsink:\n  type: file\n  path: y\n  format: parquet")

        workflow_content = """
name: valid_workflow
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["validate", str(workflow_file)])

        assert "VALID" in result.output

    def test_validate_missing_pipeline_fails(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that validation fails when pipeline file is missing."""
        workflow_content = """
name: missing_pipeline
stages:
  - name: stage1
    pipelines:
      - path: nonexistent_pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["validate", str(workflow_file)])

        assert "INVALID" in result.output or result.exit_code != 0
        assert "Missing" in result.output or "nonexistent" in result.output.lower()

    def test_validate_verbose_shows_structure(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that --verbose shows workflow structure."""
        pipeline_file = tmp_path / "pipeline.yml"
        pipeline_file.write_text("name: test\nengine: duckdb\nsource:\n  type: file\n  path: x\n  format: csv\nsink:\n  type: file\n  path: y\n  format: parquet")

        workflow_content = """
name: verbose_test
stages:
  - name: bronze
    pipelines:
      - path: pipeline.yml
  - name: silver
    depends_on: [bronze]
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["validate", str(workflow_file), "--verbose"])

        assert "VALID" in result.output
        assert "bronze" in result.output
        assert "silver" in result.output

    def test_validate_invalid_yaml_fails(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that invalid YAML syntax fails validation."""
        workflow_file = tmp_path / "invalid.yml"
        workflow_file.write_text("name: test\nstages:\n  - invalid yaml: [")

        result = cli_runner.invoke(app, ["validate", str(workflow_file)])

        assert result.exit_code != 0


class TestWorkflowInfoCommand:
    """Tests for the 'quicketl workflow info' command."""

    def test_info_shows_workflow_details(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that info shows workflow name and details."""
        workflow_content = """
name: info_test_workflow
description: A test workflow for info command
variables:
  VAR1: value1
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
  - name: stage2
    depends_on: [stage1]
    parallel: true
    pipelines:
      - path: pipeline2.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["info", str(workflow_file)])

        assert "info_test_workflow" in result.output
        assert "stage1" in result.output
        assert "stage2" in result.output

    def test_info_shows_execution_order(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that info shows execution order."""
        workflow_content = """
name: order_test
stages:
  - name: a
    pipelines:
      - path: p.yml
  - name: b
    depends_on: [a]
    pipelines:
      - path: p.yml
  - name: c
    depends_on: [b]
    pipelines:
      - path: p.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["info", str(workflow_file)])

        assert "Execution Order" in result.output

    def test_info_shows_variables(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that info shows workflow variables."""
        workflow_content = """
name: var_info_test
variables:
  ENV: production
  DEBUG: "false"
stages:
  - name: stage1
    pipelines:
      - path: p.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(app, ["info", str(workflow_file)])

        assert "Variables" in result.output
        assert "ENV" in result.output


class TestWorkflowGenerateCommand:
    """Tests for the 'quicketl workflow generate' command."""

    def test_generate_airflow_dag(self, cli_runner: CliRunner, tmp_path: Path):
        """Test generating Airflow DAG code."""
        workflow_content = """
name: airflow_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.workflow.generators.generate_airflow_dag") as mock_gen:
            mock_gen.return_value = "# Generated Airflow DAG\nfrom airflow import DAG"

            result = cli_runner.invoke(
                app, ["generate", str(workflow_file), "--target", "airflow"]
            )

            assert "airflow" in result.output.lower() or "DAG" in result.output

    def test_generate_prefect_flow(self, cli_runner: CliRunner, tmp_path: Path):
        """Test generating Prefect flow code."""
        workflow_content = """
name: prefect_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        with patch("quicketl.workflow.generators.generate_prefect_flow") as mock_gen:
            mock_gen.return_value = "# Generated Prefect Flow\nfrom prefect import flow"

            result = cli_runner.invoke(
                app, ["generate", str(workflow_file), "--target", "prefect"]
            )

            assert "prefect" in result.output.lower() or "flow" in result.output.lower()

    def test_generate_to_output_file(self, cli_runner: CliRunner, tmp_path: Path):
        """Test generating code to output file."""
        workflow_content = """
name: output_test
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)
        output_file = tmp_path / "output_dag.py"

        with patch("quicketl.workflow.generators.generate_airflow_dag") as mock_gen:
            mock_gen.return_value = "# Generated DAG"

            result = cli_runner.invoke(
                app,
                [
                    "generate",
                    str(workflow_file),
                    "--target",
                    "airflow",
                    "--output",
                    str(output_file),
                ],
            )

            assert output_file.exists() or "Generated" in result.output

    def test_generate_unknown_target_fails(self, cli_runner: CliRunner, tmp_path: Path):
        """Test that unknown target fails."""
        workflow_content = """
name: unknown_target
stages:
  - name: stage1
    pipelines:
      - path: pipeline.yml
"""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(
            app, ["generate", str(workflow_file), "--target", "unknown"]
        )

        assert result.exit_code != 0
        assert "Unknown target" in result.output or "unknown" in result.output.lower()
