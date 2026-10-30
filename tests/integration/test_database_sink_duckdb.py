"""Tests for the transaction based write modes on a DuckDB target."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

if TYPE_CHECKING:
    from pathlib import Path


def _table(ids: list[int], label: str) -> ibis.Table:
    return ibis.memtable({"id": ids, "label": [f"{label}{i}" for i in ids]})


def test_truncate_replaces_all_rows_on_duckdb(engine, temp_dir: Path):
    """Truncate runs BEGIN, DELETE, INSERT and COMMIT on one DuckDB connection."""
    connection = f"duckdb:///{temp_dir / 'target.db'}"
    engine.write_database(
        _table([1, 2, 3], "old"), connection=connection, target_table="t", mode="append"
    )

    engine.write_database(
        _table([7, 8], "new"), connection=connection, target_table="t", mode="truncate"
    )

    con = ibis.connect(connection)
    try:
        rows = con.table("t").order_by("id").execute()
        assert list(zip(rows["id"], rows["label"], strict=True)) == [(7, "new7"), (8, "new8")]
    finally:
        con.disconnect()
