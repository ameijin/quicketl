"""Parity test fixtures and configuration.

Parity tests verify that different backends produce identical results.
They are parametrized across all supported backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

if TYPE_CHECKING:
    import ibis.expr.types as ir


# Backends to test for parity
PARITY_BACKENDS = ["duckdb", "polars"]


@pytest.fixture(params=PARITY_BACKENDS)
def parity_engine_name(request: pytest.FixtureRequest) -> str:
    """Parametrize parity tests across supported backends."""
    return request.param


@pytest.fixture
def parity_engine(parity_engine_name: str):
    """Create an ETLXEngine for parity testing."""
    from quicketl.engines import ETLXEngine

    return ETLXEngine(backend=parity_engine_name)


@pytest.fixture
def parity_sample_data(parity_engine) -> ir.Table:
    """Create identical sample data for parity testing across backends."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        "region": ["North", "South", "North", "East", "South"],
        "active": [True, True, False, True, True],
    }

    df = pd.DataFrame(data)
    return parity_engine.connection.create_table("parity_data", df, overwrite=True)


def assert_tables_equal(table1, table2, engine1, engine2):
    """Assert two tables from different backends are equal.

    Converts both to pandas DataFrames and compares.
    """
    df1 = engine1.to_pandas(table1).sort_values(by=list(table1.columns)).reset_index(drop=True)
    df2 = engine2.to_pandas(table2).sort_values(by=list(table2.columns)).reset_index(drop=True)

    pd.testing.assert_frame_equal(df1, df2)
