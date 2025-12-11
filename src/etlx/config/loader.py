"""YAML configuration loading with variable substitution.

Supports ${VAR} syntax for environment variable references.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from etlx.config.models import PipelineConfig


def substitute_variables(
    value: Any,
    variables: dict[str, str] | None = None,
) -> Any:
    """Recursively substitute ${VAR} placeholders with values.

    Variables are resolved in this order:
    1. Explicit variables dict
    2. Environment variables

    Args:
        value: The value to process (can be str, dict, list, or other)
        variables: Optional mapping of variable names to values

    Returns:
        The value with all ${VAR} placeholders substituted

    Example:
        >>> substitute_variables("${HOME}/data", {"HOME": "/users/alice"})
        '/users/alice/data'
    """
    variables = variables or {}

    if isinstance(value, str):
        # Pattern matches ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

        def replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default = match.group(2)

            # Check explicit variables first, then environment
            if var_name in variables:
                return variables[var_name]
            if var_name in os.environ:
                return os.environ[var_name]
            if default is not None:
                return default

            # Return original if not found (will likely fail validation later)
            return match.group(0)

        return re.sub(pattern, replace, value)

    if isinstance(value, dict):
        return {k: substitute_variables(v, variables) for k, v in value.items()}

    if isinstance(value, list):
        return [substitute_variables(item, variables) for item in value]

    return value


def load_yaml_with_variables(
    path: Path | str,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Load a YAML file and substitute variables.

    Args:
        path: Path to the YAML file
        variables: Optional mapping of variable names to values

    Returns:
        The parsed YAML content with variables substituted

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML

    Example:
        >>> config = load_yaml_with_variables(
        ...     "pipeline.yml",
        ...     variables={"RUN_DATE": "2025-01-01"}
        ... )
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        return {}

    return substitute_variables(raw_config, variables)


def load_pipeline_config(
    path: Path | str,
    variables: dict[str, str] | None = None,
) -> PipelineConfig:
    """Load and validate a pipeline configuration from YAML.

    Args:
        path: Path to the pipeline YAML file
        variables: Optional mapping of variable names to values

    Returns:
        A validated PipelineConfig instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
        pydantic.ValidationError: If the config doesn't match the schema

    Example:
        >>> config = load_pipeline_config(
        ...     "pipelines/daily_sales.yml",
        ...     variables={"RUN_DATE": "2025-01-01"}
        ... )
        >>> print(config.name)
        'daily_sales_etl'
    """
    config_dict = load_yaml_with_variables(path, variables)
    return PipelineConfig.model_validate(config_dict)
