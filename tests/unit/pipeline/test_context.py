"""Tests for ExecutionContext."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from quicketl.pipeline.context import ExecutionContext


class TestExecutionContextInit:
    """Tests for ExecutionContext initialization."""

    def test_default_init(self):
        ctx = ExecutionContext()
        assert ctx.variables == {}
        assert ctx.tables == {}
        assert ctx.metadata != {}
        assert "run_id" in ctx.metadata

    def test_init_with_variables(self):
        ctx = ExecutionContext(variables={"FOO": "bar"})
        assert ctx.variables == {"FOO": "bar"}

    def test_run_id_generated(self):
        ctx = ExecutionContext()
        run_id = ctx.run_id
        assert isinstance(run_id, str)
        assert len(run_id) > 0

    def test_custom_run_id_preserved(self):
        ctx = ExecutionContext(metadata={"run_id": "custom_123"})
        assert ctx.run_id == "custom_123"


class TestExecutionContextVariables:
    """Tests for variable get/set."""

    def test_get_variable_exists(self):
        ctx = ExecutionContext(variables={"DB": "postgres"})
        assert ctx.get_variable("DB") == "postgres"

    def test_get_variable_missing_returns_none(self):
        ctx = ExecutionContext()
        assert ctx.get_variable("MISSING") is None

    def test_get_variable_missing_with_default(self):
        ctx = ExecutionContext()
        assert ctx.get_variable("MISSING", "fallback") == "fallback"

    def test_set_variable(self):
        ctx = ExecutionContext()
        ctx.set_variable("KEY", "VALUE")
        assert ctx.get_variable("KEY") == "VALUE"


class TestExecutionContextTables:
    """Tests for table storage and retrieval."""

    def test_store_and_get_table(self):
        ctx = ExecutionContext()
        sentinel = object()  # stand-in for an ibis table
        ctx.store_table("orders", sentinel)
        assert ctx.get_table("orders") is sentinel

    def test_get_table_not_found(self):
        ctx = ExecutionContext()
        with pytest.raises(KeyError, match="Table 'missing' not found"):
            ctx.get_table("missing")

    def test_has_table_true(self):
        ctx = ExecutionContext()
        ctx.store_table("t", object())
        assert ctx.has_table("t") is True

    def test_has_table_false(self):
        ctx = ExecutionContext()
        assert ctx.has_table("nope") is False


class TestExecutionContextFromEnv:
    """Tests for from_env class method."""

    def test_from_env_default_prefix(self):
        with mock.patch.dict(os.environ, {"ETLX_DB_URL": "pg://host/db", "OTHER": "skip"}):
            ctx = ExecutionContext.from_env()
            assert ctx.get_variable("DB_URL") == "pg://host/db"
            assert ctx.get_variable("OTHER") is None

    def test_from_env_custom_prefix(self):
        with mock.patch.dict(os.environ, {"MYAPP_KEY": "val"}):
            ctx = ExecutionContext.from_env(prefix="MYAPP_")
            assert ctx.get_variable("KEY") == "val"

    def test_from_env_no_matching_vars(self):
        with mock.patch.dict(os.environ, {"UNRELATED": "x"}, clear=True):
            ctx = ExecutionContext.from_env(prefix="ZZZ_")
            assert ctx.variables == {}


class TestExecutionContextProperties:
    """Tests for properties and serialization."""

    def test_elapsed_seconds(self):
        ctx = ExecutionContext()
        assert ctx.elapsed_seconds >= 0.0

    def test_to_dict(self):
        ctx = ExecutionContext(variables={"A": "1"})
        ctx.store_table("t1", object())
        d = ctx.to_dict()

        assert d["variables"] == {"A": "1"}
        assert "run_id" in d["metadata"]
        assert d["stored_tables"] == ["t1"]
        assert "start_time" in d
