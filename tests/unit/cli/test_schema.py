"""Tests for the 'quicketl schema' CLI command."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from quicketl.cli.main import app


def strip_ansi_and_rich(text: str) -> str:
    """Strip ANSI escape codes and Rich formatting from text."""
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Remove extra whitespace and newlines inserted by Rich
    text = re.sub(r'\n\s*', '\n', text)
    return text


class TestSchemaCommand:
    """Tests for the 'quicketl schema' command."""

    def test_schema_outputs_valid_json(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that schema outputs valid JSON to file."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(app, ["schema", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        # Read from file to avoid Rich formatting issues
        schema = json.loads(output_file.read_text())
        assert "$schema" in schema
        assert "title" in schema

    def test_schema_includes_json_schema_draft(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that schema includes JSON Schema draft reference."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(app, ["schema", "-o", str(output_file)])

        assert result.exit_code == 0

        schema = json.loads(output_file.read_text())
        assert "draft-07" in schema["$schema"]

    def test_schema_includes_pipeline_properties(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that schema includes expected pipeline properties."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(app, ["schema", "-o", str(output_file)])

        assert result.exit_code == 0

        schema = json.loads(output_file.read_text())
        properties = schema.get("properties", {})

        # Core pipeline properties should be present
        assert "name" in properties
        assert "source" in properties or "$defs" in schema
        assert "sink" in properties or "$defs" in schema

    def test_schema_with_output_writes_to_file(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that --output writes schema to file."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(
            app, ["schema", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify file contains valid JSON
        schema = json.loads(output_file.read_text())
        assert "$schema" in schema

    def test_schema_with_custom_indent(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that --indent controls JSON formatting."""
        result = cli_runner.invoke(app, ["schema", "--indent", "4"])

        assert result.exit_code == 0
        # With indent 4, lines should have 4-space indentation
        lines = result.output.split("\n")
        indented_lines = [line for line in lines if line.startswith("    ") and not line.startswith("        ")]
        assert len(indented_lines) > 0

    def test_schema_output_file_message(
        self, cli_runner: CliRunner, temp_dir: Path
    ):
        """Test that writing to file shows success message."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(
            app, ["schema", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert "written to" in result.output.lower() or str(output_file) in result.output

    def test_schema_includes_transform_definitions(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that schema includes transform type definitions."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(app, ["schema", "-o", str(output_file)])

        assert result.exit_code == 0

        schema = json.loads(output_file.read_text())
        schema_str = json.dumps(schema)

        # Should reference transform types
        assert "filter" in schema_str.lower() or "select" in schema_str.lower()

    def test_schema_includes_check_definitions(self, cli_runner: CliRunner, temp_dir: Path):
        """Test that schema includes check type definitions."""
        output_file = temp_dir / "schema.json"
        result = cli_runner.invoke(app, ["schema", "-o", str(output_file)])

        assert result.exit_code == 0

        schema = json.loads(output_file.read_text())
        schema_str = json.dumps(schema)

        # Should reference check types
        assert "not_null" in schema_str.lower() or "row_count" in schema_str.lower()
