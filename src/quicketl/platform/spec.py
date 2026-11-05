"""Platform spec model (platform.yml).

A platform spec describes the data platform you want: which warehouse, which
environments and data layers, the business domains, who can access what,
where raw files land, and how loads are scheduled. Platform templates read
it to generate Terraform, dbt and Airflow code.

The spec is deliberately small. Anything warehouse-specific (sizes, Terraform
provider settings, DAG details) lives in the generated project, where teams
edit it directly.

Example YAML:
    name: acme_data
    warehouse:
      type: snowflake
    domains:
      - name: sales
    roles:
      - name: analyst
        access: {marts: read}
"""

from __future__ import annotations

import ipaddress
import re
from collections import Counter
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PLATFORM_FILE = "platform.yml"
"""Default file name for a platform spec."""

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


class PlatformSpecError(Exception):
    """Raised when a platform spec file cannot be read as a spec."""


def _check_identifier(value: str, what: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(
            f"{what} {value!r} must start with a lowercase letter and use only "
            "lowercase letters, digits and underscores"
        )
    return value


def _check_unique(names: list[str], what: str) -> None:
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate {what}: {', '.join(duplicates)}")


class _SpecModel(BaseModel):
    """Base for spec models: unknown keys are errors, so typos are caught."""

    model_config = ConfigDict(extra="forbid")


WarehouseType = Literal["snowflake", "databricks", "redshift_serverless"]
"""Warehouses a spec can name."""


class Warehouse(_SpecModel):
    """The warehouse the platform runs on.

    Example YAML:
        warehouse:
          type: snowflake
    """

    type: WarehouseType = Field(
        ...,
        description="Warehouse product. Templates exist per warehouse; see the platform docs.",
    )


class Domain(_SpecModel):
    """A business area that owns its own data, such as sales or finance.

    Example YAML:
        domains:
          - name: sales
            description: Orders and customers
    """

    name: str = Field(..., description="Domain name, a lowercase identifier such as `sales`.")
    description: str | None = Field(
        default=None,
        description="One line saying what data the domain holds.",
    )

    @field_validator("name")
    @classmethod
    def _name_is_identifier(cls, value: str) -> str:
        return _check_identifier(value, "domain name")


class Role(_SpecModel):
    """A functional role: a kind of user and the layers it can use.

    Templates turn each role into warehouse roles and grants. For example,
    `access: {marts: read}` lets the role read the marts layer.

    Example YAML:
        roles:
          - name: analyst
            access: {marts: read}
            domains: [sales]
    """

    name: str = Field(..., description="Role name, a lowercase identifier such as `analyst`.")
    description: str | None = Field(
        default=None,
        description="One line saying who gets this role.",
    )
    access: dict[str, Literal["read", "write"]] = Field(
        ...,
        min_length=1,
        description=(
            "Layer name to access level. `read` can query the layer; `write` can also "
            "create and change objects in it."
        ),
    )
    domains: list[str] | None = Field(
        default=None,
        description="Domains the role covers. Leave it out to cover every domain.",
    )

    @field_validator("name")
    @classmethod
    def _name_is_identifier(cls, value: str) -> str:
        return _check_identifier(value, "role name")


class Source(_SpecModel):
    """A set of raw files that lands in S3 and loads into the landing layer.

    Example YAML:
        sources:
          - name: orders
            domain: sales
            location: s3://example-landing/sales/orders/
            format: parquet
    """

    name: str = Field(..., description="Source name, a lowercase identifier such as `orders`.")
    domain: str = Field(..., description="The domain that owns this source.")
    location: str = Field(
        ...,
        description="S3 prefix the files land in, for example `s3://bucket/sales/orders/`.",
    )
    format: Literal["csv", "parquet", "json"] = Field(
        default="parquet",
        description="File format of the landed files.",
    )

    @field_validator("name")
    @classmethod
    def _name_is_identifier(cls, value: str) -> str:
        return _check_identifier(value, "source name")

    @field_validator("location")
    @classmethod
    def _location_is_s3(cls, value: str) -> str:
        if not value.startswith("s3://"):
            raise ValueError(f"source location {value!r} must start with s3://")
        return value


class SSO(_SpecModel):
    """Single sign-on (SSO) for warehouse users.

    Example YAML:
        sso:
          provider: okta
    """

    provider: Literal["okta", "none"] = Field(
        default="none",
        description="Identity provider for sign-in. `none` means templates set up no SSO.",
    )


class Network(_SpecModel):
    """Network access rules for the warehouse.

    Example YAML:
        network:
          allowed_ips: [203.0.113.0/24]
    """

    allowed_ips: list[str] = Field(
        default_factory=list,
        description=(
            "IP addresses or CIDR ranges allowed to connect. Empty means templates "
            "add no network policy."
        ),
    )

    @field_validator("allowed_ips")
    @classmethod
    def _valid_networks(cls, values: list[str]) -> list[str]:
        for value in values:
            try:
                ipaddress.ip_network(value)
            except ValueError:
                raise ValueError(
                    f"{value!r} is not an IP address or CIDR range "
                    "(a range like 10.0.0.1/24 must be written 10.0.0.0/24)"
                ) from None
        return values


class Orchestrator(_SpecModel):
    """How scheduled loads and dbt runs are orchestrated.

    Example YAML:
        orchestrator:
          type: airflow
          hosting: mwaa
          schedule: "@daily"
    """

    type: Literal["airflow"] = Field(default="airflow", description="Orchestrator product.")
    hosting: Literal["mwaa"] = Field(
        default="mwaa",
        description="Where the orchestrator runs. `mwaa` is Amazon Managed Workflows for Apache Airflow.",
    )
    schedule: str = Field(
        default="@daily",
        description="Default schedule for generated DAGs, as an Airflow preset or cron expression.",
    )


class PlatformSpec(_SpecModel):
    """The whole platform spec, the contents of platform.yml.

    Example YAML:
        name: acme_data
        warehouse:
          type: snowflake
        environments: [dev, prod]
        domains:
          - name: sales
    """

    version: Literal["1"] = Field(default="1", description="Spec format version.")
    name: str = Field(
        ...,
        description="Platform name, a lowercase identifier. Templates use it as a prefix for objects.",
    )
    warehouse: Warehouse = Field(..., description="The warehouse the platform runs on.")
    environments: list[str] = Field(
        default_factory=lambda: ["dev", "prod"],
        min_length=1,
        description="Environment names. Each one gets its own databases and grants.",
    )
    layers: list[str] = Field(
        default_factory=lambda: ["raw", "staging", "marts"],
        min_length=1,
        description="Data layers in order. Sources load into the first one.",
    )
    domains: list[Domain] = Field(
        ...,
        min_length=1,
        description="Business domains, each owning its own data.",
    )
    roles: list[Role] = Field(default_factory=list, description="Functional roles.")
    sso: SSO = Field(default_factory=SSO, description="Single sign-on settings.")
    network: Network = Field(default_factory=Network, description="Network access rules.")
    sources: list[Source] = Field(default_factory=list, description="Raw file sources in S3.")
    orchestrator: Orchestrator = Field(
        default_factory=Orchestrator,
        description="Scheduling settings.",
    )

    @field_validator("name")
    @classmethod
    def _name_is_identifier(cls, value: str) -> str:
        return _check_identifier(value, "platform name")

    @field_validator("environments", "layers")
    @classmethod
    def _names_are_unique_identifiers(cls, values: list[str], info) -> list[str]:
        what = info.field_name.rstrip("s")
        for value in values:
            _check_identifier(value, f"{what} name")
        _check_unique(values, info.field_name)
        return values

    @model_validator(mode="after")
    def _check_references(self) -> PlatformSpec:
        _check_unique([d.name for d in self.domains], "domains")
        _check_unique([r.name for r in self.roles], "roles")
        _check_unique([s.name for s in self.sources], "sources")

        layers = set(self.layers)
        domains = {d.name for d in self.domains}
        problems = []
        for role in self.roles:
            problems += [
                f"role {role.name!r} refers to unknown layer {layer!r}"
                for layer in role.access
                if layer not in layers
            ]
            problems += [
                f"role {role.name!r} refers to unknown domain {domain!r}"
                for domain in role.domains or []
                if domain not in domains
            ]
        problems += [
            f"source {source.name!r} refers to unknown domain {source.domain!r}"
            for source in self.sources
            if source.domain not in domains
        ]
        if problems:
            raise ValueError("; ".join(problems))
        return self

    @property
    def landing_layer(self) -> str:
        """The layer raw sources load into: the first entry in `layers`."""
        return self.layers[0]


def load_platform_spec(path: Path | str) -> PlatformSpec:
    """Load and validate a platform spec from a YAML file.

    Args:
        path: Path to the platform.yml file.

    Returns:
        The validated spec.

    Raises:
        PlatformSpecError: If the file is missing, empty, not YAML, or not a mapping.
        pydantic.ValidationError: If the contents break the spec rules.

    Example:
        >>> spec = load_platform_spec("platform.yml")
        >>> spec.warehouse.type
        'snowflake'
    """
    path = Path(path)
    if not path.is_file():
        raise PlatformSpecError(f"Platform spec not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise PlatformSpecError(f"{path} is not valid YAML: {e}") from e

    if raw is None:
        raise PlatformSpecError(f"{path} is empty")
    if not isinstance(raw, dict):
        raise PlatformSpecError(f"{path} must be a YAML mapping of keys to values")

    return PlatformSpec.model_validate(raw)
