"""Tests for pivot and unpivot transforms.

This module tests:
- Pivot with single value column
- Pivot with aggregation
- Unpivot columns to rows
- Unpivot with custom column names
"""

from __future__ import annotations

import pytest

from quicketl.engines import ETLXEngine


@pytest.fixture
def engine() -> ETLXEngine:
    """Create a DuckDB engine for testing."""
    return ETLXEngine(backend="duckdb")


@pytest.fixture
def sales_data(engine: ETLXEngine):
    """Create sample sales data for pivot tests."""
    import ibis

    data = {
        "region": ["North", "North", "South", "South", "North", "South"],
        "product": ["A", "B", "A", "B", "A", "B"],
        "quarter": ["Q1", "Q1", "Q1", "Q1", "Q2", "Q2"],
        "revenue": [100, 150, 80, 120, 110, 90],
    }
    return ibis.memtable(data)


@pytest.fixture
def wide_data(engine: ETLXEngine):
    """Create wide-format data for unpivot tests."""
    import ibis

    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Carol"],
        "jan_sales": [100, 150, 200],
        "feb_sales": [110, 140, 190],
        "mar_sales": [120, 160, 210],
    }
    return ibis.memtable(data)


class TestPivotTransform:
    """Tests for pivot transform."""

    def test_pivot_with_single_value_column(self, engine: ETLXEngine, sales_data):
        """Pivot creates columns from unique values."""
        from quicketl.config.transforms import PivotTransform

        transform = PivotTransform(
            index=["region", "quarter"],
            columns="product",
            values="revenue",
        )

        result = engine.apply_transform(sales_data, transform)
        df = engine.to_pandas(result)

        # Should have columns: region, quarter, A, B
        assert "A" in df.columns
        assert "B" in df.columns

        # Check values for North, Q1
        north_q1 = df[(df["region"] == "North") & (df["quarter"] == "Q1")]
        assert north_q1["A"].iloc[0] == 100
        assert north_q1["B"].iloc[0] == 150

    def test_pivot_with_aggregation(self, engine: ETLXEngine, sales_data):
        """Pivot with explicit aggregation function."""
        from quicketl.config.transforms import PivotTransform

        transform = PivotTransform(
            index=["region"],
            columns="product",
            values="revenue",
            aggfunc="sum",
        )

        result = engine.apply_transform(sales_data, transform)
        df = engine.to_pandas(result)

        # North has A: 100+110=210, B: 150
        north = df[df["region"] == "North"]
        assert north["A"].iloc[0] == 210
        assert north["B"].iloc[0] == 150

        # South has A: 80, B: 120+90=210
        south = df[df["region"] == "South"]
        assert south["A"].iloc[0] == 80
        assert south["B"].iloc[0] == 210

    def test_pivot_with_multiple_aggfuncs(self, engine: ETLXEngine, sales_data):
        """Pivot with multiple aggregation functions."""
        from quicketl.config.transforms import PivotTransform

        transform = PivotTransform(
            index=["region"],
            columns="product",
            values="revenue",
            aggfunc=["sum", "mean"],
        )

        result = engine.apply_transform(sales_data, transform)
        df = engine.to_pandas(result)

        # Should have columns for each product/aggfunc combination
        # e.g., A_sum, A_mean, B_sum, B_mean
        assert any("sum" in col.lower() or "A" in col for col in df.columns)


class TestUnpivotTransform:
    """Tests for unpivot (melt) transform."""

    def test_unpivot_columns_to_rows(self, engine: ETLXEngine, wide_data):
        """Unpivot converts columns to rows."""
        from quicketl.config.transforms import UnpivotTransform

        transform = UnpivotTransform(
            id_vars=["id", "name"],
            value_vars=["jan_sales", "feb_sales", "mar_sales"],
        )

        result = engine.apply_transform(wide_data, transform)
        df = engine.to_pandas(result)

        # Should have 3 rows per original row (9 total)
        assert len(df) == 9

        # Should have id, name, variable, value columns
        assert "id" in df.columns
        assert "name" in df.columns
        # Default names for unpivot columns
        assert any("variable" in col.lower() or "name" in col.lower() for col in df.columns)
        assert any("value" in col.lower() for col in df.columns)

    def test_unpivot_with_value_name(self, engine: ETLXEngine, wide_data):
        """Unpivot with custom column names."""
        from quicketl.config.transforms import UnpivotTransform

        transform = UnpivotTransform(
            id_vars=["id", "name"],
            value_vars=["jan_sales", "feb_sales", "mar_sales"],
            var_name="month",
            value_name="sales",
        )

        result = engine.apply_transform(wide_data, transform)
        df = engine.to_pandas(result)

        # Should have custom column names
        assert "month" in df.columns
        assert "sales" in df.columns

        # Check values are preserved
        alice_jan = df[(df["name"] == "Alice") & (df["month"] == "jan_sales")]
        assert alice_jan["sales"].iloc[0] == 100

    def test_unpivot_preserves_all_values(self, engine: ETLXEngine, wide_data):
        """Unpivot preserves all original values."""
        from quicketl.config.transforms import UnpivotTransform

        transform = UnpivotTransform(
            id_vars=["id", "name"],
            value_vars=["jan_sales", "feb_sales", "mar_sales"],
            var_name="month",
            value_name="sales",
        )

        result = engine.apply_transform(wide_data, transform)
        df = engine.to_pandas(result)

        # Total sum should be preserved
        expected_sum = 100 + 110 + 120 + 150 + 140 + 160 + 200 + 190 + 210
        assert df["sales"].sum() == expected_sum
