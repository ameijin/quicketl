"""Tests for JSON output format in file writer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class TestJsonWriter:
    """Tests for writing JSON/JSONL output."""

    def test_write_json_creates_file(self, engine, sample_data, temp_dir: Path):
        """Test writing JSON Lines output."""
        output_path = temp_dir / "output.json"

        result = engine.write_file(
            sample_data,
            str(output_path),
            format="json",
        )

        assert result.rows_written == 5
        assert output_path.exists()

    def test_write_json_valid_jsonl(self, engine, sample_data, temp_dir: Path):
        """Test that output is valid JSON Lines (one JSON object per line)."""
        output_path = temp_dir / "output.jsonl"

        engine.write_file(sample_data, str(output_path), format="json")

        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == 5

        # Each line should be valid JSON
        for line in lines:
            record = json.loads(line)
            assert "name" in record
            assert "region" in record
            assert "amount" in record

    def test_write_json_partitioned_raises(self, engine, sample_data, temp_dir: Path):
        """Test that partitioned JSON writes raise ValueError."""
        output_path = temp_dir / "partitioned_json"

        with pytest.raises(ValueError, match="not supported for JSON"):
            engine.write_file(
                sample_data,
                str(output_path),
                format="json",
                partition_by=["region"],
            )


class TestJsonSinkConfig:
    """Tests for JSON in FileSink config model."""

    def test_file_sink_accepts_json_format(self):
        from quicketl.config.models import FileSink

        sink = FileSink(path="output.json", format="json")
        assert sink.format == "json"

    def test_file_sink_rejects_invalid_format(self):
        from pydantic import ValidationError

        from quicketl.config.models import FileSink

        with pytest.raises(ValidationError):
            FileSink(path="output.xml", format="xml")
