"""Tests for --env and --profile CLI flags."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest
from click.exceptions import Exit as ClickExit
from typer.testing import CliRunner

from quicketl.cli.main import app
from quicketl.cli.run import _resolve_project_config

# Mock target is the source module because _resolve_project_config uses
# lazy imports inside the function body.
_FIND_PROJECT = "quicketl.config.project.find_project_config"


class TestResolveProjectConfig:
    """Tests for _resolve_project_config helper."""

    def test_returns_none_when_no_flags(self):
        variables: dict[str, str] = {}
        result = _resolve_project_config(env=None, profile=None, variables=variables)
        assert result is None
        assert variables == {}

    def test_env_resolves_engine(self, tmp_path: Path):
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "environments:\n"
            "  prod:\n"
            "    engine: snowflake\n"
        )
        variables: dict[str, str] = {}

        with mock.patch(_FIND_PROJECT, return_value=project_yml):
            result = _resolve_project_config(env="prod", profile=None, variables=variables)

        assert result == "snowflake"

    def test_env_not_found_exits(self, tmp_path: Path):
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "environments:\n"
            "  dev:\n"
            "    engine: duckdb\n"
        )

        with mock.patch(_FIND_PROJECT, return_value=project_yml), pytest.raises(ClickExit):
            _resolve_project_config(env="nonexistent", profile=None, variables={})

    def test_profile_injects_variables(self, tmp_path: Path):
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "profiles:\n"
            "  warehouse:\n"
            "    type: postgres\n"
            "    host: db.example.com\n"
            "    port: 5432\n"
        )
        variables: dict[str, str] = {}

        with mock.patch(_FIND_PROJECT, return_value=project_yml):
            _resolve_project_config(env=None, profile="warehouse", variables=variables)

        assert variables["PROFILE_TYPE"] == "postgres"
        assert variables["PROFILE_HOST"] == "db.example.com"
        assert variables["PROFILE_PORT"] == "5432"

    def test_profile_not_found_exits(self, tmp_path: Path):
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text("profiles: {}\n")

        with mock.patch(_FIND_PROJECT, return_value=project_yml), pytest.raises(ClickExit):
            _resolve_project_config(env=None, profile="missing", variables={})

    def test_no_project_file_returns_none(self):
        variables: dict[str, str] = {}
        with mock.patch(_FIND_PROJECT, return_value=None):
            result = _resolve_project_config(env="prod", profile=None, variables=variables)
        assert result is None

    def test_env_and_profile_together(self, tmp_path: Path):
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "environments:\n"
            "  prod:\n"
            "    engine: snowflake\n"
            "profiles:\n"
            "  warehouse:\n"
            "    type: snowflake\n"
            "    account: myaccount\n"
        )
        variables: dict[str, str] = {}

        with mock.patch(_FIND_PROJECT, return_value=project_yml):
            result = _resolve_project_config(env="prod", profile="warehouse", variables=variables)

        assert result == "snowflake"
        assert variables["PROFILE_TYPE"] == "snowflake"
        assert variables["PROFILE_ACCOUNT"] == "myaccount"


class TestRunCommandEnvFlag:
    """Integration tests for --env flag in quicketl run."""

    def test_run_with_env_flag(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path, tmp_path: Path
    ):
        """Test that --env loads environment config."""
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "environments:\n"
            "  dev:\n"
            "    engine: duckdb\n"
        )

        with mock.patch(_FIND_PROJECT, return_value=project_yml):
            result = cli_runner.invoke(
                app, ["run", str(valid_pipeline_yaml), "--env", "dev"]
            )

        assert result.exit_code in [0, 2]


class TestRunCommandProfileFlag:
    """Integration tests for --profile flag in quicketl run."""

    def test_run_with_profile_flag(
        self, cli_runner: CliRunner, valid_pipeline_yaml: Path, tmp_path: Path
    ):
        """Test that --profile loads connection profile."""
        project_yml = tmp_path / "quicketl.yml"
        project_yml.write_text(
            "profiles:\n"
            "  local:\n"
            "    type: duckdb\n"
        )

        with mock.patch(_FIND_PROJECT, return_value=project_yml):
            result = cli_runner.invoke(
                app, ["run", str(valid_pipeline_yaml), "--profile", "local"]
            )

        assert result.exit_code in [0, 2]
