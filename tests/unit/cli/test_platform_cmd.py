"""Tests for the 'quicketl platform' CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args

from quicketl.cli.main import app
from quicketl.cli.platform import WarehouseChoice
from quicketl.platform.spec import WarehouseType, load_platform_spec

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

VALID_SPEC = """
name: acme_data
warehouse:
  type: snowflake
domains:
  - name: sales
roles:
  - name: analyst
    access: {marts: read}
sources:
  - name: orders
    domain: sales
    location: s3://example-landing/sales/orders/
"""

INVALID_SPEC = """
name: acme_data
warehouse:
  type: snowflake
domains:
  - name: sales
roles:
  - name: analyst
    access: {gold: read}
"""


class TestPlatformInit:
    def test_warehouse_choices_match_the_spec(self):
        assert {c.value for c in WarehouseChoice} == set(get_args(WarehouseType))

    def test_writes_a_valid_starter_spec(self, cli_runner: CliRunner, temp_dir: Path):
        project = temp_dir / "acme-data"
        project.mkdir()

        result = cli_runner.invoke(app, ["platform", "init", str(project)])

        assert result.exit_code == 0, result.output
        spec = load_platform_spec(project / "platform.yml")
        assert spec.name == "acme_data"
        assert spec.warehouse.type == "snowflake"

    def test_starter_spec_explains_itself(self, cli_runner: CliRunner, temp_dir: Path):
        cli_runner.invoke(app, ["platform", "init", str(temp_dir)])

        text = (temp_dir / "platform.yml").read_text()
        assert "# " in text
        assert "quicketl platform validate" in text

    def test_creates_missing_folder(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["platform", "init", str(temp_dir / "new" / "proj")])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "new" / "proj" / "platform.yml").exists()

    def test_name_and_warehouse_options(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(
            app,
            ["platform", "init", str(temp_dir), "--name", "lake", "--warehouse", "databricks"],
        )

        assert result.exit_code == 0, result.output
        spec = load_platform_spec(temp_dir / "platform.yml")
        assert spec.name == "lake"
        assert spec.warehouse.type == "databricks"

    def test_redshift_serverless(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(
            app, ["platform", "init", str(temp_dir), "-w", "redshift_serverless"]
        )

        assert result.exit_code == 0, result.output
        assert load_platform_spec(temp_dir / "platform.yml").warehouse.type == (
            "redshift_serverless"
        )

    def test_unknown_warehouse_rejected(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["platform", "init", str(temp_dir), "-w", "bigquery"])

        assert result.exit_code != 0
        assert not (temp_dir / "platform.yml").exists()

    def test_invalid_name_rejected(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["platform", "init", str(temp_dir), "--name", "Acme"])

        assert result.exit_code == 1
        assert "lowercase" in result.output
        assert not (temp_dir / "platform.yml").exists()

    def test_folder_name_starting_with_digit_gets_prefix(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        project = temp_dir / "2026 Platform"
        project.mkdir()

        result = cli_runner.invoke(app, ["platform", "init", str(project)])

        assert result.exit_code == 0, result.output
        assert load_platform_spec(project / "platform.yml").name == "p_2026_platform"

    def test_does_not_overwrite_existing_spec(self, cli_runner: CliRunner, temp_dir: Path):
        existing = temp_dir / "platform.yml"
        existing.write_text("keep me\n")

        result = cli_runner.invoke(app, ["platform", "init", str(temp_dir)])

        assert result.exit_code == 1
        assert "--force" in result.output
        assert existing.read_text() == "keep me\n"

    def test_force_overwrites(self, cli_runner: CliRunner, temp_dir: Path):
        (temp_dir / "platform.yml").write_text("old\n")

        result = cli_runner.invoke(app, ["platform", "init", str(temp_dir), "--force"])

        assert result.exit_code == 0, result.output
        assert load_platform_spec(temp_dir / "platform.yml").warehouse.type == "snowflake"

    def test_defaults_to_cwd(self, cli_runner: CliRunner, temp_dir: Path, monkeypatch):
        monkeypatch.chdir(temp_dir)

        result = cli_runner.invoke(app, ["platform", "init"])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "platform.yml").exists()


class TestPlatformValidate:
    def test_valid_spec_exits_0_with_summary(self, cli_runner: CliRunner, temp_dir: Path):
        path = temp_dir / "platform.yml"
        path.write_text(VALID_SPEC)

        result = cli_runner.invoke(app, ["platform", "validate", str(path)])

        assert result.exit_code == 0, result.output
        assert "Platform spec is valid" in result.output
        assert "snowflake" in result.output
        assert "Domains: 1" in result.output
        assert "Roles: 1" in result.output
        assert "Sources: 1" in result.output

    def test_invalid_spec_exits_1_with_field_and_reason(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        path = temp_dir / "platform.yml"
        path.write_text(INVALID_SPEC)

        result = cli_runner.invoke(app, ["platform", "validate", str(path)])

        assert result.exit_code == 1
        assert "Platform spec is invalid" in result.output
        assert "unknown layer 'gold'" in result.output

    def test_defaults_to_platform_yml_in_cwd(
        self, cli_runner: CliRunner, temp_dir: Path, monkeypatch
    ):
        (temp_dir / "platform.yml").write_text(VALID_SPEC)
        monkeypatch.chdir(temp_dir)

        result = cli_runner.invoke(app, ["platform", "validate"])

        assert result.exit_code == 0, result.output

    def test_missing_file_exits_1(self, cli_runner: CliRunner, temp_dir: Path):
        result = cli_runner.invoke(app, ["platform", "validate", str(temp_dir / "nope.yml")])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_platform_help_lists_commands(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["platform", "--help"])

        assert result.exit_code == 0
        assert "init" in result.output
        assert "validate" in result.output
