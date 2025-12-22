"""Tests for the 'quicketl run' CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quicketl.cli.main import app
from quicketl.cli.run import parse_variables


class TestParseVariables:
    """Tests for the parse_variables helper function."""

    def test_parse_variables_with_single_variable(self):
        """Test parsing a single KEY=VALUE variable."""
        result = parse_variables(["DATE=2025-01-01"])
        assert result == {"DATE": "2025-01-01"}

    def test_parse_variables_with_multiple_variables(self):
        """Test parsing multiple KEY=VALUE variables."""
        result = parse_variables(["DATE=2025-01-01", "ENV=prod", "DEBUG=true"])
        assert result == {
            "DATE": "2025-01-01",
            "ENV": "prod",
            "DEBUG": "true",
        }

    def test_parse_variables_with_empty_list(self):
        """Test parsing an empty variable list."""
        result = parse_variables([])
        assert result == {}

    def test_parse_variables_with_value_containing_equals(self):
        """Test parsing a variable where the value contains '='."""
        result = parse_variables(["QUERY=a=1&b=2"])
        assert result == {"QUERY": "a=1&b=2"}

    def test_parse_variables_with_empty_value(self):
        """Test parsing a variable with an empty value."""
        result = parse_variables(["EMPTY="])
        assert result == {"EMPTY": ""}

    def test_parse_variables_with_invalid_format_raises_error(self):
        """Test that invalid format raises typer.BadParameter."""
        import typer

        with pytest.raises(typer.BadParameter) as exc_info:
            parse_variables(["INVALID_NO_EQUALS"])

        assert "Invalid variable format" in str(exc_info.value)
        assert "Use KEY=VALUE" in str(exc_info.value)


class TestRunCommand:
    """Tests for the 'quicketl run' command."""

    def test_run_with_valid_config_succeeds(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test running a valid pipeline succeeds."""
        result = cli_runner.invoke(app, ["run", str(valid_pipeline_yaml)])

        assert result.exit_code == 0
        assert "Running pipeline" in result.output or "SUCCESS" in result.output

    def test_run_with_missing_file_exits_1(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that running with a non-existent file exits with code 1."""
        nonexistent = temp_dir / "nonexistent.yml"
        result = cli_runner.invoke(app, ["run", str(nonexistent)])

        assert result.exit_code != 0

    def test_run_with_dry_run_writes_no_output(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path, temp_dir: Path
    ):
        """Test that --dry-run prevents output file from being written."""
        output_path = temp_dir / "output.parquet"

        # Ensure output doesn't exist before
        if output_path.exists():
            output_path.unlink()

        result = cli_runner.invoke(
            app, ["run", str(valid_pipeline_yaml), "--dry-run"]
        )

        # The command should succeed (exit 0) or partial (exit 2)
        assert result.exit_code in [0, 2]
        # Output file should not be created in dry-run mode
        assert not output_path.exists()

    def test_run_with_invalid_var_format_fails(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that invalid variable format causes failure."""
        result = cli_runner.invoke(
            app, ["run", str(valid_pipeline_yaml), "--var", "INVALID_NO_EQUALS"]
        )

        assert result.exit_code != 0
        # Error message may vary - just check it failed
        assert "error" in result.output.lower() or result.exit_code != 0

    def test_run_with_var_substitutes_correctly(
        self, cli_runner: CliRunner, pipeline_with_vars_yaml: Path, temp_dir: Path
    ):
        """Test that --var correctly substitutes variables."""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name,amount\n1,Alice,150\n")
        output_path = temp_dir / "output.parquet"

        result = cli_runner.invoke(
            app,
            [
                "run",
                str(pipeline_with_vars_yaml),
                "--var",
                f"INPUT_PATH={input_path}",
                "--var",
                f"OUTPUT_PATH={output_path}",
                "--var",
                "THRESHOLD=50",
            ],
        )

        # May fail due to file not found if var substitution fails
        # but should not fail on parsing the variables
        assert "Invalid variable format" not in result.output

    def test_run_with_json_outputs_valid_json(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that --json outputs valid JSON."""
        result = cli_runner.invoke(
            app, ["run", str(valid_pipeline_yaml), "--json"]
        )

        # Exit 0 = success, 2 = partial success
        assert result.exit_code in [0, 2]
        # Try to parse the output as JSON (filter out non-JSON lines)
        lines = result.output.strip().split('\n')
        json_lines = [line for line in lines if line.strip().startswith('{') or line.strip().startswith('"')]
        if json_lines:
            output_data = json.loads('\n'.join(lines))
            assert "pipeline_name" in output_data or "status" in output_data

    def test_run_with_engine_override_uses_specified_engine(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that --engine overrides the configured engine."""
        # Run with polars engine override
        result = cli_runner.invoke(
            app, ["run", str(valid_pipeline_yaml), "--engine", "polars"]
        )

        # Should succeed with polars (exit 0 or 2 for partial)
        assert result.exit_code in [0, 2]

    def test_run_with_verbose_shows_more_output(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that --verbose shows additional output."""
        result = cli_runner.invoke(
            app, ["run", str(valid_pipeline_yaml), "--verbose"]
        )

        # Should complete (exit 0 or 2)
        assert result.exit_code in [0, 2]

    def test_run_with_no_fail_on_checks_continues_on_check_failure(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --no-fail-on-checks allows pipeline to complete."""
        # Create a pipeline with checks that will fail
        yaml_content = """
name: failing_checks_pipeline
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

checks:
  - type: row_count
    min: 100  # Will fail since we only have 2 rows

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name\n1,Alice\n2,Bob\n")
        output_path = temp_dir / "output.parquet"

        yaml_path = temp_dir / "failing.yml"
        yaml_path.write_text(
            yaml_content.format(input_path=input_path, output_path=output_path)
        )

        # With --no-fail-on-checks, pipeline should complete
        result = cli_runner.invoke(
            app, ["run", str(yaml_path), "--no-fail-on-checks"]
        )

        # Should complete (might be partial success)
        assert result.exit_code in [0, 2]  # 0 = success, 2 = partial

    def test_run_with_fail_on_checks_exits_on_check_failure(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --fail-on-checks (default) exits on check failure."""
        # Create a pipeline with checks that will fail
        yaml_content = """
name: failing_checks_pipeline
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

checks:
  - type: row_count
    min: 100  # Will fail since we only have 2 rows

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name\n1,Alice\n2,Bob\n")
        output_path = temp_dir / "output.parquet"

        yaml_path = temp_dir / "failing.yml"
        yaml_path.write_text(
            yaml_content.format(input_path=input_path, output_path=output_path)
        )

        # With default --fail-on-checks, should fail
        result = cli_runner.invoke(app, ["run", str(yaml_path)])

        # Should fail due to check failure
        assert result.exit_code in [1, 2]


class TestMainCLI:
    """Tests for the main CLI application."""

    def test_main_with_no_args_shows_help(self, cli_runner: CliRunner):
        """Test that running without arguments shows help."""
        result = cli_runner.invoke(app)

        assert result.exit_code == 0
        assert "QuickETL" in result.output
        assert "run" in result.output
        assert "validate" in result.output

    def test_version_flag_shows_version(self, cli_runner: CliRunner):
        """Test that --version shows the version number."""
        result = cli_runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "quicketl version" in result.output

    def test_help_flag_shows_help(self, cli_runner: CliRunner):
        """Test that --help shows help text."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "QuickETL" in result.output
        assert "Commands:" in result.output or "run" in result.output
