"""Parity tests for transforms across backends.

These tests verify that transform operations produce identical results
when executed on different backends (duckdb, polars).
"""

from __future__ import annotations

import pandas as pd
import pytest

from quicketl.engines import ETLXEngine


class TestFilterParity:
    """Verify filter operations produce identical results across backends."""

    @pytest.mark.parity
    def test_filter_numeric_comparison(self, parity_engine, parity_sample_data):
        """Test that numeric filtering is consistent."""
        predicate = parity_engine._parse_predicate(parity_sample_data, "amount > 150")
        result = parity_sample_data.filter(predicate)
        df = parity_engine.to_pandas(result)

        assert len(df) == 3
        assert set(df["name"].tolist()) == {"Bob", "Diana", "Eve"}

    @pytest.mark.parity
    def test_filter_string_comparison(self, parity_engine, parity_sample_data):
        """Test that string filtering is consistent."""
        predicate = parity_engine._parse_predicate(parity_sample_data, "region = 'North'")
        result = parity_sample_data.filter(predicate)
        df = parity_engine.to_pandas(result)

        assert len(df) == 2
        assert set(df["name"].tolist()) == {"Alice", "Charlie"}

    @pytest.mark.parity
    def test_filter_boolean_column(self, parity_engine, parity_sample_data):
        """Test that boolean column filtering is consistent."""
        predicate = parity_engine._parse_predicate(parity_sample_data, "active")
        result = parity_sample_data.filter(predicate)
        df = parity_engine.to_pandas(result)

        assert len(df) == 4
        assert "Charlie" not in df["name"].tolist()

    @pytest.mark.parity
    def test_filter_in_operator(self, parity_engine, parity_sample_data):
        """Test that IN operator is consistent."""
        predicate = parity_engine._parse_predicate(
            parity_sample_data, "region IN ('North', 'East')"
        )
        result = parity_sample_data.filter(predicate)
        df = parity_engine.to_pandas(result)

        assert len(df) == 3
        assert set(df["region"].tolist()) == {"North", "East"}


class TestDeriveColumnParity:
    """Verify derive_column operations produce identical results."""

    @pytest.mark.parity
    def test_arithmetic_expression(self, parity_engine, parity_sample_data):
        """Test that arithmetic expressions are consistent."""
        expr = parity_engine._parse_expression(parity_sample_data, "amount * 2")
        result = parity_sample_data.mutate(double_amount=expr)
        df = parity_engine.to_pandas(result)

        assert df["double_amount"].iloc[0] == 200.0  # 100 * 2
        assert df["double_amount"].iloc[1] == 400.0  # 200 * 2

    @pytest.mark.parity
    def test_string_upper(self, parity_engine, parity_sample_data):
        """Test that UPPER function is consistent."""
        expr = parity_engine._parse_expression(parity_sample_data, "UPPER(name)")
        result = parity_sample_data.mutate(upper_name=expr)
        df = parity_engine.to_pandas(result)

        assert df["upper_name"].iloc[0] == "ALICE"
        assert df["upper_name"].iloc[1] == "BOB"

    @pytest.mark.parity
    def test_string_lower(self, parity_engine, parity_sample_data):
        """Test that LOWER function is consistent."""
        expr = parity_engine._parse_expression(parity_sample_data, "LOWER(name)")
        result = parity_sample_data.mutate(lower_name=expr)
        df = parity_engine.to_pandas(result)

        assert df["lower_name"].iloc[0] == "alice"
        assert df["lower_name"].iloc[1] == "bob"


class TestSelectColumnsParity:
    """Verify select operations produce identical results."""

    @pytest.mark.parity
    def test_select_subset(self, parity_engine, parity_sample_data):
        """Test that selecting columns is consistent."""
        result = parity_sample_data.select("id", "name")
        df = parity_engine.to_pandas(result)

        assert list(df.columns) == ["id", "name"]
        assert len(df) == 5

    @pytest.mark.parity
    def test_select_with_rename(self, parity_engine, parity_sample_data):
        """Test that renaming columns is consistent."""
        result = parity_sample_data.rename(value="amount")
        df = parity_engine.to_pandas(result)

        assert "value" in df.columns
        assert "amount" not in df.columns


class TestSortParity:
    """Verify sort operations produce identical results."""

    @pytest.mark.parity
    def test_sort_ascending(self, parity_engine, parity_sample_data):
        """Test ascending sort is consistent."""
        result = parity_sample_data.order_by("amount")
        df = parity_engine.to_pandas(result)

        assert df["amount"].tolist() == [100.0, 150.0, 200.0, 250.0, 300.0]

    @pytest.mark.parity
    def test_sort_descending(self, parity_engine, parity_sample_data):
        """Test descending sort is consistent."""
        import ibis

        result = parity_sample_data.order_by(ibis.desc("amount"))
        df = parity_engine.to_pandas(result)

        assert df["amount"].tolist() == [300.0, 250.0, 200.0, 150.0, 100.0]


class TestAggregateParity:
    """Verify aggregation operations produce identical results."""

    @pytest.mark.parity
    def test_group_by_count(self, parity_engine, parity_sample_data):
        """Test group by with count is consistent."""
        result = parity_sample_data.group_by("region").agg(
            count=parity_sample_data.id.count()
        )
        df = parity_engine.to_pandas(result).sort_values("region").reset_index(drop=True)

        assert len(df) == 3  # North, South, East
        north_count = df[df["region"] == "North"]["count"].iloc[0]
        assert north_count == 2

    @pytest.mark.parity
    def test_group_by_sum(self, parity_engine, parity_sample_data):
        """Test group by with sum is consistent."""
        result = parity_sample_data.group_by("region").agg(
            total=parity_sample_data.amount.sum()
        )
        df = parity_engine.to_pandas(result).sort_values("region").reset_index(drop=True)

        north_total = df[df["region"] == "North"]["total"].iloc[0]
        assert north_total == 250.0  # 100 + 150

    @pytest.mark.parity
    def test_group_by_avg(self, parity_engine, parity_sample_data):
        """Test group by with average is consistent."""
        result = parity_sample_data.group_by("region").agg(
            avg_amount=parity_sample_data.amount.mean()
        )
        df = parity_engine.to_pandas(result).sort_values("region").reset_index(drop=True)

        north_avg = df[df["region"] == "North"]["avg_amount"].iloc[0]
        assert north_avg == 125.0  # (100 + 150) / 2


class TestLimitParity:
    """Verify limit operations produce identical results."""

    @pytest.mark.parity
    def test_limit(self, parity_engine, parity_sample_data):
        """Test limit is consistent."""
        # First sort to ensure deterministic results
        sorted_data = parity_sample_data.order_by("id")
        result = sorted_data.limit(3)
        df = parity_engine.to_pandas(result)

        assert len(df) == 3
        assert df["id"].tolist() == [1, 2, 3]


class TestDistinctParity:
    """Verify distinct operations produce identical results."""

    @pytest.mark.parity
    def test_distinct(self, parity_engine, parity_sample_data):
        """Test distinct is consistent."""
        result = parity_sample_data.select("region").distinct()
        df = parity_engine.to_pandas(result)

        assert len(df) == 3
        assert set(df["region"].tolist()) == {"North", "South", "East"}


class TestNullHandlingParity:
    """Verify null handling is consistent across backends."""

    @pytest.mark.parity
    def test_coalesce_with_nulls(self, parity_engine):
        """Test COALESCE handles nulls consistently."""
        data = {
            "id": [1, 2, 3],
            "val": ["A", None, "C"],
        }
        df = pd.DataFrame(data)
        table = parity_engine.connection.create_table("null_test", df, overwrite=True)

        expr = parity_engine._parse_expression(table, "COALESCE(val, 'default')")
        result = table.mutate(safe_val=expr)
        df_result = parity_engine.to_pandas(result)

        assert df_result["safe_val"].iloc[1] == "default"
        assert df_result["safe_val"].iloc[0] == "A"

    @pytest.mark.parity
    def test_is_null_predicate(self, parity_engine):
        """Test IS NULL predicate is consistent."""
        data = {
            "id": [1, 2, 3],
            "val": ["A", None, "C"],
        }
        df = pd.DataFrame(data)
        table = parity_engine.connection.create_table("null_test2", df, overwrite=True)

        predicate = parity_engine._parse_predicate(table, "val IS NULL")
        result = table.filter(predicate)
        df_result = parity_engine.to_pandas(result)

        assert len(df_result) == 1
        assert df_result["id"].iloc[0] == 2


class TestMultiBackendComparison:
    """Tests that explicitly compare results between backends."""

    @pytest.mark.parity
    def test_transform_chain_produces_same_result(self):
        """Test that a chain of transforms produces identical results."""
        # Create engines for both backends
        duckdb_engine = ETLXEngine(backend="duckdb")
        polars_engine = ETLXEngine(backend="polars")

        # Create identical data
        data = {
            "id": [1, 2, 3, 4, 5],
            "category": ["A", "B", "A", "B", "A"],
            "value": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(data)

        duck_table = duckdb_engine.connection.create_table("chain_test", df, overwrite=True)
        polars_table = polars_engine.connection.create_table("chain_test", df, overwrite=True)

        # Apply chain of transforms
        def apply_transforms(engine, table):
            # Filter
            pred = engine._parse_predicate(table, "value > 15")
            filtered = table.filter(pred)

            # Derive column
            expr = engine._parse_expression(filtered, "value * 2")
            derived = filtered.mutate(doubled=expr)

            # Select
            selected = derived.select("category", "value", "doubled")

            # Sort
            sorted_result = selected.order_by("value")

            return sorted_result

        duck_result = apply_transforms(duckdb_engine, duck_table)
        polars_result = apply_transforms(polars_engine, polars_table)

        # Convert to pandas and compare
        duck_df = duckdb_engine.to_pandas(duck_result).reset_index(drop=True)
        polars_df = polars_engine.to_pandas(polars_result).reset_index(drop=True)

        pd.testing.assert_frame_equal(duck_df, polars_df)

    @pytest.mark.parity
    def test_aggregation_produces_same_result(self):
        """Test that aggregation produces identical results across backends."""
        duckdb_engine = ETLXEngine(backend="duckdb")
        polars_engine = ETLXEngine(backend="polars")

        data = {
            "region": ["N", "S", "N", "S", "N"],
            "sales": [100, 200, 150, 250, 175],
        }
        df = pd.DataFrame(data)

        duck_table = duckdb_engine.connection.create_table("agg_test", df, overwrite=True)
        polars_table = polars_engine.connection.create_table("agg_test", df, overwrite=True)

        # Aggregate
        duck_agg = duck_table.group_by("region").agg(
            total=duck_table.sales.sum(),
            avg=duck_table.sales.mean(),
            cnt=duck_table.sales.count(),
        )
        polars_agg = polars_table.group_by("region").agg(
            total=polars_table.sales.sum(),
            avg=polars_table.sales.mean(),
            cnt=polars_table.sales.count(),
        )

        duck_df = duckdb_engine.to_pandas(duck_agg).sort_values("region").reset_index(drop=True)
        polars_df = polars_engine.to_pandas(polars_agg).sort_values("region").reset_index(drop=True)

        pd.testing.assert_frame_equal(duck_df, polars_df)
