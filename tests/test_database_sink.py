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
