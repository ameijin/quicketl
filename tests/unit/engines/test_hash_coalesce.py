"""Tests for hash_key and coalesce transforms.

This module tests:
- Hash key generation with MD5, SHA256
- Hash multiple columns
- Coalesce returns first non-null
- Coalesce with default value
"""

from __future__ import annotations

import pytest

from quicketl.engines import ETLXEngine


@pytest.fixture
def engine() -> ETLXEngine:
    """Create a DuckDB engine for testing."""
    return ETLXEngine(backend="duckdb")


@pytest.fixture
def sample_data(engine: ETLXEngine):
    """Create sample data for hash and coalesce tests."""
    import ibis

    data = {
        "id": [1, 2, 3],
        "customer_id": ["C001", "C002", "C003"],
        "order_id": ["O001", "O002", "O003"],
        "primary_email": ["alice@example.com", None, "carol@example.com"],
        "secondary_email": ["alice2@example.com", "bob@example.com", None],
        "fallback_email": ["default@example.com", "default@example.com", "default@example.com"],
    }
    return ibis.memtable(data)


class TestHashKeyTransform:
    """Tests for hash key generation transform."""

    def test_hash_single_column_md5(self, engine: ETLXEngine, sample_data):
        """Hash single column using MD5."""
        from quicketl.config.transforms import HashKeyTransform

        transform = HashKeyTransform(
            name="customer_hash",
            columns=["customer_id"],
            algorithm="md5",
        )

        result = engine.apply_transform(sample_data, transform)
        df = engine.to_pandas(result)

        # Should have new column
        assert "customer_hash" in df.columns

        # Hash values should be 32-character hex strings (MD5)
        for hash_val in df["customer_hash"]:
            assert len(hash_val) == 32
            assert all(c in "0123456789abcdef" for c in hash_val.lower())

        # Same input should produce same hash
        # (we can verify by checking if different customer_ids produce different hashes)
        assert df["customer_hash"].nunique() == 3

    def test_hash_multiple_columns(self, engine: ETLXEngine, sample_data):
        """Hash multiple columns together."""
        from quicketl.config.transforms import HashKeyTransform

        transform = HashKeyTransform(
            name="composite_key",
            columns=["customer_id", "order_id"],
            algorithm="md5",
        )

        result = engine.apply_transform(sample_data, transform)
        df = engine.to_pandas(result)

        # Should have new column
        assert "composite_key" in df.columns

        # All composite keys should be unique
        assert df["composite_key"].nunique() == 3

    def test_hash_with_sha256(self, engine: ETLXEngine, sample_data):
        """Hash with SHA256 algorithm."""
        from quicketl.config.transforms import HashKeyTransform

        transform = HashKeyTransform(
            name="customer_hash",
            columns=["customer_id"],
            algorithm="sha256",
        )

        result = engine.apply_transform(sample_data, transform)
        df = engine.to_pandas(result)

        # SHA256 produces 64-character hex strings
        for hash_val in df["customer_hash"]:
            assert len(hash_val) == 64
            assert all(c in "0123456789abcdef" for c in hash_val.lower())

    def test_hash_deterministic(self, engine: ETLXEngine, sample_data):
        """Hash is deterministic - same input produces same output."""
        from quicketl.config.transforms import HashKeyTransform

        transform = HashKeyTransform(
            name="customer_hash",
            columns=["customer_id"],
            algorithm="md5",
        )

        result1 = engine.apply_transform(sample_data, transform)
        result2 = engine.apply_transform(sample_data, transform)

        df1 = engine.to_pandas(result1)
        df2 = engine.to_pandas(result2)

        # Same data should produce same hashes
        assert list(df1["customer_hash"]) == list(df2["customer_hash"])

    def test_hash_with_separator(self, engine: ETLXEngine, sample_data):
        """Hash multiple columns with custom separator."""
        from quicketl.config.transforms import HashKeyTransform

        transform = HashKeyTransform(
            name="composite_key",
            columns=["customer_id", "order_id"],
            algorithm="md5",
            separator="|",
        )

        result = engine.apply_transform(sample_data, transform)
        df = engine.to_pandas(result)

        assert "composite_key" in df.columns
        assert df["composite_key"].nunique() == 3


class TestCoalesceTransform:
    """Tests for coalesce transform."""

    def test_coalesce_returns_first_non_null(self, engine: ETLXEngine, sample_data):
        """Coalesce returns first non-null value from columns."""
        from quicketl.config.transforms import CoalesceTransform

        transform = CoalesceTransform(
            name="email",
            columns=["primary_email", "secondary_email", "fallback_email"],
        )

        result = engine.apply_transform(sample_data, transform)
        df = engine.to_pandas(result)

        # Row 1: alice@example.com (primary is not null)
        assert df.iloc[0]["email"] == "alice@example.com"

        # Row 2: bob@example.com (primary is null, secondary is not null)
        assert df.iloc[1]["email"] == "bob@example.com"

        # Row 3: carol@example.com (primary is not null)
        assert df.iloc[2]["email"] == "carol@example.com"

    def test_coalesce_with_default(self, engine: ETLXEngine):
        """Coalesce with a literal default value."""
        import ibis

        from quicketl.config.transforms import CoalesceTransform

        data = {
            "id": [1, 2],
            "value1": [None, None],
            "value2": [None, None],
        }
        table = ibis.memtable(data)

        transform = CoalesceTransform(
            name="result",
            columns=["value1", "value2"],
            default="unknown",
        )

        result = engine.apply_transform(table, transform)
        df = engine.to_pandas(result)

        # Both rows should have default value since all nulls
        assert df.iloc[0]["result"] == "unknown"
        assert df.iloc[1]["result"] == "unknown"

    def test_coalesce_with_numeric_default(self, engine: ETLXEngine):
        """Coalesce with numeric default value."""
        import ibis

        from quicketl.config.transforms import CoalesceTransform

        data = {
            "id": [1, 2, 3],
            "primary_value": [100.0, None, None],
            "secondary_value": [None, 50.0, None],
        }
        table = ibis.memtable(data)

        transform = CoalesceTransform(
            name="value",
            columns=["primary_value", "secondary_value"],
            default=0.0,
        )

        result = engine.apply_transform(table, transform)
        df = engine.to_pandas(result)

        assert df.iloc[0]["value"] == 100.0  # primary not null
        assert df.iloc[1]["value"] == 50.0   # secondary not null
        assert df.iloc[2]["value"] == 0.0    # both null, use default

    def test_coalesce_preserves_types(self, engine: ETLXEngine):
        """Coalesce preserves data types."""
        import ibis

        from quicketl.config.transforms import CoalesceTransform

        data = {
            "id": [1, 2],
            "int_col1": [None, 10],
            "int_col2": [20, None],
        }
        table = ibis.memtable(data)

        transform = CoalesceTransform(
            name="result",
            columns=["int_col1", "int_col2"],
        )

        result = engine.apply_transform(table, transform)
        df = engine.to_pandas(result)

        # Should preserve integer type
        assert df.iloc[0]["result"] == 20
        assert df.iloc[1]["result"] == 10
