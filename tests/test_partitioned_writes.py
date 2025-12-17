"""Tests for partitioned file writes."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


class TestPartitionedWrites:
    """Tests for partitioned file writes."""

    def test_write_partitioned_parquet(self, engine, sample_data, temp_dir: Path):
        """Test writing parquet partitioned by a column."""
        output_path = temp_dir / "partitioned_output"

        result = engine.write_file(
            sample_data,
            str(output_path),
            format="parquet",
            partition_by=["region"],
        )

        assert result.rows_written == 5

        # Verify partitioned directory structure
        assert output_path.exists()
        assert output_path.is_dir()

        # Check partition directories exist
        partition_dirs = [d for d in output_path.iterdir() if d.is_dir()]
        assert len(partition_dirs) == 3  # North, South, East

        # Verify partitions contain the expected regions
        # PyArrow may use either "region=North" (Hive style) or just "North" (directory style)
        partition_names = {d.name for d in partition_dirs}
        # Check that we have 3 distinct partitions for North, South, East
        has_north = any("North" in name for name in partition_names)
        has_south = any("South" in name for name in partition_names)
        has_east = any("East" in name for name in partition_names)
        assert has_north and has_south and has_east

    def test_write_partitioned_parquet_multiple_columns(self, engine, temp_dir: Path):
        """Test writing parquet partitioned by multiple columns."""
        import ibis

        # Create data with multiple partition columns
        table = ibis.memtable(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "date": ["2025-01", "2025-01", "2025-02", "2025-02", "2025-01", "2025-02"],
                "region": ["North", "South", "North", "South", "North", "South"],
                "value": [100, 200, 150, 250, 175, 225],
            }
        )

        output_path = temp_dir / "multi_partitioned"

        result = engine.write_file(
            table,
            str(output_path),
            format="parquet",
            partition_by=["date", "region"],
        )

        assert result.rows_written == 6

        # Verify nested partition structure
        # Should have date partitions at top level
        date_dirs = [d for d in output_path.iterdir() if d.is_dir()]
        assert len(date_dirs) == 2  # 2025-01, 2025-02

        # Each date should have region subdirs
        for date_dir in date_dirs:
            region_dirs = [d for d in date_dir.iterdir() if d.is_dir()]
            assert len(region_dirs) == 2  # North, South

    def test_write_partitioned_csv(self, engine, sample_data, temp_dir: Path):
        """Test writing CSV partitioned by a column."""
        output_path = temp_dir / "partitioned_csv"

        result = engine.write_file(
            sample_data,
            str(output_path),
            format="csv",
            partition_by=["region"],
        )

        assert result.rows_written == 5

        # Verify partitioned directory structure
        assert output_path.exists()
        assert output_path.is_dir()

        # Check partition directories exist
        partition_dirs = [d for d in output_path.iterdir() if d.is_dir()]
        assert len(partition_dirs) == 3

    def test_write_non_partitioned_parquet(self, engine, sample_data, temp_dir: Path):
        """Test writing non-partitioned parquet still works."""
        output_path = temp_dir / "single_file.parquet"

        result = engine.write_file(
            sample_data,
            str(output_path),
            format="parquet",
            partition_by=None,
        )

        assert result.rows_written == 5
        assert output_path.exists()
        assert output_path.is_file()

        # Verify content
        df = pq.read_table(output_path).to_pandas()
        assert len(df) == 5

    def test_partitioned_write_via_pipeline(self, temp_dir: Path):
        """Test partitioned writes through pipeline config."""
        from quicketl.pipeline import Pipeline

        # Create test data
        table = pa.table(
            {
                "id": [1, 2, 3, 4],
                "region": ["North", "South", "North", "South"],
                "value": [100, 200, 150, 250],
            }
        )
        input_path = temp_dir / "input.parquet"
        pq.write_table(table, input_path)

        yaml_content = f"""
name: partitioned_write_test
engine: duckdb

source:
  type: file
  path: {input_path}
  format: parquet

transforms:
  - op: select
    columns: [id, region, value]

sink:
  type: file
  path: {temp_dir}/partitioned_output
  format: parquet
  partition_by: [region]
"""
        yaml_path = temp_dir / "partition_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded, f"Pipeline failed: {result.error}"
        assert result.rows_written == 4

        # Verify partitioned output
        output_path = temp_dir / "partitioned_output"
        assert output_path.exists()
        partition_dirs = [d for d in output_path.iterdir() if d.is_dir()]
        assert len(partition_dirs) == 2  # North, South
