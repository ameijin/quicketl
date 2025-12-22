"""Project-level configuration (quicketl.yml).

Defines the structure and loading of project configuration files
that contain environment, profile, and other global settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project-level configuration model.

    This represents the quicketl.yml file at the root of a project.

    Attributes:
        version: Configuration schema version.
        defaults: Default settings applied to all pipelines.
        environments: Environment definitions with inheritance.
        profiles: Connection profile definitions.
        secrets: Secrets provider configuration.
        plugins: List of plugin packages or paths.
        telemetry: Telemetry/observability configuration.
        logging: Logging configuration.
    """

    version: str = "1.0"
    defaults: dict[str, Any] = Field(default_factory=dict)
    environments: dict[str, dict[str, Any]] = Field(default_factory=dict)
    profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)
    plugins: list[str | dict[str, str]] = Field(default_factory=list)
    telemetry: dict[str, Any] = Field(default_factory=dict)
    logging: dict[str, Any] = Field(default_factory=dict)


def load_project_config(
    path: Path | str,
    *,
    variables: dict[str, str] | None = None,
) -> ProjectConfig:
    """Load project configuration from a YAML file.

    If the file doesn't exist, returns a ProjectConfig with defaults.

    Args:
        path: Path to the quicketl.yml file.
        variables: Optional variables for substitution.

    Returns:
        A validated ProjectConfig instance.

    Example:
        >>> config = load_project_config("quicketl.yml")
        >>> config.version
        '1.0'
    """
    path = Path(path)

    if not path.exists():
        # Return default config if file doesn't exist
        return ProjectConfig()

    with path.open("r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        return ProjectConfig()

    # Apply variable substitution if provided
    if variables:
        from quicketl.config.loader import substitute_variables

        raw_config = substitute_variables(raw_config, variables)

    return ProjectConfig.model_validate(raw_config)


def find_project_config(start_path: Path | str | None = None) -> Path | None:
    """Find the nearest quicketl.yml file by searching up the directory tree.

    Args:
        start_path: Starting directory for the search. Defaults to cwd.

    Returns:
        Path to quicketl.yml if found, None otherwise.

    Example:
        >>> path = find_project_config()
        >>> if path:
        ...     print(f"Found project config at: {path}")
    """
    start_path = Path.cwd() if start_path is None else Path(start_path)

    current = start_path.resolve()

    while current != current.parent:
        config_path = current / "quicketl.yml"
        if config_path.exists():
            return config_path

        # Also check for quicketl.yaml
        config_path = current / "quicketl.yaml"
        if config_path.exists():
            return config_path

        current = current.parent

    return None
