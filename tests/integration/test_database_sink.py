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


def _create_strict_target(db_path: Path) -> None:
    """Create a target table that rejects the sample data on insert.

    The extra NOT NULL column is missing from the incoming rows, so any
    insert of the sample data fails partway through a write.
    """
    import sqlite3

    with sqlite3.connect(db_path) as con:
        con.execute(
            "CREATE TABLE test_table (id INTEGER, name TEXT, amount REAL, "
            "region TEXT, active INTEGER, note TEXT NOT NULL)"
        )
        con.executemany(
            "INSERT INTO test_table VALUES (?, ?, ?, ?, ?, 'original')",
            [(i, f"row{i}", 1.0, "North", 1) for i in range(1, 6)],
        )
    con.close()


def _row_count(db_path: Path) -> int:
    import sqlite3

    with sqlite3.connect(db_path) as con:
        count = con.execute("SELECT COUNT(*) FROM test_table").fetchone()[0]
    con.close()
    return count


class TestDatabaseSinkFailureSafety:
    """A failed write must keep existing rows and surface the real error."""

    @pytest.mark.parametrize("mode", ["upsert", "truncate"])
    def test_failed_insert_keeps_existing_rows(
        self, engine, sample_data, temp_dir: Path, mode: str
    ):
        """If the insert fails after the delete, the delete is rolled back."""
        db_path = temp_dir / "test.db"
        _create_strict_target(db_path)

        with pytest.raises(Exception, match="NOT NULL"):
            engine.write_database(
                sample_data,
                connection=f"sqlite:///{db_path}",
                target_table="test_table",
                mode=mode,
                upsert_keys=["id"] if mode == "upsert" else None,
            )

        assert _row_count(db_path) == 5

    def test_failed_append_surfaces_original_error(self, engine, sample_data, temp_dir: Path):
        """An append failure is raised as is, not replaced by a create error."""
        db_path = temp_dir / "test.db"
        _create_strict_target(db_path)

        with pytest.raises(Exception, match="NOT NULL"):
            engine.write_database(
                sample_data,
                connection=f"sqlite:///{db_path}",
                target_table="test_table",
                mode="append",
            )

        assert _row_count(db_path) == 5

    @pytest.mark.parametrize("mode", ["append", "truncate", "upsert"])
    def test_missing_table_is_created(self, engine, sample_data, temp_dir: Path, mode: str):
        """Writing to a table that does not exist yet creates it."""
        import ibis

        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"

        result = engine.write_database(
            sample_data,
            connection=connection,
            target_table="new_table",
            mode=mode,
            upsert_keys=["id"] if mode == "upsert" else None,
        )

        assert result.rows_written == 5
        assert ibis.connect(connection).table("new_table").count().execute() == 5

    def test_truncate_replaces_all_rows(self, engine, sample_data, temp_dir: Path):
        """Truncate leaves exactly the incoming rows in the table."""
        import ibis

        db_path = temp_dir / "test.db"
        connection = f"sqlite:///{db_path}"
        for _ in range(2):
            engine.write_database(
                sample_data, connection=connection, target_table="t", mode="append"
            )

        engine.write_database(sample_data, connection=connection, target_table="t", mode="truncate")

        assert ibis.connect(connection).table("t").count().execute() == 5


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
