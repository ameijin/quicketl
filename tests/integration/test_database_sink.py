"""Tests for database sink functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class TestDatabaseSink:
    """Tests for the database sink feature."""

    def test_write_database_sqlite_replace(self, engine, sample_data, temp_dir: Path):
        """Test writing to SQLite database with replace mode."""
        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="replace",
        )

        assert result.rows_written == 5
        assert result.table == "test_table"
        assert result.duration_ms >= 0

    def test_write_database_sqlite_append(self, engine, sample_data, temp_dir: Path):
        """Test writing to SQLite database with append mode."""
        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        # First write
        engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="replace",
        )

        # Append more data
        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="append",
        )

        assert result.rows_written == 5
        assert result.table == "test_table"

    def test_write_database_sqlite_truncate(self, engine, sample_data, temp_dir: Path):
        """Test writing to SQLite database with truncate mode."""
        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        # First write with more rows
        engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="replace",
        )

        # Truncate and insert new data
        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="truncate",
        )

        assert result.rows_written == 5
        assert result.table == "test_table"

    def test_write_sink_database_config(self, engine, sample_data, temp_dir: Path):
        """Test write_sink with DatabaseSink configuration."""
        from quicketl.config.models import DatabaseSink

        db_path = temp_dir / "test.db"
        sink_config = DatabaseSink(
            connection=f"sqlite:///{db_path}",
            table="output_table",
            mode="replace",
        )

        result = engine.write_sink(sample_data, sink_config)

        assert result.rows_written == 5
        assert result.table == "output_table"


    def test_write_database_sqlite_upsert(self, engine, sample_data, temp_dir: Path):
        """Test writing to SQLite database with upsert mode."""
        import ibis

        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        # Initial write
        engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="replace",
        )

        # Verify initial state
        con = ibis.connect(connection)
        initial_count = con.table("test_table").count().execute()
        assert initial_count == 5

        # Upsert with overlapping data (same IDs) — should replace matching rows
        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="test_table",
            mode="upsert",
            upsert_keys=["id"],
        )

        assert result.rows_written == 5

        # After upsert with same keys, count should still be 5 (not 10)
        final_count = con.table("test_table").count().execute()
        assert final_count == 5

    def test_write_database_upsert_requires_keys(self, engine, sample_data, temp_dir: Path):
        """Test that upsert mode requires upsert_keys."""
        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        with pytest.raises(ValueError, match="upsert_keys are required"):
            engine.write_database(
                sample_data,
                connection=connection,
                target_table="test_table",
                mode="upsert",
            )

    def test_write_database_upsert_new_table(self, engine, sample_data, temp_dir: Path):
        """Test upsert creates the table if it doesn't exist."""
        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="new_table",
            mode="upsert",
            upsert_keys=["id"],
        )

        assert result.rows_written == 5
        assert result.table == "new_table"

    def test_write_sink_database_upsert_config(self, engine, sample_data, temp_dir: Path):
        """Test write_sink with DatabaseSink upsert configuration."""
        from quicketl.config.models import DatabaseSink

        db_path = temp_dir / "test.db"
        sink_config = DatabaseSink(
            connection=f"sqlite:///{db_path}",
            table="output_table",
            mode="upsert",
            upsert_keys=["id"],
        )

        result = engine.write_sink(sample_data, sink_config)

        assert result.rows_written == 5


class TestDatabaseSinkIntegration:
    """Integration tests for database sink (require external databases)."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires PostgreSQL - run manually")
    def test_write_database_postgres(self, engine, sample_data):
        """Test writing to PostgreSQL database."""
        connection = "postgresql://warehouse:warehouse@localhost:5432/warehouse"

        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="test.sample_data",
            mode="replace",
        )

        assert result.rows_written == 5
        assert result.table == "test.sample_data"
