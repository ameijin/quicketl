"""CLI test fixtures and configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI test runner for testing Typer commands."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_pipeline_yaml(temp_dir: Path) -> Path:
    """Create a valid pipeline YAML file for testing."""
    yaml_content = """
name: test_pipeline
description: A test pipeline
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

transforms:
  - op: filter
    predicate: amount > 100
  - op: select
    columns: [id, name, amount]

checks:
  - type: not_null
    columns: [id]
  - type: row_count
    min: 1

sink:
  type: file
  path: {output_path}
  format: parquet
"""
    # Create input CSV
    input_path = temp_dir / "input.csv"
    input_path.write_text("id,name,amount\n1,Alice,150\n2,Bob,50\n3,Charlie,200\n")

    output_path = temp_dir / "output.parquet"

    yaml_path = temp_dir / "pipeline.yml"
    yaml_path.write_text(
        yaml_content.format(input_path=input_path, output_path=output_path)
    )
    return yaml_path


@pytest.fixture
def invalid_pipeline_yaml(temp_dir: Path) -> Path:
    """Create an invalid pipeline YAML file for testing."""
    yaml_content = """
name: invalid_pipeline
# Missing required fields: source, sink
"""
    yaml_path = temp_dir / "invalid.yml"
    yaml_path.write_text(yaml_content)
    return yaml_path


@pytest.fixture
def pipeline_with_vars_yaml(temp_dir: Path) -> Path:
    """Create a pipeline YAML file with variables for testing."""
    yaml_content = """
name: variable_test_pipeline
engine: duckdb

source:
  type: file
  path: ${INPUT_PATH}
  format: csv

transforms:
  - op: filter
    predicate: amount > ${THRESHOLD:-100}

sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
"""
    yaml_path = temp_dir / "pipeline_vars.yml"
    yaml_path.write_text(yaml_content)
    return yaml_path
