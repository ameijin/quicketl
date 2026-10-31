"""Tests for the 'quicketl init' wizard and the --kind option."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from quicketl.cli.main import app
from quicketl.platform.spec import load_platform_spec

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner


@pytest.fixture
def interactive(monkeypatch):
    """Make `quicketl init` behave as if it runs in a terminal."""
    monkeypatch.setattr("quicketl.cli.init._is_interactive", lambda: True)


@pytest.fixture
def in_temp_dir(temp_dir: Path, monkeypatch) -> Path:
    project = temp_dir / "acme-data"
    project.mkdir()
    monkeypatch.chdir(project)
    return project


class TestWizard:
    def test_enter_everywhere_creates_a_platform_spec_here(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init"], input="\n\n\n\n")

        assert result.exit_code == 0, result.output
        spec = load_platform_spec(in_temp_dir / "platform.yml")
        assert spec.name == "acme_data"
        assert spec.warehouse.type == "snowflake"
        assert "quicketl platform scaffold" in result.output

    def test_platform_answers_are_used(self, cli_runner: CliRunner, interactive, in_temp_dir: Path):
        result = cli_runner.invoke(
            app, ["init"], input="platform\nlake\nlake_platform\ndatabricks\n"
        )

        assert result.exit_code == 0, result.output
        spec = load_platform_spec(in_temp_dir / "lake" / "platform.yml")
        assert spec.name == "lake_platform"
        assert spec.warehouse.type == "databricks"

    def test_name_default_follows_the_chosen_folder(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init"], input="platform\nsales-platform\n\n\n")

        assert result.exit_code == 0, result.output
        spec = load_platform_spec(in_temp_dir / "sales-platform" / "platform.yml")
        assert spec.name == "sales_platform"

    def test_invalid_answer_is_asked_again(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(
            app, ["init"], input="warehouse\nplatform\n\n\nbigquery\nsnowflake\n"
        )

        assert result.exit_code == 0, result.output
        assert (in_temp_dir / "platform.yml").exists()

    def test_invalid_platform_name_fails_without_writing(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init"], input="platform\n.\nAcme\n\n")

        assert result.exit_code == 1
        assert "lowercase" in result.output
        assert not (in_temp_dir / "platform.yml").exists()

    def test_pipeline_choice_creates_a_pipeline_project(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init"], input="pipeline\nmyproj\n")

        assert result.exit_code == 0, result.output
        assert (in_temp_dir / "myproj" / "pipelines" / "sample.yml").exists()
        assert (in_temp_dir / "myproj" / "quicketl.yml").exists()

    def test_pipeline_choice_with_blank_name_uses_this_folder(
        self, cli_runner: CliRunner, interactive, in_temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init"], input="pipeline\n\n")

        assert result.exit_code == 0, result.output
        assert (in_temp_dir / "pipelines" / "sample.yml").exists()

    def test_existing_flags_never_prompt(self, cli_runner: CliRunner, interactive, temp_dir: Path):
        """1.x calls such as `quicketl init NAME -o DIR` keep working without questions."""
        result = cli_runner.invoke(app, ["init", "proj", "-o", str(temp_dir)], input="")

        assert result.exit_code == 0, result.output
        assert (temp_dir / "proj" / "pipelines" / "sample.yml").exists()
        assert "What do you want to set up" not in result.output


class TestNonInteractive:
    def test_bare_init_without_terminal_asks_for_kind(
        self, cli_runner: CliRunner, monkeypatch, in_temp_dir: Path
    ):
        monkeypatch.setattr("quicketl.cli.init._is_interactive", lambda: False)

        result = cli_runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "--kind" in result.output
        assert list(in_temp_dir.iterdir()) == []

    def test_kind_platform_with_name(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["init", "acme", "--kind", "platform", "-o", str(temp_dir)])

        assert result.exit_code == 0, result.output
        assert load_platform_spec(temp_dir / "acme" / "platform.yml").name == "acme"

    def test_kind_platform_without_name_uses_output_dir(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        result = cli_runner.invoke(app, ["init", "--kind", "platform", "-o", str(temp_dir)])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "platform.yml").exists()

    def test_kind_platform_respects_force(self, cli_runner: CliRunner, temp_dir: Path):
        (temp_dir / "platform.yml").write_text("keep\n")

        refused = cli_runner.invoke(app, ["init", "--kind", "platform", "-o", str(temp_dir)])
        forced = cli_runner.invoke(
            app, ["init", "--kind", "platform", "-o", str(temp_dir), "--force"]
        )

        assert refused.exit_code == 1
        assert forced.exit_code == 0, forced.output
        assert load_platform_spec(temp_dir / "platform.yml").warehouse.type == "snowflake"

    def test_kind_pipeline_matches_old_behavior(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["init", "--kind", "pipeline", "-o", str(temp_dir)])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "pipelines" / "sample.yml").exists()

    def test_kind_platform_with_pipeline_flag_is_rejected(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        result = cli_runner.invoke(
            app, ["init", "p1", "--kind", "platform", "-p", "-o", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "--pipeline" in result.output
        assert list(temp_dir.iterdir()) == []
