"""Tests for join and union transforms."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


@pytest.fixture
def orders_data(temp_dir: Path) -> Path:
    """Create orders parquet file."""
    table = pa.table(
        {
            "order_id": [1, 2, 3, 4, 5],
            "customer_id": [101, 102, 101, 103, 102],
            "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        }
    )
    path = temp_dir / "orders.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture
def customers_data(temp_dir: Path) -> Path:
    """Create customers parquet file."""
    table = pa.table(
        {
            "customer_id": [101, 102, 103, 104],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "region": ["North", "South", "East", "West"],
        }
    )
    path = temp_dir / "customers.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture
def events_source1(temp_dir: Path) -> Path:
    """Create events source 1 parquet file."""
    table = pa.table(
        {
            "event_id": [1, 2, 3],
            "event_type": ["click", "view", "purchase"],
            "user_id": [101, 102, 101],
        }
    )
    path = temp_dir / "events1.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture
def events_source2(temp_dir: Path) -> Path:
    """Create events source 2 parquet file."""
    table = pa.table(
        {
            "event_id": [4, 5],
            "event_type": ["click", "view"],
            "user_id": [103, 104],
        }
    )
    path = temp_dir / "events2.parquet"
    pq.write_table(table, path)
    return path


class TestJoinTransform:
    """Tests for join transform."""

    def test_inner_join(self, engine, orders_data: Path, customers_data: Path):
        """Test inner join between orders and customers."""
        # Load both tables
        orders = engine.read_file(str(orders_data), "parquet")
        customers = engine.read_file(str(customers_data), "parquet")

        # Perform join using engine.join directly
        result = engine.join(orders, customers, on=["customer_id"], how="inner")

        # Verify result
        df = result.execute()
        assert len(df) == 5  # All orders have matching customers
        assert "name" in df.columns
        assert "region" in df.columns

    def test_left_join(self, engine, orders_data: Path, customers_data: Path):
        """Test left join preserves all left table rows."""
        orders = engine.read_file(str(orders_data), "parquet")
        customers = engine.read_file(str(customers_data), "parquet")

        result = engine.join(orders, customers, on=["customer_id"], how="left")

        df = result.execute()
        assert len(df) == 5  # All orders preserved

    def test_join_transform_with_context(self, engine, orders_data: Path, customers_data: Path):
        """Test join transform using apply_transform with context."""
        from quicketl.config.transforms import JoinTransform

        orders = engine.read_file(str(orders_data), "parquet")
        customers = engine.read_file(str(customers_data), "parquet")

        # Create context with named tables
        context = {"customers": customers}

        # Apply join transform
        transform = JoinTransform(right="customers", on=["customer_id"], how="left")
        result = engine.apply_transform(orders, transform, context)

        df = result.execute()
        assert len(df) == 5
        assert "name" in df.columns

    def test_join_transform_missing_context(self, engine, orders_data: Path):
        """Test join transform raises error when context table is missing."""
        from quicketl.config.transforms import JoinTransform

        orders = engine.read_file(str(orders_data), "parquet")

        transform = JoinTransform(right="customers", on=["customer_id"], how="inner")

        with pytest.raises(ValueError, match="Join requires table 'customers' in context"):
            engine.apply_transform(orders, transform, context={})


class TestUnionTransform:
    """Tests for union transform."""

    def test_union_tables(self, engine, events_source1: Path, events_source2: Path):
        """Test union of two tables."""
        events1 = engine.read_file(str(events_source1), "parquet")
        events2 = engine.read_file(str(events_source2), "parquet")

        result = engine.union([events1, events2])

        count = result.count().execute()
        assert count == 5  # 3 + 2 rows

    def test_union_transform_with_context(self, engine, events_source1: Path, events_source2: Path):
        """Test union transform using apply_transform with context."""
        from quicketl.config.transforms import UnionTransform

        events1 = engine.read_file(str(events_source1), "parquet")
        events2 = engine.read_file(str(events_source2), "parquet")

        # Create context with named tables
        context = {"events2": events2}

        # Apply union transform (current table + events2 from context)
        transform = UnionTransform(sources=["events2"])
        result = engine.apply_transform(events1, transform, context)

        count = result.count().execute()
        assert count == 5  # 3 + 2 rows

    def test_union_transform_missing_context(self, engine, events_source1: Path):
        """Test union transform raises error when context table is missing."""
        from quicketl.config.transforms import UnionTransform

        events1 = engine.read_file(str(events_source1), "parquet")

        transform = UnionTransform(sources=["events2", "events3"])

        with pytest.raises(ValueError, match="Union requires table 'events2' in context"):
            engine.apply_transform(events1, transform, context={})


class TestMultiSourcePipeline:
    """Tests for multi-source pipeline configuration."""

    def test_join_pipeline_from_yaml(self, temp_dir: Path, orders_data: Path, customers_data: Path):
        """Test running a join pipeline from YAML config."""
        from quicketl.pipeline import Pipeline

        # Create pipeline YAML
        # Note: "on" must be quoted in YAML because it's a reserved word (boolean True)
        yaml_content = f"""
name: orders_with_customers
engine: duckdb

sources:
  orders:
    type: file
    path: {orders_data}
    format: parquet
  customers:
    type: file
    path: {customers_data}
    format: parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]
    how: left
  - op: select
    columns: [order_id, customer_id, amount, name, region]

sink:
  type: file
  path: {temp_dir}/output.parquet
  format: parquet
"""
        yaml_path = temp_dir / "join_pipeline.yml"
        yaml_path.write_text(yaml_content)

        # Run pipeline
        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded, f"Pipeline failed: {result.error}"
        assert result.rows_processed == 5
        assert result.rows_written == 5

        # Verify output
        output = pq.read_table(temp_dir / "output.parquet")
        assert "name" in output.column_names
        assert "region" in output.column_names

    def test_union_pipeline_from_yaml(
        self, temp_dir: Path, events_source1: Path, events_source2: Path
    ):
        """Test running a union pipeline from YAML config."""
        from quicketl.pipeline import Pipeline

        yaml_content = f"""
name: all_events
engine: duckdb

sources:
  events1:
    type: file
    path: {events_source1}
    format: parquet
  events2:
    type: file
    path: {events_source2}
    format: parquet

transforms:
  - op: union
    sources: [events2]

sink:
  type: file
  path: {temp_dir}/all_events.parquet
  format: parquet
"""
        yaml_path = temp_dir / "union_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded, f"Pipeline failed: {result.error}"
        assert result.rows_processed == 5  # 3 + 2

    def test_multi_source_with_aggregation(
        self, temp_dir: Path, orders_data: Path, customers_data: Path
    ):
        """Test multi-source pipeline with join and aggregation."""
        from quicketl.pipeline import Pipeline

        # Note: "on" must be quoted in YAML because it's a reserved word
        yaml_content = f"""
name: revenue_by_region
engine: duckdb

sources:
  orders:
    type: file
    path: {orders_data}
    format: parquet
  customers:
    type: file
    path: {customers_data}
    format: parquet

transforms:
  - op: join
    right: customers
    "on": [customer_id]
    how: left
  - op: aggregate
    group_by: [region]
    aggs:
      total_revenue: sum(amount)
      order_count: count(*)

sink:
  type: file
  path: {temp_dir}/revenue.parquet
  format: parquet
"""
        yaml_path = temp_dir / "agg_pipeline.yml"
        yaml_path.write_text(yaml_content)

        pipeline = Pipeline.from_yaml(yaml_path)
        result = pipeline.run()

        assert result.succeeded, f"Pipeline failed: {result.error}"
        assert result.rows_processed == 3  # 3 regions

        # Verify aggregation
        output = pq.read_table(temp_dir / "revenue.parquet").to_pandas()
        assert "total_revenue" in output.columns
        assert "order_count" in output.columns
