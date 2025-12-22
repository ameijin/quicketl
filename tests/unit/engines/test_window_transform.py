"""Tests for window function transforms.

This module tests:
- Row number, rank, dense_rank over partitions
- Lag and lead with offsets
- Sum, avg, min, max over windows
- Window frame specifications (partition_by, order_by)
"""

from __future__ import annotations

import pandas as pd
import pytest

from quicketl.engines import ETLXEngine


@pytest.fixture
def engine() -> ETLXEngine:
    """Create a DuckDB engine for testing."""
    return ETLXEngine(backend="duckdb")


@pytest.fixture
def sample_orders(engine: ETLXEngine):
    """Create sample orders data for window function tests."""
    import ibis

    data = {
        "order_id": [1, 2, 3, 4, 5, 6],
        "customer_id": ["A", "A", "A", "B", "B", "B"],
        "order_date": [
            "2024-01-01",
            "2024-01-15",
            "2024-02-01",
            "2024-01-10",
            "2024-01-20",
            "2024-02-05",
        ],
        "amount": [100.0, 150.0, 200.0, 75.0, 125.0, 175.0],
    }
    return ibis.memtable(data)


class TestWindowTransform:
    """Tests for window function transforms."""

    def test_row_number_over_partition(self, engine: ETLXEngine, sample_orders):
        """Row number assigns sequential numbers within partition."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "row_num",
                    "func": "row_number",
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                }
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        # Customer A should have row numbers 1, 2, 3
        customer_a = df[df["customer_id"] == "A"].sort_values("order_date")
        assert list(customer_a["row_num"]) == [1, 2, 3]

        # Customer B should have row numbers 1, 2, 3
        customer_b = df[df["customer_id"] == "B"].sort_values("order_date")
        assert list(customer_b["row_num"]) == [1, 2, 3]

    def test_rank_over_partition(self, engine: ETLXEngine, sample_orders):
        """Rank with ties assigns same rank, skips next."""
        # Add duplicate amounts to test rank behavior
        import ibis

        from quicketl.config.transforms import WindowTransform

        data = {
            "id": [1, 2, 3, 4],
            "category": ["X", "X", "X", "X"],
            "score": [100, 100, 90, 80],  # Tie at 100
        }
        table = ibis.memtable(data)

        transform = WindowTransform(
            columns=[
                {
                    "name": "score_rank",
                    "func": "rank",
                    "partition_by": ["category"],
                    "order_by": [{"column": "score", "descending": True}],
                }
            ]
        )

        result = engine.apply_transform(table, transform)
        df = engine.to_pandas(result).sort_values("score", ascending=False)

        # Both 100s get rank 1, 90 gets rank 3 (skips 2), 80 gets rank 4
        assert list(df["score_rank"]) == [1, 1, 3, 4]

    def test_dense_rank_over_partition(self, engine: ETLXEngine):
        """Dense rank with ties assigns same rank, doesn't skip."""
        import ibis

        from quicketl.config.transforms import WindowTransform

        data = {
            "id": [1, 2, 3, 4],
            "category": ["X", "X", "X", "X"],
            "score": [100, 100, 90, 80],
        }
        table = ibis.memtable(data)

        transform = WindowTransform(
            columns=[
                {
                    "name": "dense_rank",
                    "func": "dense_rank",
                    "partition_by": ["category"],
                    "order_by": [{"column": "score", "descending": True}],
                }
            ]
        )

        result = engine.apply_transform(table, transform)
        df = engine.to_pandas(result).sort_values("score", ascending=False)

        # Both 100s get rank 1, 90 gets rank 2 (no skip), 80 gets rank 3
        assert list(df["dense_rank"]) == [1, 1, 2, 3]

    def test_lag_with_offset(self, engine: ETLXEngine, sample_orders):
        """Lag returns value from previous row."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "prev_amount",
                    "func": "lag",
                    "column": "amount",
                    "offset": 1,
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                }
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        customer_a = df[df["customer_id"] == "A"].sort_values("order_date")
        # First row has no previous, should be null
        assert customer_a.iloc[0]["prev_amount"] is None or pd.isna(
            customer_a.iloc[0]["prev_amount"]
        )
        # Second row should have first row's amount
        assert customer_a.iloc[1]["prev_amount"] == 100.0
        # Third row should have second row's amount
        assert customer_a.iloc[2]["prev_amount"] == 150.0

    def test_lead_with_offset(self, engine: ETLXEngine, sample_orders):
        """Lead returns value from next row."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "next_amount",
                    "func": "lead",
                    "column": "amount",
                    "offset": 1,
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                }
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        customer_a = df[df["customer_id"] == "A"].sort_values("order_date")
        # First row should have second row's amount
        assert customer_a.iloc[0]["next_amount"] == 150.0
        # Second row should have third row's amount
        assert customer_a.iloc[1]["next_amount"] == 200.0
        # Third row has no next, should be null
        assert customer_a.iloc[2]["next_amount"] is None or pd.isna(
            customer_a.iloc[2]["next_amount"]
        )

    def test_sum_over_window(self, engine: ETLXEngine, sample_orders):
        """Running sum over window."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "running_total",
                    "func": "sum",
                    "column": "amount",
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                }
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        customer_a = df[df["customer_id"] == "A"].sort_values("order_date")
        # Running totals: 100, 250 (100+150), 450 (100+150+200)
        assert list(customer_a["running_total"]) == [100.0, 250.0, 450.0]

    def test_window_with_partition_and_order(self, engine: ETLXEngine, sample_orders):
        """Window with both partition and order specified."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "row_num",
                    "func": "row_number",
                    "partition_by": ["customer_id"],
                    "order_by": [{"column": "amount", "descending": True}],
                }
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        # Customer A ordered by amount desc: 200, 150, 100 -> row nums 1, 2, 3
        customer_a = df[df["customer_id"] == "A"].sort_values(
            "amount", ascending=False
        )
        assert list(customer_a["row_num"]) == [1, 2, 3]

    def test_multiple_window_columns(self, engine: ETLXEngine, sample_orders):
        """Multiple window columns in single transform."""
        from quicketl.config.transforms import WindowTransform

        transform = WindowTransform(
            columns=[
                {
                    "name": "row_num",
                    "func": "row_number",
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                },
                {
                    "name": "prev_amount",
                    "func": "lag",
                    "column": "amount",
                    "offset": 1,
                    "partition_by": ["customer_id"],
                    "order_by": ["order_date"],
                },
            ]
        )

        result = engine.apply_transform(sample_orders, transform)
        df = engine.to_pandas(result)

        # Should have both new columns
        assert "row_num" in df.columns
        assert "prev_amount" in df.columns


