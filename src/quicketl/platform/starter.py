"""Starter platform spec written by `quicketl platform init`."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quicketl.platform.spec import WarehouseType

_STARTER = """\
# Platform spec: describes the data platform you want.
# Check it with: quicketl platform validate
# Every field: https://quicketl.com/platform/spec/
version: "1"

# Lowercase letters, digits and underscores. Used as a prefix for warehouse objects.
name: {name}

warehouse:
  type: {warehouse}

# Each environment gets its own databases and grants.
environments: [dev, prod]

# Data layers in order. Sources load into the first one.
layers: [raw, staging, marts]

# Business areas that own their own data. Rename or add your own.
domains:
  - name: core
    description: Shared data used across the business

# Kinds of users and what they can do in each layer (read or write).
roles:
  - name: loader
    description: Service user that loads raw files
    access: {{raw: write}}
  - name: transformer
    description: Service user that runs dbt
    access: {{raw: read, staging: write, marts: write}}
  - name: analyst
    description: People who query the finished data
    access: {{marts: read}}

# Single sign-on: okta or none.
sso:
  provider: none

# IP addresses or CIDR ranges allowed to connect. Empty means no network policy.
network:
  allowed_ips: []

# Raw files that land in S3. Example:
#   - name: orders
#     domain: core
#     location: s3://your-landing-bucket/core/orders/
#     format: parquet
sources: []

orchestrator:
  type: airflow
  hosting: mwaa
  schedule: "@daily"
"""


def default_platform_name(folder_name: str) -> str:
    """Turn a folder name into a valid platform name.

    Lowercases it, replaces anything other than letters, digits and
    underscores with `_`, and adds a `p_` prefix if it would start with a
    digit.

    Args:
        folder_name: Name of the project folder, such as `acme-data`.

    Returns:
        A lowercase identifier, such as `acme_data`. Falls back to
        `my_platform` if nothing usable is left.

    Example:
        >>> default_platform_name("2026 Platform")
        'p_2026_platform'
    """
    name = re.sub(r"[^a-z0-9_]+", "_", folder_name.lower()).strip("_")
    if not name:
        return "my_platform"
    if not name[0].isalpha():
        name = f"p_{name}"
    return name


def render_starter_spec(name: str, warehouse: WarehouseType) -> str:
    """Return the text of a commented starter platform.yml.

    Args:
        name: Platform name. It is not checked here; validate the result.
        warehouse: Warehouse type.

    Returns:
        YAML text with comments explaining each section.
    """
    return _STARTER.format(name=name, warehouse=warehouse)
