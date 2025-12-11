"""Tests for transform operations.

Tests all 12 transform operations across backends for parity.
"""

from __future__ import annotations

import pytest


class TestSelectTransform:
    """Tests for select transform."""

    def test_select_columns(self, engine, sample_data):
        """Select specific columns."""
        result = engine.select(sample_data, ["id", "name"])

        assert list(result.columns) == ["id", "name"]
        assert result.count().execute() == 5

    def test_select_single_column(self, engine, sample_data):
        """Select a single column."""
        result = engine.select(sample_data, ["amount"])

        assert list(result.columns) == ["amount"]


class TestRenameTransform:
    """Tests for rename transform."""

    def test_rename_column(self, engine, sample_data):
        """Rename a column."""
        result = engine.rename(sample_data, {"name": "full_name"})

        assert "full_name" in result.columns
        assert "name" not in result.columns

    def test_rename_multiple_columns(self, engine, sample_data):
        """Rename multiple columns."""
        result = engine.rename(sample_data, {"name": "full_name", "amount": "total"})

        assert "full_name" in result.columns
        assert "total" in result.columns
        assert "name" not in result.columns
        assert "amount" not in result.columns


class TestFilterTransform:
    """Tests for filter transform."""

    def test_filter_greater_than(self, engine, sample_data):
        """Filter with greater than condition."""
        result = engine.filter(sample_data, "amount > 150")

        count = result.count().execute()
        assert count == 3  # 200, 300, 250

    def test_filter_equality(self, engine, sample_data):
        """Filter with equality condition."""
        result = engine.filter(sample_data, "region == 'North'")

        count = result.count().execute()
        assert count == 2

    def test_filter_boolean(self, engine, sample_data):
        """Filter on boolean column."""
        result = engine.filter(sample_data, "active == true")

        count = result.count().execute()
        assert count == 4


class TestDeriveColumnTransform:
    """Tests for derive_column transform."""

    def test_derive_arithmetic(self, engine, sample_data):
        """Add computed column with arithmetic."""
        result = engine.derive_column(sample_data, "doubled", "amount * 2")

        assert "doubled" in result.columns
        # Check first row
        df = result.limit(1).execute()
        assert df["doubled"].iloc[0] == 200.0  # 100 * 2

    def test_derive_with_existing_columns(self, engine, sample_data):
        """Derive column using multiple existing columns."""
        result = engine.derive_column(sample_data, "id_plus_amount", "id + amount")

        assert "id_plus_amount" in result.columns


class TestCastTransform:
    """Tests for cast transform."""

    def test_cast_to_string(self, engine, sample_data):
        """Cast integer to string."""
        result = engine.cast(sample_data, {"id": "string"})

        schema = engine.schema(result)
        assert "string" in schema["id"].lower() or "utf8" in schema["id"].lower()

    def test_cast_multiple_columns(self, engine, sample_data):
        """Cast multiple columns."""
        result = engine.cast(sample_data, {"id": "string", "amount": "int64"})

        schema = engine.schema(result)
        assert "int" in schema["amount"].lower()


class TestFillNullTransform:
    """Tests for fill_null transform."""

    def test_fill_null_string(self, engine, sample_data_with_nulls):
        """Fill null string values."""
        result = engine.fill_null(sample_data_with_nulls, {"name": "Unknown"})

        # Count nulls after fill
        null_count = result.filter(result["name"].isnull()).count().execute()
        assert null_count == 0

    def test_fill_null_numeric(self, engine, sample_data_with_nulls):
        """Fill null numeric values."""
        result = engine.fill_null(sample_data_with_nulls, {"amount": 0.0})

        null_count = result.filter(result["amount"].isnull()).count().execute()
        assert null_count == 0


class TestDedupTransform:
    """Tests for dedup transform."""

    def test_dedup_all_columns(self, engine, sample_data_with_duplicates):
        """Remove duplicates across all columns."""
        result = engine.dedup(sample_data_with_duplicates)

        count = result.count().execute()
        assert count == 3  # 3 unique rows

    def test_dedup_specific_columns(self, engine, sample_data_with_duplicates):
        """Remove duplicates based on specific columns."""
        result = engine.dedup(sample_data_with_duplicates, columns=["id"])

        count = result.count().execute()
        assert count == 3  # 3 unique ids


class TestSortTransform:
    """Tests for sort transform."""

    def test_sort_ascending(self, engine, sample_data):
        """Sort ascending."""
        result = engine.sort(sample_data, by=["amount"])

        df = result.execute()
        amounts = df["amount"].tolist()
        assert amounts == sorted(amounts)

    def test_sort_descending(self, engine, sample_data):
        """Sort descending."""
        result = engine.sort(sample_data, by=["amount"], descending=True)

        df = result.execute()
        amounts = df["amount"].tolist()
        assert amounts == sorted(amounts, reverse=True)


class TestAggregateTransform:
    """Tests for aggregate transform."""

    def test_aggregate_sum(self, engine, sample_data):
        """Aggregate with sum."""
        result = engine.aggregate(
            sample_data,
            group_by=["region"],
            aggs={"total_amount": "sum(amount)"},
        )

        count = result.count().execute()
        assert count == 3  # North, South, East

    def test_aggregate_multiple_aggs(self, engine, sample_data):
        """Aggregate with multiple aggregations."""
        result = engine.aggregate(
            sample_data,
            group_by=["region"],
            aggs={
                "total_amount": "sum(amount)",
                "row_count": "count(*)",
            },
        )

        assert "total_amount" in result.columns
        assert "row_count" in result.columns


class TestUnionTransform:
    """Tests for union transform."""

    def test_union_two_tables(self, engine, sample_data):
        """Union two tables."""
        result = engine.union([sample_data, sample_data])

        count = result.count().execute()
        assert count == 10  # 5 + 5


class TestLimitTransform:
    """Tests for limit transform."""

    def test_limit(self, engine, sample_data):
        """Limit rows."""
        result = engine.limit(sample_data, 3)

        count = result.count().execute()
        assert count == 3

    def test_limit_greater_than_rows(self, engine, sample_data):
        """Limit greater than available rows."""
        result = engine.limit(sample_data, 100)

        count = result.count().execute()
        assert count == 5  # Only 5 rows available


class TestTransformParity:
    """Test that transforms produce identical results across backends."""

    @pytest.mark.parity
    def test_filter_parity(self, engine_name, sample_data):
        """Verify filter produces same results across backends."""
        from etlx.engines import ETLXEngine

        engine = ETLXEngine(backend=engine_name)
        result = engine.filter(sample_data, "amount > 150")

        count = result.count().execute()
        assert count == 3

        # Verify total amount
        total = result.select(["amount"]).execute()["amount"].sum()
        assert total == 750.0  # 200 + 300 + 250

    @pytest.mark.parity
    def test_aggregate_parity(self, engine_name, sample_data):
        """Verify aggregation produces same results across backends."""
        from etlx.engines import ETLXEngine

        engine = ETLXEngine(backend=engine_name)
        result = engine.aggregate(
            sample_data,
            group_by=["region"],
            aggs={"total": "sum(amount)"},
        )

        df = result.execute()
        totals = dict(zip(df["region"], df["total"]))

        assert totals["North"] == 250.0  # 100 + 150
        assert totals["South"] == 450.0  # 200 + 250
        assert totals["East"] == 300.0
