"""End-to-end integration tests for pipeline execution.

These tests verify complete pipeline execution from YAML to output.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quicketl.pipeline import Pipeline


class TestPipelineE2E:
    """End-to-end pipeline execution tests."""

    @pytest.mark.integration
    def test_csv_to_parquet_pipeline(self, temp_dir: Path):
        """Test a complete CSV to Parquet pipeline."""
        # Create input data
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name,amount\n1,Alice,100\n2,Bob,200\n3,Charlie,150\n")

        output_path = temp_dir / "output.parquet"

        yaml_content = f"""
name: csv_to_parquet
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

transforms:
  - op: filter
    predicate: amount > 100

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        # Run pipeline
        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        # Verify
        assert result.succeeded
        assert output_path.exists()

        # Read back and verify
        df = pd.read_parquet(output_path)
        assert len(df) == 2
        assert set(df["name"].tolist()) == {"Bob", "Charlie"}

    @pytest.mark.integration
    def test_pipeline_with_transforms_chain(self, temp_dir: Path):
        """Test pipeline with multiple transform operations."""
        input_path = temp_dir / "input.csv"
        input_path.write_text(
            "id,first_name,last_name,amount\n"
            "1,  alice  ,smith,100\n"
            "2,bob,jones,200\n"
            "3,charlie,brown,150\n"
        )

        output_path = temp_dir / "output.parquet"

        yaml_content = f"""
name: transform_chain
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

transforms:
  - op: derive_column
    name: full_name
    expr: "CONCAT(TRIM(first_name), ' ', last_name)"

  - op: derive_column
    name: amount_doubled
    expr: "amount * 2"

  - op: select
    columns: [id, full_name, amount_doubled]

  - op: sort
    by: [amount_doubled]

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded
        df = pd.read_parquet(output_path)
        assert list(df.columns) == ["id", "full_name", "amount_doubled"]
        assert df["amount_doubled"].tolist() == [200, 300, 400]  # sorted

    @pytest.mark.integration
    def test_pipeline_with_quality_checks(self, temp_dir: Path):
        """Test pipeline with quality checks that pass."""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name,amount\n1,Alice,100\n2,Bob,200\n")

        output_path = temp_dir / "output.parquet"

        yaml_content = f"""
name: with_checks
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

checks:
  - type: not_null
    columns: [id, name]

  - type: row_count
    min: 1
    max: 100

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded
        assert output_path.exists()

    @pytest.mark.integration
    def test_pipeline_with_variable_substitution(self, temp_dir: Path):
        """Test pipeline with variable substitution."""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name,amount\n1,Alice,100\n2,Bob,200\n")

        output_path = temp_dir / "output.parquet"

        yaml_content = """
name: ${PIPELINE_NAME}
engine: duckdb

source:
  type: file
  path: ${INPUT_PATH}
  format: csv

transforms:
  - op: filter
    predicate: "amount > ${THRESHOLD}"

sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(
            yaml_path,
            variables={
                "PIPELINE_NAME": "var_substitution_test",
                "INPUT_PATH": str(input_path),
                "OUTPUT_PATH": str(output_path),
                "THRESHOLD": "150",
            },
        )
        result = pipeline.run()

        assert result.succeeded
        assert result.pipeline_name == "var_substitution_test"
        df = pd.read_parquet(output_path)
        assert len(df) == 1
        assert df["name"].iloc[0] == "Bob"

    @pytest.mark.integration
    def test_pipeline_dry_run_no_output(self, temp_dir: Path):
        """Test that dry_run doesn't create output file."""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name\n1,Alice\n")

        output_path = temp_dir / "should_not_exist.parquet"

        yaml_content = f"""
name: dry_run_test
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run(dry_run=True)

        assert result.succeeded
        assert not output_path.exists()

    @pytest.mark.integration
    def test_pipeline_with_aggregation(self, temp_dir: Path):
        """Test pipeline with aggregation transform."""
        input_path = temp_dir / "input.csv"
        input_path.write_text(
            "id,region,amount\n"
            "1,North,100\n"
            "2,South,200\n"
            "3,North,150\n"
            "4,South,250\n"
        )

        output_path = temp_dir / "output.parquet"

        yaml_content = f"""
name: aggregation_test
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

transforms:
  - op: aggregate
    group_by: [region]
    aggs:
      total: SUM(amount)
      count: COUNT(id)

  - op: sort
    by: [region]

sink:
  type: file
  path: {output_path}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded
        df = pd.read_parquet(output_path)
        assert len(df) == 2

        north = df[df["region"] == "North"].iloc[0]
        assert north["total"] == 250
        assert north["count"] == 2


class TestPipelineErrors:
    """Tests for pipeline error handling."""

    @pytest.mark.integration
    def test_missing_source_file_fails(self, temp_dir: Path):
        """Test that missing source file causes failure."""
        yaml_content = f"""
name: missing_source
engine: duckdb

source:
  type: file
  path: {temp_dir / "nonexistent.csv"}
  format: csv

sink:
  type: file
  path: {temp_dir / "output.parquet"}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.failed
        assert result.error is not None

    @pytest.mark.integration
    def test_check_failure_fails_pipeline(self, temp_dir: Path):
        """Test that failing quality check fails pipeline."""
        input_path = temp_dir / "input.csv"
        input_path.write_text("id,name\n1,Alice\n2,\n")  # Empty name

        yaml_content = f"""
name: check_failure
engine: duckdb

source:
  type: file
  path: {input_path}
  format: csv

checks:
  - type: not_null
    columns: [name]

sink:
  type: file
  path: {temp_dir / "output.parquet"}
  format: parquet
"""
        yaml_path = temp_dir / "pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        # Should fail or be partial due to check failure
        assert not result.succeeded or result.status.value == "partial"
