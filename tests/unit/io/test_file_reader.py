"""Tests for file reader functionality."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quicketl.io.readers.file import read_csv, read_file, read_json, read_parquet


class TestReadFile:
    """Tests for the read_file function."""

    def test_read_csv_file(self, temp_dir: Path):
        """Test reading a CSV file."""
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n")

        table = read_file(str(csv_path), "csv")
        df = table.to_pandas()

        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "value"]
        assert df["name"].iloc[0] == "Alice"

    def test_read_parquet_file(self, temp_dir: Path):
        """Test reading a Parquet file."""
        parquet_path = temp_dir / "test.parquet"
        pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]}).to_parquet(parquet_path)

        table = read_file(str(parquet_path), "parquet")
        df = table.to_pandas()

        assert len(df) == 2
        assert "id" in df.columns
        assert "name" in df.columns

    def test_read_parquet_with_pq_alias(self, temp_dir: Path):
        """Test reading Parquet with 'pq' alias."""
        parquet_path = temp_dir / "test.parquet"
        pd.DataFrame({"id": [1, 2]}).to_parquet(parquet_path)

        table = read_file(str(parquet_path), "pq")
        df = table.to_pandas()

        assert len(df) == 2

    def test_read_json_file(self, temp_dir: Path):
        """Test reading a JSON/JSONL file."""
        json_path = temp_dir / "test.json"
        json_path.write_text('{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}\n')

        table = read_file(str(json_path), "json")
        df = table.to_pandas()

        assert len(df) == 2
        assert "id" in df.columns

    def test_read_json_with_jsonl_alias(self, temp_dir: Path):
        """Test reading JSON with 'jsonl' alias."""
        json_path = temp_dir / "test.jsonl"
        json_path.write_text('{"id": 1}\n{"id": 2}\n')

        table = read_file(str(json_path), "jsonl")
        df = table.to_pandas()

        assert len(df) == 2

    def test_read_json_with_ndjson_alias(self, temp_dir: Path):
        """Test reading JSON with 'ndjson' alias."""
        json_path = temp_dir / "test.ndjson"
        json_path.write_text('{"id": 1}\n{"id": 2}\n')

        table = read_file(str(json_path), "ndjson")
        df = table.to_pandas()

        assert len(df) == 2

    def test_read_unsupported_format_raises_error(self, temp_dir: Path):
        """Test that unsupported format raises ValueError."""
        fake_path = temp_dir / "test.xyz"
        fake_path.write_text("some data")

        with pytest.raises(ValueError) as exc_info:
            read_file(str(fake_path), "xyz")

        assert "Unsupported file format" in str(exc_info.value)

    def test_read_with_custom_backend(self, temp_dir: Path):
        """Test reading with custom backend."""
        import ibis

        csv_path = temp_dir / "test.csv"
        csv_path.write_text("id,value\n1,100\n")

        backend = ibis.duckdb.connect()
        table = read_file(str(csv_path), "csv", backend=backend)
        df = table.to_pandas()

        assert len(df) == 1


class TestReadParquet:
    """Tests for the read_parquet function."""

    def test_read_parquet(self, temp_dir: Path):
        """Test read_parquet convenience function."""
        parquet_path = temp_dir / "test.parquet"
        pd.DataFrame({"id": [1, 2, 3]}).to_parquet(parquet_path)

        table = read_parquet(str(parquet_path))
        df = table.to_pandas()

        assert len(df) == 3


class TestReadCsv:
    """Tests for the read_csv function."""

    def test_read_csv(self, temp_dir: Path):
        """Test read_csv convenience function."""
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("id,name\n1,Alice\n2,Bob\n")

        table = read_csv(str(csv_path))
        df = table.to_pandas()

        assert len(df) == 2
        assert df["name"].iloc[0] == "Alice"


class TestReadJson:
    """Tests for the read_json function."""

    def test_read_json(self, temp_dir: Path):
        """Test read_json convenience function."""
        json_path = temp_dir / "test.json"
        json_path.write_text('{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}\n')

        table = read_json(str(json_path))
        df = table.to_pandas()

        assert len(df) == 2
