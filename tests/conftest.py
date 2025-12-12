"""Pytest configuration and fixtures for ETLX tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import ibis.expr.types as ir


@pytest.fixture(params=["duckdb", "polars"])
def engine_name(request: pytest.FixtureRequest) -> str:
    """Parametrize tests across supported backends."""
    return request.param


@pytest.fixture
def engine(engine_name: str):
    """Create an ETLXEngine for testing."""
    from quicketl.engines import ETLXEngine

    return ETLXEngine(backend=engine_name)


@pytest.fixture
def sample_data(engine) -> ir.Table:
    """Create sample test data as an Ibis table."""
    import pandas as pd

    # Create sample data
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        "region": ["North", "South", "North", "East", "South"],
        "active": [True, True, False, True, True],
    }

    # Create table using the engine's backend connection
    df = pd.DataFrame(data)
    return engine.connection.create_table("sample_data", df, overwrite=True)


@pytest.fixture
def sample_data_with_nulls(engine) -> ir.Table:
    """Create sample data with null values."""
    import numpy as np
    import pandas as pd

    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", None, "Charlie", "Diana", None],
        "amount": [100.0, 200.0, np.nan, 300.0, 250.0],
        "region": ["North", "South", "North", None, "South"],
    }

    df = pd.DataFrame(data)
    return engine.connection.create_table("sample_data_with_nulls", df, overwrite=True)


@pytest.fixture
def sample_data_with_duplicates(engine) -> ir.Table:
    """Create sample data with duplicate rows."""
    import pandas as pd

    data = {
        "id": [1, 2, 2, 3, 3],
        "name": ["Alice", "Bob", "Bob", "Charlie", "Charlie"],
        "amount": [100.0, 200.0, 200.0, 150.0, 150.0],
    }

    df = pd.DataFrame(data)
    return engine.connection.create_table("sample_data_with_duplicates", df, overwrite=True)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_parquet(temp_dir: Path, sample_data) -> Path:
    """Create a sample parquet file."""
    path = temp_dir / "sample.parquet"
    sample_data.to_parquet(str(path))
    return path


@pytest.fixture
def sample_csv(temp_dir: Path, sample_data) -> Path:
    """Create a sample CSV file."""
    path = temp_dir / "sample.csv"
    sample_data.to_csv(str(path))
    return path


@pytest.fixture
def sample_pipeline_yaml(temp_dir: Path, sample_parquet: Path) -> Path:
    """Create a sample pipeline YAML file."""
    yaml_content = f"""
name: test_pipeline
description: Test pipeline for unit tests
engine: duckdb

source:
  type: file
  path: {sample_parquet}
  format: parquet

transforms:
  - op: filter
    predicate: amount > 100
  - op: select
    columns: [id, name, amount]

checks:
  - type: not_null
    columns: [id, name]
  - type: row_count
    min: 1

sink:
  type: file
  path: {temp_dir / "output.parquet"}
  format: parquet
"""
    yaml_path = temp_dir / "pipeline.yml"
    yaml_path.write_text(yaml_content)
    return yaml_path


@pytest.fixture
def pipeline_config():
    """Create a sample PipelineConfig object."""
    from quicketl.config.checks import NotNullCheck, RowCountCheck
    from quicketl.config.models import (
        FileSink,
        FileSource,
        PipelineConfig,
    )
    from quicketl.config.transforms import FilterTransform, SelectTransform

    return PipelineConfig(
        name="test_pipeline",
        description="Test pipeline",
        engine="duckdb",
        source=FileSource(path="data.parquet", format="parquet"),
        transforms=[
            FilterTransform(predicate="amount > 100"),
            SelectTransform(columns=["id", "name", "amount"]),
        ],
        checks=[
            NotNullCheck(columns=["id", "name"]),
            RowCountCheck(min=1),
        ],
        sink=FileSink(path="output.parquet", format="parquet"),
    )
