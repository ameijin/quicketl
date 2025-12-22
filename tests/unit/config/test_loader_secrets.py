"""Tests for secret resolution in config loader.

This module tests the ${secret:path} syntax in YAML configuration loading.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from quicketl.config.loader import substitute_variables


class TestSecretSubstitution:
    """Tests for ${secret:path} substitution in config loading."""

    def test_substitute_env_secret_reference(self, monkeypatch):
        """Substitute ${secret:VAR} using env provider."""
        monkeypatch.setenv("DATABASE_PASSWORD", "my_db_pass")

        result = substitute_variables(
            "postgresql://user:${secret:DATABASE_PASSWORD}@localhost/db",
            {},
            secrets_provider="env",
        )

        assert result == "postgresql://user:my_db_pass@localhost/db"

    def test_substitute_secret_with_path(self, monkeypatch):
        """Substitute ${secret:path/to/secret} format."""
        monkeypatch.setenv("DB_CREDENTIALS_PASSWORD", "secret123")

        result = substitute_variables(
            "${secret:DB_CREDENTIALS_PASSWORD}",
            {},
            secrets_provider="env",
        )

        assert result == "secret123"

    def test_mixed_env_and_secret_references(self, monkeypatch):
        """Handle both ${VAR} and ${secret:path} in same string."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("DB_PASSWORD", "secret_pass")

        result = substitute_variables(
            "postgresql://admin:${secret:DB_PASSWORD}@${HOST}/mydb",
            {},
            secrets_provider="env",
        )

        assert result == "postgresql://admin:secret_pass@localhost/mydb"

    def test_nested_secret_references_in_dict(self, monkeypatch):
        """Handle secret references nested in dict values."""
        monkeypatch.setenv("API_KEY", "key123")
        monkeypatch.setenv("API_SECRET", "secret456")

        data = {
            "credentials": {
                "key": "${secret:API_KEY}",
                "secret": "${secret:API_SECRET}",
            }
        }

        result = substitute_variables(data, {}, secrets_provider="env")

        assert result["credentials"]["key"] == "key123"
        assert result["credentials"]["secret"] == "secret456"

    def test_secret_reference_with_default(self, monkeypatch):
        """Handle ${secret:path:-default} syntax."""
        monkeypatch.delenv("MISSING_SECRET", raising=False)

        result = substitute_variables(
            "${secret:MISSING_SECRET:-default_value}",
            {},
            secrets_provider="env",
        )

        assert result == "default_value"

    def test_secret_reference_missing_raises_error(self, monkeypatch):
        """Missing secret without default raises error."""
        monkeypatch.delenv("MISSING_SECRET", raising=False)

        with pytest.raises(KeyError, match="Secret not found"):
            substitute_variables(
                "${secret:MISSING_SECRET}",
                {},
                secrets_provider="env",
            )

    def test_secret_provider_config_passed_through(self):
        """Secrets provider config is passed to provider."""
        mock_provider = MagicMock()
        mock_provider.get_secret.return_value = "mock_secret"

        with patch("quicketl.secrets.get_provider", return_value=mock_provider):
            result = substitute_variables(
                "${secret:my/path}",
                {},
                secrets_provider="aws",
                secrets_config={"region_name": "us-west-2"},
            )

        assert result == "mock_secret"
        mock_provider.get_secret.assert_called_once_with("my/path", default=None)


class TestSecretSubstitutionInPipeline:
    """Tests for secret substitution in pipeline config loading."""

    def test_pipeline_source_with_secret(self, tmp_path, monkeypatch):
        """Pipeline source connection string uses secrets."""
        monkeypatch.setenv("DB_CONN_STRING", "postgresql://user:pass@host/db")

        from quicketl.config.loader import load_pipeline_config

        yaml_content = """
name: test_pipeline
engine: duckdb

source:
  type: database
  connection: ${secret:DB_CONN_STRING}
  query: SELECT * FROM users

sink:
  type: file
  path: /tmp/output.parquet
  format: parquet
"""
        yaml_file = tmp_path / "pipeline.yml"
        yaml_file.write_text(yaml_content)

        config = load_pipeline_config(yaml_file, secrets_provider="env")

        assert config.source.connection == "postgresql://user:pass@host/db"

    def test_pipeline_sink_with_secret(self, tmp_path, monkeypatch):
        """Pipeline sink connection uses secrets."""
        monkeypatch.setenv("OUTPUT_DB_CONN", "snowflake://user:pass@account/db")

        from quicketl.config.loader import load_pipeline_config

        yaml_content = """
name: test_pipeline
engine: duckdb

source:
  type: file
  path: /data/input.csv
  format: csv

sink:
  type: database
  connection: ${secret:OUTPUT_DB_CONN}
  table: output_table
  mode: replace
"""
        yaml_file = tmp_path / "pipeline.yml"
        yaml_file.write_text(yaml_content)

        config = load_pipeline_config(yaml_file, secrets_provider="env")

        assert config.sink.connection == "snowflake://user:pass@account/db"
