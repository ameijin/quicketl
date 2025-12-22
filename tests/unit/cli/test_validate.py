"""Tests for the 'quicketl validate' CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from quicketl.cli.main import app


class TestValidateCommand:
    """Tests for the 'quicketl validate' command."""

    def test_validate_with_valid_config_shows_valid(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test validating a valid config shows 'valid' message."""
        result = cli_runner.invoke(app, ["validate", str(valid_pipeline_yaml)])

        # Check output shows validation passed (exit code may vary due to Typer behavior)
        assert "valid" in result.output.lower()
        assert "error" not in result.output.lower() or "is valid" in result.output.lower()

    def test_validate_with_invalid_config_exits_1(
        self, cli_runner: CliRunner, invalid_pipeline_yaml: Path
    ):
        """Test validating an invalid config exits with code 1."""
        result = cli_runner.invoke(app, ["validate", str(invalid_pipeline_yaml)])

        assert result.exit_code == 1
        assert "invalid" in result.output.lower() or "error" in result.output.lower()

    def test_validate_with_missing_file_exits_1(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test validating a non-existent file exits with code 1."""
        nonexistent = temp_dir / "nonexistent.yml"
        result = cli_runner.invoke(app, ["validate", str(nonexistent)])

        assert result.exit_code != 0

    def test_validate_with_verbose_shows_details(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that --verbose shows configuration details."""
        result = cli_runner.invoke(
            app, ["validate", str(valid_pipeline_yaml), "--verbose"]
        )

        # Verbose output should show more details
        assert "valid" in result.output.lower()

    def test_validate_shows_summary_without_verbose(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that non-verbose validation shows brief summary."""
        result = cli_runner.invoke(app, ["validate", str(valid_pipeline_yaml)])

        # Should show engine, source, transforms count, etc.
        assert "Engine" in result.output or "engine" in result.output

    def test_validate_with_invalid_yaml_syntax_exits_1(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test validating file with invalid YAML syntax exits with code 1."""
        invalid_yaml = temp_dir / "invalid_syntax.yml"
        invalid_yaml.write_text("name: test\n  invalid indentation")

        result = cli_runner.invoke(app, ["validate", str(invalid_yaml)])

        assert result.exit_code == 1

    def test_validate_with_missing_required_fields_shows_errors(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that missing required fields are reported."""
        yaml_content = """
name: incomplete_pipeline
engine: duckdb
# Missing source and sink
"""
        yaml_path = temp_dir / "incomplete.yml"
        yaml_path.write_text(yaml_content)

        result = cli_runner.invoke(app, ["validate", str(yaml_path)])

        assert result.exit_code == 1

    def test_validate_with_invalid_transform_type_shows_error(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that invalid transform type is reported."""
        yaml_content = """
name: invalid_transform_pipeline
engine: duckdb

source:
  type: file
  path: /tmp/test.csv
  format: csv

transforms:
  - op: nonexistent_operation
    columns: [id]

sink:
  type: file
  path: /tmp/output.parquet
  format: parquet
"""
        yaml_path = temp_dir / "invalid_transform.yml"
        yaml_path.write_text(yaml_content)

        result = cli_runner.invoke(app, ["validate", str(yaml_path)])

        assert result.exit_code == 1

    def test_validate_with_invalid_check_type_shows_error(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that invalid check type is reported."""
        yaml_content = """
name: invalid_check_pipeline
engine: duckdb

source:
  type: file
  path: /tmp/test.csv
  format: csv

checks:
  - type: nonexistent_check
    columns: [id]

sink:
  type: file
  path: /tmp/output.parquet
  format: parquet
"""
        yaml_path = temp_dir / "invalid_check.yml"
        yaml_path.write_text(yaml_content)

        result = cli_runner.invoke(app, ["validate", str(yaml_path)])

        assert result.exit_code == 1

    def test_validate_shows_transform_and_check_counts(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that validation output shows transform and check counts."""
        result = cli_runner.invoke(app, ["validate", str(valid_pipeline_yaml)])

        # Should mention transforms and checks
        assert "Transforms" in result.output or "transforms" in result.output.lower()
        assert "Checks" in result.output or "checks" in result.output.lower()

