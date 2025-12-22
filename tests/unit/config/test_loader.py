"""Tests for the config loader and variable substitution.

This module tests YAML loading and ${VAR} variable substitution.
"""

from __future__ import annotations

import os
import string
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from quicketl.config.loader import (
    load_pipeline_config,
    load_yaml_with_variables,
    substitute_variables,
)


class TestSubstituteVariablesStrings:
    """Tests for substitute_variables with string values."""

    def test_simple_variable_substitution(self):
        """Test simple ${VAR} substitution."""
        result = substitute_variables("${NAME}", {"NAME": "Alice"})
        assert result == "Alice"

    def test_variable_in_string(self):
        """Test variable embedded in string."""
        result = substitute_variables("Hello, ${NAME}!", {"NAME": "Bob"})
        assert result == "Hello, Bob!"

    def test_multiple_variables(self):
        """Test multiple variables in one string."""
        result = substitute_variables(
            "${GREETING}, ${NAME}!",
            {"GREETING": "Hello", "NAME": "Charlie"},
        )
        assert result == "Hello, Charlie!"

    def test_variable_with_default_uses_value(self):
        """Test ${VAR:-default} uses provided value."""
        result = substitute_variables("${NAME:-Unknown}", {"NAME": "Diana"})
        assert result == "Diana"

    def test_variable_with_default_uses_default(self):
        """Test ${VAR:-default} uses default when var missing."""
        result = substitute_variables("${NAME:-Unknown}", {})
        assert result == "Unknown"

    def test_empty_default_value(self):
        """Test ${VAR:-} with empty default."""
        result = substitute_variables("${NAME:-}", {})
        assert result == ""

    def test_missing_variable_preserved(self):
        """Test missing variable without default is preserved."""
        result = substitute_variables("${MISSING}", {})
        assert result == "${MISSING}"

    def test_no_variables_in_string(self):
        """Test string without variables passes through."""
        result = substitute_variables("plain text", {})
        assert result == "plain text"

    def test_environment_variable_fallback(self, monkeypatch):
        """Test fallback to environment variables."""
        monkeypatch.setenv("TEST_VAR", "from_env")
        result = substitute_variables("${TEST_VAR}", {})
        assert result == "from_env"

    def test_explicit_overrides_environment(self, monkeypatch):
        """Test explicit variable overrides environment."""
        monkeypatch.setenv("TEST_VAR", "from_env")
        result = substitute_variables("${TEST_VAR}", {"TEST_VAR": "explicit"})
        assert result == "explicit"

    def test_path_with_variable(self):
        """Test path-like string with variable."""
        result = substitute_variables("/data/${DATE}/output.csv", {"DATE": "2025-01-01"})
        assert result == "/data/2025-01-01/output.csv"

    def test_url_with_variables(self):
        """Test URL with multiple variables."""
        result = substitute_variables(
            "postgresql://${USER}:${PASS}@${HOST}/db",
            {"USER": "admin", "PASS": "secret", "HOST": "localhost"},
        )
        assert result == "postgresql://admin:secret@localhost/db"


class TestSubstituteVariablesDict:
    """Tests for substitute_variables with dict values."""

    def test_dict_with_variable_values(self):
        """Test dict values are substituted."""
        data = {"name": "${NAME}", "path": "${PATH}"}
        result = substitute_variables(data, {"NAME": "test", "PATH": "/tmp"})
        assert result == {"name": "test", "path": "/tmp"}

    def test_nested_dict(self):
        """Test nested dict values are substituted."""
        data = {
            "outer": {
                "inner": "${VALUE}",
            }
        }
        result = substitute_variables(data, {"VALUE": "nested"})
        assert result == {"outer": {"inner": "nested"}}

    def test_deeply_nested_dict(self):
        """Test deeply nested dict values are substituted."""
        data = {
            "a": {
                "b": {
                    "c": {
                        "d": "${DEEP}",
                    }
                }
            }
        }
        result = substitute_variables(data, {"DEEP": "value"})
        assert result["a"]["b"]["c"]["d"] == "value"


class TestSubstituteVariablesList:
    """Tests for substitute_variables with list values."""

    def test_list_with_variable_values(self):
        """Test list values are substituted."""
        data = ["${A}", "${B}", "${C}"]
        result = substitute_variables(data, {"A": "1", "B": "2", "C": "3"})
        assert result == ["1", "2", "3"]

    def test_list_in_dict(self):
        """Test list inside dict is substituted."""
        data = {"columns": ["${COL1}", "${COL2}"]}
        result = substitute_variables(data, {"COL1": "id", "COL2": "name"})
        assert result == {"columns": ["id", "name"]}


class TestSubstituteVariablesOtherTypes:
    """Tests for substitute_variables with other types."""

    def test_integer_passthrough(self):
        """Test integers pass through unchanged."""
        assert substitute_variables(42, {}) == 42

    def test_float_passthrough(self):
        """Test floats pass through unchanged."""
        assert substitute_variables(3.14, {}) == 3.14

    def test_boolean_passthrough(self):
        """Test booleans pass through unchanged."""
        assert substitute_variables(True, {}) is True
        assert substitute_variables(False, {}) is False

    def test_none_passthrough(self):
        """Test None passes through unchanged."""
        assert substitute_variables(None, {}) is None


class TestLoadYamlWithVariables:
    """Tests for load_yaml_with_variables function."""

    def test_load_simple_yaml(self, tmp_path):
        """Test loading a simple YAML file."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("name: test\nvalue: 123")

        result = load_yaml_with_variables(yaml_file)
        assert result == {"name": "test", "value": 123}

    def test_load_yaml_with_variable_substitution(self, tmp_path):
        """Test loading YAML with variable substitution."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("path: /data/${DATE}/file.csv")

        result = load_yaml_with_variables(yaml_file, {"DATE": "2025-01-01"})
        assert result["path"] == "/data/2025-01-01/file.csv"

    def test_load_yaml_missing_file_raises_error(self, tmp_path):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_yaml_with_variables(tmp_path / "nonexistent.yml")

    def test_load_empty_yaml_returns_empty_dict(self, tmp_path):
        """Test loading empty YAML file returns empty dict."""
        yaml_file = tmp_path / "empty.yml"
        yaml_file.write_text("")

        result = load_yaml_with_variables(yaml_file)
        assert result == {}

    def test_load_yaml_accepts_string_path(self, tmp_path):
        """Test loading YAML with string path."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")

        result = load_yaml_with_variables(str(yaml_file))
        assert result == {"key": "value"}


class TestLoadPipelineConfig:
    """Tests for load_pipeline_config function."""

    def test_load_valid_pipeline_config(self, tmp_path):
        """Test loading a valid pipeline configuration."""
        yaml_content = """
name: test_pipeline
engine: duckdb

source:
  type: file
  path: /data/input.csv
  format: csv

transforms:
  - op: filter
    predicate: amount > 0

checks:
  - type: not_null
    columns: [id]

sink:
  type: file
  path: /data/output.parquet
  format: parquet
"""
        yaml_file = tmp_path / "pipeline.yml"
        yaml_file.write_text(yaml_content)

        config = load_pipeline_config(yaml_file)
        assert config.name == "test_pipeline"
        assert config.engine == "duckdb"

    def test_load_pipeline_with_variable_substitution(self, tmp_path):
        """Test loading pipeline with variable substitution."""
        yaml_content = """
name: ${PIPELINE_NAME}
engine: duckdb

source:
  type: file
  path: ${INPUT_PATH}
  format: csv

sink:
  type: file
  path: ${OUTPUT_PATH}
  format: parquet
"""
        yaml_file = tmp_path / "pipeline.yml"
        yaml_file.write_text(yaml_content)

        config = load_pipeline_config(
            yaml_file,
            variables={
                "PIPELINE_NAME": "my_pipeline",
                "INPUT_PATH": "/data/in.csv",
                "OUTPUT_PATH": "/data/out.parquet",
            },
        )
        assert config.name == "my_pipeline"
        assert config.source.path == "/data/in.csv"
        assert config.sink.path == "/data/out.parquet"


# ============================================================================
# Property-Based Tests with Hypothesis
# ============================================================================


class TestSubstituteVariablesWithHypothesis:
    """Property-based tests for variable substitution."""

    @pytest.mark.hypothesis
    @given(st.text().filter(lambda s: "${" not in s and "}" not in s))
    @settings(max_examples=100)
    def test_string_without_vars_unchanged(self, text):
        """Strings without ${} should pass through unchanged."""
        result = substitute_variables(text, {})
        assert result == text

    @pytest.mark.hypothesis
    @given(
        st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
        st.text(alphabet=string.ascii_letters + string.digits + " ", min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_variable_substitution_always_works(self, var_name, var_value):
        """Variable substitution should work for any valid name/value pair."""
        template = f"${{{var_name}}}"
        result = substitute_variables(template, {var_name: var_value})
        assert result == var_value

    @pytest.mark.hypothesis
    @given(
        st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
        st.text(alphabet=string.ascii_letters + string.digits + " ", min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_default_value_used_when_var_missing(self, var_name, default):
        """Default value should be used when variable is missing."""
        template = f"${{{var_name}:-{default}}}"
        result = substitute_variables(template, {})
        assert result == default

    @pytest.mark.hypothesis
    @given(st.integers())
    @settings(max_examples=50)
    def test_integers_passthrough_unchanged(self, value):
        """Integers should pass through substitute_variables unchanged."""
        result = substitute_variables(value, {"UNUSED": "var"})
        assert result == value

    @pytest.mark.hypothesis
    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_floats_passthrough_unchanged(self, value):
        """Floats should pass through substitute_variables unchanged."""
        result = substitute_variables(value, {"UNUSED": "var"})
        assert result == value

    @pytest.mark.hypothesis
    @given(st.lists(st.text(min_size=0, max_size=20), max_size=10))
    @settings(max_examples=50)
    def test_list_of_strings_all_substituted(self, strings):
        """All strings in a list should be processed."""
        result = substitute_variables(strings, {})
        assert len(result) == len(strings)
        # All non-variable strings should be unchanged
        for orig, res in zip(strings, result):
            if "${" not in orig:
                assert res == orig

    @pytest.mark.hypothesis
    @given(st.dictionaries(
        keys=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        values=st.text(min_size=0, max_size=20),
        max_size=10,
    ))
    @settings(max_examples=50)
    def test_dict_values_all_substituted(self, data):
        """All values in a dict should be processed."""
        result = substitute_variables(data, {})
        assert set(result.keys()) == set(data.keys())
        # All non-variable values should be unchanged
        for key in data:
            if "${" not in data[key]:
                assert result[key] == data[key]
