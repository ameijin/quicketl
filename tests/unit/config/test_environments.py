"""Tests for environment inheritance and connection profiles.

This module tests:
- Environment configuration with inheritance (base, dev, prod)
- Deep merging of nested config values
- Connection profiles with secret references
- Project configuration (quicketl.yml)
"""

from __future__ import annotations

import pytest

from quicketl.config.environments import (
    load_environment,
    merge_configs,
)
from quicketl.config.profiles import (
    ProfileRegistry,
    load_profiles,
)
from quicketl.config.project import (
    load_project_config,
)

# ============================================================================
# Environment Inheritance Tests
# ============================================================================


class TestEnvironmentInheritance:
    """Tests for environment configuration with inheritance."""

    def test_base_environment_loaded(self, tmp_path):
        """Load base environment without inheritance."""
        config = {
            "environments": {
                "base": {
                    "engine": "duckdb",
                    "quality": {"fail_on_error": True},
                }
            }
        }

        env = load_environment(config, "base")

        assert env.engine == "duckdb"
        assert env.quality["fail_on_error"] is True

    def test_dev_extends_base(self, tmp_path):
        """Dev environment inherits from base."""
        config = {
            "environments": {
                "base": {
                    "engine": "duckdb",
                    "quality": {"fail_on_error": True},
                },
                "dev": {
                    "extends": "base",
                    "quality": {"fail_on_error": False},
                },
            }
        }

        env = load_environment(config, "dev")

        assert env.engine == "duckdb"  # Inherited from base
        assert env.quality["fail_on_error"] is False  # Overridden in dev

    def test_prod_overrides_base_values(self, tmp_path):
        """Prod environment overrides base with production settings."""
        config = {
            "environments": {
                "base": {
                    "engine": "duckdb",
                    "logging": {"level": "DEBUG"},
                },
                "prod": {
                    "extends": "base",
                    "engine": "snowflake",
                    "logging": {"level": "INFO", "format": "json"},
                },
            }
        }

        env = load_environment(config, "prod")

        assert env.engine == "snowflake"  # Overridden
        assert env.logging["level"] == "INFO"  # Overridden
        assert env.logging["format"] == "json"  # Added in prod

    def test_deep_merge_of_nested_config(self, tmp_path):
        """Nested config values are deeply merged."""
        config = {
            "environments": {
                "base": {
                    "quality": {
                        "checks": {
                            "not_null": {"severity": "error"},
                            "unique": {"severity": "warn"},
                        }
                    }
                },
                "prod": {
                    "extends": "base",
                    "quality": {
                        "checks": {
                            "not_null": {"severity": "error", "fail_fast": True},
                        }
                    },
                },
            }
        }

        env = load_environment(config, "prod")

        # Deep merge should preserve unique from base and add fail_fast to not_null
        assert env.quality["checks"]["not_null"]["severity"] == "error"
        assert env.quality["checks"]["not_null"]["fail_fast"] is True
        assert env.quality["checks"]["unique"]["severity"] == "warn"

    def test_environment_from_env_variable(self, tmp_path, monkeypatch):
        """Environment can be selected via environment variable."""
        monkeypatch.setenv("QUICKETL_ENV", "staging")

        config = {
            "environments": {
                "dev": {"engine": "duckdb"},
                "staging": {"engine": "snowflake"},
            }
        }

        env = load_environment(config)  # No env name, uses QUICKETL_ENV

        assert env.engine == "snowflake"

    def test_missing_environment_raises_error(self, tmp_path):
        """Requesting missing environment raises error."""
        config = {
            "environments": {
                "dev": {"engine": "duckdb"},
            }
        }

        with pytest.raises(KeyError, match="Environment not found"):
            load_environment(config, "prod")

    def test_circular_extends_raises_error(self, tmp_path):
        """Circular inheritance raises error."""
        config = {
            "environments": {
                "a": {"extends": "b", "engine": "duckdb"},
                "b": {"extends": "a", "engine": "polars"},
            }
        }

        with pytest.raises(ValueError, match="Circular"):
            load_environment(config, "a")


# ============================================================================
# Config Merge Tests
# ============================================================================


class TestMergeConfigs:
    """Tests for deep config merging."""

    def test_merge_flat_dicts(self):
        """Merge two flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Merge nested dictionaries recursively."""
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 3, "c": 4}}

        result = merge_configs(base, override)

        assert result == {"outer": {"a": 1, "b": 3, "c": 4}}

    def test_override_replaces_non_dict_values(self):
        """Non-dict values in override replace base entirely."""
        base = {"key": {"nested": "value"}}
        override = {"key": "simple_string"}

        result = merge_configs(base, override)

        assert result == {"key": "simple_string"}

    def test_merge_preserves_lists(self):
        """Lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}

        result = merge_configs(base, override)

        assert result == {"items": [4, 5]}


# ============================================================================
# Connection Profile Tests
# ============================================================================


class TestConnectionProfiles:
    """Tests for connection profile management."""

    def test_load_profile_from_config(self, tmp_path):
        """Load a connection profile from config."""
        config = {
            "profiles": {
                "snowflake_prod": {
                    "type": "snowflake",
                    "account": "myaccount",
                    "warehouse": "TRANSFORM_WH",
                    "role": "TRANSFORM_ROLE",
                }
            }
        }

        profiles = load_profiles(config)
        profile = profiles.get("snowflake_prod")

        assert profile.type == "snowflake"
        assert profile.account == "myaccount"
        assert profile.warehouse == "TRANSFORM_WH"

    def test_profile_with_secret_references(self, tmp_path, monkeypatch):
        """Profile values can reference secrets."""
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "secret_account")
        monkeypatch.setenv("SNOWFLAKE_PASSWORD", "secret_pass")

        config = {
            "profiles": {
                "snowflake_prod": {
                    "type": "snowflake",
                    "account": "${secret:SNOWFLAKE_ACCOUNT}",
                    "password": "${secret:SNOWFLAKE_PASSWORD}",
                }
            }
        }

        profiles = load_profiles(config, secrets_provider="env")
        profile = profiles.get("snowflake_prod")

        assert profile.account == "secret_account"
        assert profile.password == "secret_pass"

    def test_profile_in_source_config(self, tmp_path, monkeypatch):
        """Source can reference a profile for connection."""
        monkeypatch.setenv("DB_CONN", "postgresql://user:pass@host/db")

        from quicketl.config.loader import load_pipeline_config

        yaml_content = """
name: test_pipeline
engine: duckdb

source:
  type: database
  profile: postgres_prod
  query: SELECT * FROM users

sink:
  type: file
  path: /tmp/output.parquet
  format: parquet
"""
        project_config = {
            "profiles": {
                "postgres_prod": {
                    "type": "postgres",
                    "connection": "${secret:DB_CONN}",
                }
            }
        }

        yaml_file = tmp_path / "pipeline.yml"
        yaml_file.write_text(yaml_content)

        # This should resolve the profile and use its connection
        config = load_pipeline_config(
            yaml_file,
            secrets_provider="env",
            profiles=project_config.get("profiles"),
        )

        assert config.source.connection == "postgresql://user:pass@host/db"

    def test_missing_profile_raises_error(self):
        """Referencing missing profile raises error."""
        profiles = ProfileRegistry({})

        with pytest.raises(KeyError, match="Profile not found"):
            profiles.get("nonexistent")


# ============================================================================
# Project Configuration Tests
# ============================================================================


class TestProjectConfig:
    """Tests for project-level configuration (quicketl.yml)."""

    def test_load_project_config_basic(self, tmp_path):
        """Load basic project configuration."""
        yaml_content = """
version: "1.0"
defaults:
  engine: duckdb
"""
        yaml_file = tmp_path / "quicketl.yml"
        yaml_file.write_text(yaml_content)

        config = load_project_config(yaml_file)

        assert config.version == "1.0"
        assert config.defaults["engine"] == "duckdb"

    def test_load_project_config_with_environments(self, tmp_path):
        """Load project config with environment definitions."""
        yaml_content = """
version: "1.0"

environments:
  base:
    engine: duckdb
  prod:
    extends: base
    engine: snowflake
"""
        yaml_file = tmp_path / "quicketl.yml"
        yaml_file.write_text(yaml_content)

        config = load_project_config(yaml_file)

        assert "base" in config.environments
        assert "prod" in config.environments
        assert config.environments["prod"]["extends"] == "base"

    def test_load_project_config_with_profiles(self, tmp_path):
        """Load project config with connection profiles."""
        yaml_content = """
version: "1.0"

profiles:
  snowflake_prod:
    type: snowflake
    account: myaccount
    warehouse: TRANSFORM_WH
"""
        yaml_file = tmp_path / "quicketl.yml"
        yaml_file.write_text(yaml_content)

        config = load_project_config(yaml_file)

        assert "snowflake_prod" in config.profiles
        assert config.profiles["snowflake_prod"]["type"] == "snowflake"

    def test_load_project_config_with_secrets(self, tmp_path):
        """Load project config with secrets provider settings."""
        yaml_content = """
version: "1.0"

secrets:
  provider: aws
  config:
    region_name: us-east-1
"""
        yaml_file = tmp_path / "quicketl.yml"
        yaml_file.write_text(yaml_content)

        config = load_project_config(yaml_file)

        assert config.secrets["provider"] == "aws"
        assert config.secrets["config"]["region_name"] == "us-east-1"

    def test_project_config_not_found_returns_defaults(self, tmp_path):
        """Missing project config returns sensible defaults."""
        config = load_project_config(tmp_path / "nonexistent.yml")

        assert config.version == "1.0"
        assert config.environments == {}
        assert config.profiles == {}
