"""Tests for engines/backends.py module."""

from __future__ import annotations

import pytest

from quicketl.engines.backends import (
    BACKENDS,
    BackendConfig,
    get_backend,
    get_backend_info,
    list_backends,
)
from quicketl.engines.base import QuickETLEngine


class TestBackendConfig:
    """Tests for BackendConfig dataclass."""

    def test_to_engine_duckdb(self):
        config = BackendConfig(name="duckdb")
        engine = config.to_engine()
        assert isinstance(engine, QuickETLEngine)

    def test_to_engine_with_options(self):
        config = BackendConfig(name="duckdb", options={})
        engine = config.to_engine()
        assert isinstance(engine, QuickETLEngine)

    def test_default_values(self):
        config = BackendConfig(name="duckdb")
        assert config.connection_string is None
        assert config.options is None


class TestListBackends:
    """Tests for list_backends function."""

    def test_returns_list(self):
        result = list_backends()
        assert isinstance(result, list)
        assert len(result) == len(BACKENDS)

    def test_each_entry_has_id(self):
        result = list_backends()
        for entry in result:
            assert "id" in entry
            assert "name" in entry
            assert "description" in entry


class TestGetBackend:
    """Tests for get_backend function."""

    def test_get_duckdb(self):
        engine = get_backend("duckdb")
        assert isinstance(engine, QuickETLEngine)

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend: nonexistent"):
            get_backend("nonexistent")


class TestGetBackendInfo:
    """Tests for get_backend_info function."""

    def test_get_duckdb_info(self):
        info = get_backend_info("duckdb")
        assert info["id"] == "duckdb"
        assert info["name"] == "DuckDB"
        assert info["supports_sql"] is True

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend: fake"):
            get_backend_info("fake")

    def test_all_backends_have_required_keys(self):
        required_keys = {"name", "description", "supports_sql", "supports_file_io", "requires_connection"}
        for backend_id, info in BACKENDS.items():
            assert required_keys.issubset(info.keys()), f"{backend_id} missing keys"
