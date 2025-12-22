"""Tests for the 'quicketl info' CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from quicketl.cli.main import app


class TestInfoCommand:
    """Tests for the 'quicketl info' command."""

    def test_info_without_flags_shows_version(self, cli_runner: CliRunner):
        """Test that info without flags shows version information."""
        result = cli_runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "QuickETL" in result.output

    def test_info_with_backends_flag_lists_backends(self, cli_runner: CliRunner):
        """Test that --backends lists available backends."""
        result = cli_runner.invoke(app, ["info", "--backends"])

        assert result.exit_code == 0
        # Should list common backends
        assert "duckdb" in result.output.lower()
        assert "polars" in result.output.lower()

    def test_info_with_check_flag_verifies_backends(self, cli_runner: CliRunner):
        """Test that --check verifies backend availability."""
        result = cli_runner.invoke(app, ["info", "--check"])

        assert result.exit_code == 0
        # Should show status for backends
        assert "duckdb" in result.output.lower()
        # DuckDB and Polars should be available (installed by default)
        assert "OK" in result.output or "Available" in result.output

    def test_info_with_config_shows_pipeline_details(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path
    ):
        """Test that --config shows pipeline configuration details."""
        result = cli_runner.invoke(
            app, ["info", "--config", str(valid_pipeline_yaml)]
        )

        assert result.exit_code == 0
        # Should show pipeline name
        assert "test_pipeline" in result.output
        # Should show transforms and checks
        assert "Transforms" in result.output or "transforms" in result.output.lower()

    def test_info_with_invalid_config_exits_1(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --config with invalid file exits with error."""
        nonexistent = temp_dir / "nonexistent.yml"
        result = cli_runner.invoke(app, ["info", "--config", str(nonexistent)])

        assert result.exit_code != 0

    def test_info_shows_commands_help(self, cli_runner: CliRunner):
        """Test that info shows available commands."""
        result = cli_runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "run" in result.output
        assert "validate" in result.output

    def test_info_backends_shows_descriptions(self, cli_runner: CliRunner):
        """Test that backends list includes descriptions."""
        result = cli_runner.invoke(app, ["info", "--backends"])

        assert result.exit_code == 0
        # Table should have description column content
        # Common backends should have descriptions
        assert "Backend" in result.output or "backend" in result.output.lower()
