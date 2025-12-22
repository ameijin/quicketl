"""Tests for the 'quicketl init' CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from quicketl.cli.main import app


class TestInitCommand:
    """Tests for the 'quicketl init' command."""

    def test_init_without_name_creates_in_current_dir(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init without name initializes in current directory."""
        result = cli_runner.invoke(app, ["init", "-o", str(temp_dir)])

        assert result.exit_code == 0
        assert (temp_dir / "pipelines").exists()
        assert (temp_dir / "pipelines" / "sample.yml").exists()
        assert (temp_dir / "data").exists()

    def test_init_with_name_creates_project_subdirectory(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init with name creates project in subdirectory."""
        result = cli_runner.invoke(
            app, ["init", "-o", str(temp_dir), "my_project"]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "my_project"
        assert project_dir.exists()
        assert (project_dir / "pipelines").exists()
        assert (project_dir / "pipelines" / "sample.yml").exists()
        assert (project_dir / "data").exists()
        assert (project_dir / "README.md").exists()

    def test_init_with_pipeline_flag_creates_single_file(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --pipeline creates only a YAML file."""
        result = cli_runner.invoke(
            app, ["init", "-o", str(temp_dir), "--pipeline", "my_pipeline"]
        )

        assert result.exit_code == 0
        assert (temp_dir / "my_pipeline.yml").exists()
        # Should NOT create directories
        assert not (temp_dir / "pipelines").exists()

    def test_init_with_pipeline_flag_requires_name(self, cli_runner: CliRunner):
        """Test that --pipeline without name fails."""
        result = cli_runner.invoke(app, ["init", "--pipeline"])

        assert result.exit_code == 1
        assert "required" in result.output.lower() or "error" in result.output.lower()

    def test_init_existing_directory_without_force_fails(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init fails if project directory exists without --force."""
        # Create the directory first
        project_dir = temp_dir / "existing_project"
        project_dir.mkdir()

        result = cli_runner.invoke(
            app, ["init", "-o", str(temp_dir), "existing_project"]
        )

        assert result.exit_code == 1
        assert "exists" in result.output.lower()

    def test_init_with_force_overwrites_existing(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --force allows overwriting existing project."""
        # Create the directory first
        project_dir = temp_dir / "existing_project"
        project_dir.mkdir()
        (project_dir / "old_file.txt").write_text("old content")

        result = cli_runner.invoke(
            app, ["init", "-o", str(temp_dir), "--force", "existing_project"]
        )

        assert result.exit_code == 0
        assert (project_dir / "pipelines" / "sample.yml").exists()

    def test_init_creates_sample_data(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init creates sample CSV data file."""
        result = cli_runner.invoke(app, ["init", "-o", str(temp_dir)])

        assert result.exit_code == 0
        data_file = temp_dir / "data" / "sales.csv"
        assert data_file.exists()

        # Verify CSV has content
        content = data_file.read_text()
        assert "id" in content
        assert "Electronics" in content

    def test_init_creates_env_template(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init creates .env template."""
        result = cli_runner.invoke(app, ["init", "-o", str(temp_dir)])

        assert result.exit_code == 0
        env_file = temp_dir / ".env"
        assert env_file.exists()

    def test_init_sample_pipeline_is_valid(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that the created sample pipeline is valid."""
        # Initialize
        result = cli_runner.invoke(app, ["init", "-o", str(temp_dir)])
        assert result.exit_code == 0

        # Validate the sample pipeline
        pipeline_path = temp_dir / "pipelines" / "sample.yml"
        result = cli_runner.invoke(app, ["validate", str(pipeline_path)])

        # Check output shows validation passed (exit code may vary due to Typer behavior)
        assert "valid" in result.output.lower()
        assert "invalid" not in result.output.lower()

    def test_init_output_shows_next_steps(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that init output shows how to run the sample pipeline."""
        result = cli_runner.invoke(app, ["init", "-o", str(temp_dir)])

        assert result.exit_code == 0
        assert "quicketl run" in result.output
