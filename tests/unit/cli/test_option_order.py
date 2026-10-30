"""Tests that CLI options work both before and after the positional argument."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quicketl.cli.main import app


class TestRunOptionOrder:
    """`quicketl run FILE [OPTIONS]` must behave like `quicketl run [OPTIONS] FILE`."""

    def test_dry_run_after_positional(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path, temp_dir: Path
    ):
        """--dry-run after the config file succeeds and writes nothing."""
        result = cli_runner.invoke(app, ["run", str(valid_pipeline_yaml), "--dry-run"])

        assert result.exit_code == 0, result.output
        assert not (temp_dir / "output.parquet").exists()

    def test_dry_run_before_positional(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path, temp_dir: Path
    ):
        """--dry-run before the config file keeps working."""
        result = cli_runner.invoke(app, ["run", "--dry-run", str(valid_pipeline_yaml)])

        assert result.exit_code == 0, result.output
        assert not (temp_dir / "output.parquet").exists()

    def test_json_after_positional(self, cli_runner: CliRunner, valid_pipeline_yaml: Path):
        """--json after the config file emits parseable JSON."""
        result = cli_runner.invoke(app, ["run", str(valid_pipeline_yaml), "--dry-run", "--json"])

        assert result.exit_code == 0, result.output
        # Structured log lines may precede the JSON document on stdout.
        data = json.loads(result.output[result.output.index('{\n  "pipeline_name"') :])
        assert data["pipeline_name"] == "test_pipeline"

    def test_var_after_positional(
        self, cli_runner: CliRunner, pipeline_with_vars_yaml: Path, temp_dir: Path
    ):
        """--var after the config file substitutes variables."""
        input_path = temp_dir / "vars_input.csv"
        input_path.write_text("id,name,amount\n1,Alice,150\n")
        output_path = temp_dir / "vars_output.parquet"

        result = cli_runner.invoke(
            app,
            [
                "run",
                str(pipeline_with_vars_yaml),
                "--var",
                f"INPUT_PATH={input_path}",
                "--var",
                f"OUTPUT_PATH={output_path}",
            ],
        )

        assert result.exit_code == 0, result.output
        assert output_path.exists()

    def test_missing_config_file_still_fails(self, cli_runner: CliRunner):
        """Omitting the config file is still a usage error."""
        result = cli_runner.invoke(app, ["run", "--dry-run"])

        assert result.exit_code == 2


class TestValidateOptionOrder:
    """`quicketl validate FILE [OPTIONS]` must work."""

    def test_verbose_after_positional(self, cli_runner: CliRunner, valid_pipeline_yaml: Path):
        """--verbose after the config file succeeds."""
        result = cli_runner.invoke(app, ["validate", str(valid_pipeline_yaml), "--verbose"])

        assert result.exit_code == 0, result.output
        assert "Configuration is valid" in result.output


class TestInitOptionOrder:
    """`quicketl init NAME [OPTIONS]` must work."""

    def test_options_after_positional(self, cli_runner: CliRunner, temp_dir: Path):
        """--pipeline and -o after the name create the pipeline file."""
        result = cli_runner.invoke(app, ["init", "my_pipeline", "--pipeline", "-o", str(temp_dir)])

        assert result.exit_code == 0, result.output
        assert any(temp_dir.rglob("my_pipeline*.yml"))
