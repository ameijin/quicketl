"""Tests for the 'quicketl platform' CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quicketl.cli.main import app

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

    def test_platform_help_lists_validate(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["platform", "--help"])

        assert result.exit_code == 0
        assert "validate" in result.output
