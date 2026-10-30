"""Tests for the platform spec model (platform.yml)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from quicketl.platform.spec import PlatformSpec, PlatformSpecError, load_platform_spec

if TYPE_CHECKING:
    from pathlib import Path

FULL_SPEC = """
version: "1"
name: acme_data
warehouse:
  type: snowflake
environments: [dev, prod]
layers: [raw, staging, marts]
domains:
  - name: sales
    description: Orders and customers
  - name: finance
roles:
  - name: loader
    access: {raw: write}
  - name: transformer
    access: {raw: read, staging: write, marts: write}
  - name: analyst
    access: {marts: read}
    domains: [sales]
sso:
  provider: okta
network:
  allowed_ips: [203.0.113.0/24, 198.51.100.7]
sources:
  - name: orders
    domain: sales
    location: s3://example-landing/sales/orders/
    format: parquet
orchestrator:
  type: airflow
  hosting: mwaa
  schedule: "@daily"
"""


def minimal(**overrides: Any) -> dict[str, Any]:
    """Smallest valid spec as a dict, with top-level overrides."""
    spec: dict[str, Any] = {
        "name": "acme_data",
        "warehouse": {"type": "snowflake"},
        "domains": [{"name": "sales"}],
    }
    spec.update(overrides)
    return spec


def error_text(exc: pytest.ExceptionInfo[ValidationError]) -> str:
    return str(exc.value)


class TestDefaults:
    def test_minimal_spec_fills_defaults(self):
        spec = PlatformSpec.model_validate(minimal())

        assert spec.version == "1"
        assert spec.environments == ["dev", "prod"]
        assert spec.layers == ["raw", "staging", "marts"]
        assert spec.roles == []
        assert spec.sources == []
        assert spec.sso.provider == "none"
        assert spec.network.allowed_ips == []
        assert spec.orchestrator.type == "airflow"
        assert spec.orchestrator.hosting == "mwaa"
        assert spec.orchestrator.schedule == "@daily"

    def test_landing_layer_is_the_first_layer(self):
        spec = PlatformSpec.model_validate(minimal(layers=["bronze", "silver", "gold"]))

        assert spec.landing_layer == "bronze"


class TestLoad:
    def test_load_full_spec(self, temp_dir: Path):
        path = temp_dir / "platform.yml"
        path.write_text(FULL_SPEC)

        spec = load_platform_spec(path)

        assert spec.name == "acme_data"
        assert spec.warehouse.type == "snowflake"
        assert [d.name for d in spec.domains] == ["sales", "finance"]
        assert spec.roles[2].domains == ["sales"]
        assert spec.roles[0].domains is None
        assert spec.sources[0].format == "parquet"
        assert spec.network.allowed_ips == ["203.0.113.0/24", "198.51.100.7"]

    def test_missing_file_raises(self, temp_dir: Path):
        with pytest.raises(PlatformSpecError, match="not found"):
            load_platform_spec(temp_dir / "platform.yml")

    def test_empty_file_raises(self, temp_dir: Path):
        path = temp_dir / "platform.yml"
        path.write_text("")

        with pytest.raises(PlatformSpecError, match="empty"):
            load_platform_spec(path)

    def test_non_mapping_raises(self, temp_dir: Path):
        path = temp_dir / "platform.yml"
        path.write_text("- just\n- a list\n")

        with pytest.raises(PlatformSpecError, match="mapping"):
            load_platform_spec(path)

    def test_bad_yaml_raises(self, temp_dir: Path):
        path = temp_dir / "platform.yml"
        path.write_text("name: [unclosed\n")

        with pytest.raises(PlatformSpecError, match="YAML"):
            load_platform_spec(path)


class TestNames:
    @pytest.mark.parametrize("name", ["Acme", "1acme", "acme-data", "acme data", ""])
    def test_project_name_must_be_identifier(self, name: str):
        with pytest.raises(ValidationError, match="lowercase"):
            PlatformSpec.model_validate(minimal(name=name))

    def test_environment_names_must_be_identifiers(self):
        with pytest.raises(ValidationError, match="lowercase"):
            PlatformSpec.model_validate(minimal(environments=["Dev"]))

    def test_duplicate_environments_rejected(self):
        with pytest.raises(ValidationError, match="duplicate") as exc:
            PlatformSpec.model_validate(minimal(environments=["dev", "dev"]))

        assert "dev" in error_text(exc)

    def test_at_least_one_environment(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(environments=[]))

    def test_duplicate_layers_rejected(self):
        with pytest.raises(ValidationError, match="duplicate"):
            PlatformSpec.model_validate(minimal(layers=["raw", "raw"]))

    def test_at_least_one_domain(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(domains=[]))

    def test_duplicate_domains_rejected(self):
        with pytest.raises(ValidationError, match="duplicate"):
            PlatformSpec.model_validate(minimal(domains=[{"name": "sales"}, {"name": "sales"}]))

    def test_duplicate_roles_rejected(self):
        role = {"name": "analyst", "access": {"marts": "read"}}
        with pytest.raises(ValidationError, match="duplicate"):
            PlatformSpec.model_validate(minimal(roles=[role, role]))

    def test_duplicate_sources_rejected(self):
        source = {"name": "orders", "domain": "sales", "location": "s3://b/orders/"}
        with pytest.raises(ValidationError, match="duplicate"):
            PlatformSpec.model_validate(minimal(sources=[source, source]))


class TestReferences:
    def test_role_access_to_unknown_layer_rejected(self):
        role = {"name": "analyst", "access": {"gold": "read"}}

        with pytest.raises(ValidationError, match="unknown layer 'gold'"):
            PlatformSpec.model_validate(minimal(roles=[role]))

    def test_role_with_unknown_domain_rejected(self):
        role = {"name": "analyst", "access": {"marts": "read"}, "domains": ["hr"]}

        with pytest.raises(ValidationError, match="unknown domain 'hr'"):
            PlatformSpec.model_validate(minimal(roles=[role]))

    def test_all_bad_references_reported_together(self):
        role = {"name": "analyst", "access": {"gold": "read"}, "domains": ["hr"]}
        source = {"name": "orders", "domain": "ops", "location": "s3://b/orders/"}

        with pytest.raises(ValidationError) as exc:
            PlatformSpec.model_validate(minimal(roles=[role], sources=[source]))

        text = error_text(exc)
        assert "unknown layer 'gold'" in text
        assert "unknown domain 'hr'" in text
        assert "unknown domain 'ops'" in text

    def test_role_needs_some_access(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(roles=[{"name": "analyst", "access": {}}]))

    def test_role_access_level_must_be_read_or_write(self):
        role = {"name": "analyst", "access": {"marts": "admin"}}

        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(roles=[role]))

    def test_source_with_unknown_domain_rejected(self):
        source = {"name": "orders", "domain": "hr", "location": "s3://b/orders/"}

        with pytest.raises(ValidationError, match="unknown domain 'hr'"):
            PlatformSpec.model_validate(minimal(sources=[source]))


class TestSources:
    def test_source_location_must_be_s3(self):
        source = {"name": "orders", "domain": "sales", "location": "/data/orders"}

        with pytest.raises(ValidationError, match="s3://"):
            PlatformSpec.model_validate(minimal(sources=[source]))

    def test_source_format_defaults_to_parquet(self):
        source = {"name": "orders", "domain": "sales", "location": "s3://b/orders/"}

        spec = PlatformSpec.model_validate(minimal(sources=[source]))

        assert spec.sources[0].format == "parquet"

    def test_unknown_source_format_rejected(self):
        source = {
            "name": "orders",
            "domain": "sales",
            "location": "s3://b/orders/",
            "format": "xlsx",
        }

        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(sources=[source]))


class TestNetwork:
    def test_invalid_ip_rejected(self):
        with pytest.raises(ValidationError, match="not an IP address or CIDR range"):
            PlatformSpec.model_validate(minimal(network={"allowed_ips": ["10.0.0.300"]}))

    def test_cidr_with_host_bits_rejected(self):
        """10.0.0.1/24 is almost always a typo for 10.0.0.0/24."""
        with pytest.raises(ValidationError, match="not an IP address or CIDR range"):
            PlatformSpec.model_validate(minimal(network={"allowed_ips": ["10.0.0.1/24"]}))


class TestStrictness:
    def test_unknown_top_level_key_rejected(self):
        """Typos such as `enviroments` fail instead of being ignored."""
        with pytest.raises(ValidationError, match="enviroments"):
            PlatformSpec.model_validate(minimal(enviroments=["dev"]))

    def test_unknown_nested_key_rejected(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(warehouse={"type": "snowflake", "size": "xl"}))

    def test_unknown_warehouse_rejected(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(warehouse={"type": "bigquery"}))

    @pytest.mark.parametrize("warehouse", ["snowflake", "databricks", "redshift_serverless"])
    def test_supported_warehouses(self, warehouse: str):
        spec = PlatformSpec.model_validate(minimal(warehouse={"type": warehouse}))

        assert spec.warehouse.type == warehouse

    def test_unsupported_version_rejected(self):
        with pytest.raises(ValidationError):
            PlatformSpec.model_validate(minimal(version="2"))
