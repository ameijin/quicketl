"""Environment configuration with inheritance support.

Enables environment-based configuration (dev, staging, prod) with
inheritance from a base environment.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    """Configuration for a specific environment.

    Attributes:
        engine: The default engine/backend to use.
        quality: Quality check configuration.
        logging: Logging configuration.
        secrets: Secrets provider configuration.
        extra: Additional environment-specific settings.
    """

    engine: str = "duckdb"
    quality: dict[str, Any] = Field(default_factory=dict)
    logging: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two configuration dictionaries.

    The override values take precedence. Nested dictionaries are merged
    recursively, while other values (including lists) are replaced.

    Args:
        base: The base configuration.
        override: The override configuration.

    Returns:
        A new dictionary with merged values.

    Example:
        >>> base = {"a": 1, "nested": {"x": 1, "y": 2}}
        >>> override = {"a": 2, "nested": {"y": 3, "z": 4}}
        >>> merge_configs(base, override)
        {'a': 2, 'nested': {'x': 1, 'y': 3, 'z': 4}}
    """
    result = dict(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            # Recursively merge nested dicts
            result[key] = merge_configs(result[key], value)
        else:
            # Override with new value
            result[key] = value

    return result


def load_environment(
    config: dict[str, Any],
    env_name: str | None = None,
    *,
    _visited: set[str] | None = None,
) -> EnvironmentConfig:
    """Load an environment configuration with inheritance resolution.

    Args:
        config: The full configuration containing environments.
        env_name: The environment name to load. If None, uses QUICKETL_ENV.

    Returns:
        The resolved EnvironmentConfig.

    Raises:
        KeyError: If the environment is not found.
        ValueError: If circular inheritance is detected.

    Example:
        >>> config = {
        ...     "environments": {
        ...         "base": {"engine": "duckdb"},
        ...         "prod": {"extends": "base", "engine": "snowflake"}
        ...     }
        ... }
        >>> env = load_environment(config, "prod")
        >>> env.engine
        'snowflake'
    """
    # Default to QUICKETL_ENV environment variable
    if env_name is None:
        env_name = os.environ.get("QUICKETL_ENV", "dev")

    environments = config.get("environments", {})

    if env_name not in environments:
        raise KeyError(f"Environment not found: {env_name}")

    # Track visited environments for circular detection
    if _visited is None:
        _visited = set()

    if env_name in _visited:
        raise ValueError(f"Circular environment inheritance detected: {env_name}")

    _visited.add(env_name)

    env_config = environments[env_name]

    # Check for inheritance
    extends = env_config.get("extends")
    if extends:
        # Recursively load parent environment
        parent_env = load_environment(config, extends, _visited=_visited)
        parent_dict = parent_env.model_dump()

        # Remove 'extends' key before merging
        child_dict = {k: v for k, v in env_config.items() if k != "extends"}

        # Merge parent and child
        merged = merge_configs(parent_dict, child_dict)
        return EnvironmentConfig.model_validate(merged)

    return EnvironmentConfig.model_validate(env_config)
