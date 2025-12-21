"""YAML configuration loading with variable substitution.

Supports ${VAR} syntax for environment variable references
and ${secret:path} syntax for secrets provider lookups.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from quicketl.config.models import PipelineConfig
from quicketl.config.workflow import WorkflowConfig

if TYPE_CHECKING:
    from quicketl.secrets.base import AbstractSecretsProvider


def substitute_variables(
    value: Any,
    variables: dict[str, str] | None = None,
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> Any:
    """Recursively substitute ${VAR} and ${secret:path} placeholders with values.

    Variables are resolved in this order:
    1. Explicit variables dict
    2. Environment variables

    Secrets use the ${secret:path} syntax and are resolved via secrets providers.

    Args:
        value: The value to process (can be str, dict, list, or other)
        variables: Optional mapping of variable names to values
        secrets_provider: Secrets provider type ('env', 'aws', 'azure')
        secrets_config: Configuration options for the secrets provider

    Returns:
        The value with all ${VAR} and ${secret:path} placeholders substituted

    Raises:
        KeyError: If a secret is not found and no default is provided

    Example:
        >>> substitute_variables("${HOME}/data", {"HOME": "/users/alice"})
        '/users/alice/data'

        >>> substitute_variables(
        ...     "${secret:DB_PASSWORD}",
        ...     {},
        ...     secrets_provider="env"
        ... )
        'password_from_env'
    """
    variables = variables or {}
    secrets_config = secrets_config or {}

    # Lazy load secrets provider only when needed
    _secrets_provider_instance: AbstractSecretsProvider | None = None

    def get_secrets_provider() -> AbstractSecretsProvider:
        nonlocal _secrets_provider_instance
        if _secrets_provider_instance is None:
            from quicketl.secrets import get_provider

            provider_type = secrets_provider or "env"
            _secrets_provider_instance = get_provider(provider_type, **secrets_config)
        return _secrets_provider_instance

    if isinstance(value, str):
        # First handle ${secret:path} or ${secret:path:-default} syntax
        secret_pattern = r"\$\{secret:([^}:]+)(?::-([^}]*))?\}"

        def replace_secret(match: re.Match[str]) -> str:
            secret_path = match.group(1)
            default = match.group(2)

            try:
                provider = get_secrets_provider()
                return provider.get_secret(secret_path, default=default)
            except KeyError:
                if default is not None:
                    return default
                raise

        # Check if there are any secret references
        if "${secret:" in value:
            value = re.sub(secret_pattern, replace_secret, value)

        # Then handle regular ${VAR} or ${VAR:-default} syntax
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

        def replace_var(match: re.Match[str]) -> str:
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

        return re.sub(pattern, replace_var, value)

    if isinstance(value, dict):
        return {
            k: substitute_variables(
                v, variables, secrets_provider=secrets_provider, secrets_config=secrets_config
            )
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            substitute_variables(
                item, variables, secrets_provider=secrets_provider, secrets_config=secrets_config
            )
            for item in value
        ]

    return value


def load_yaml_with_variables(
    path: Path | str,
    variables: dict[str, str] | None = None,
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a YAML file and substitute variables.

    Args:
        path: Path to the YAML file
        variables: Optional mapping of variable names to values
        secrets_provider: Secrets provider type ('env', 'aws', 'azure')
        secrets_config: Configuration options for the secrets provider

    Returns:
        The parsed YAML content with variables substituted

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
        KeyError: If a secret is not found and no default is provided

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

    return substitute_variables(
        raw_config,
        variables,
        secrets_provider=secrets_provider,
        secrets_config=secrets_config,
    )


def _resolve_profiles(
    config_dict: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve profile references in source/sink configurations.

    When source or sink has a 'profile' key, look up the profile and merge
    its values into the config. Profile values provide defaults; explicit
    source/sink values take precedence.

    Args:
        config_dict: The pipeline configuration dictionary.
        profiles: Dictionary of profile name to profile config.
        secrets_provider: Secrets provider for resolving profile secrets.
        secrets_config: Secrets provider configuration.

    Returns:
        The config dict with profiles resolved.
    """
    result = dict(config_dict)

    # Resolve source profile
    if "source" in result and isinstance(result["source"], dict):
        result["source"] = _resolve_profile_in_config(
            result["source"],
            profiles,
            secrets_provider=secrets_provider,
            secrets_config=secrets_config,
        )

    # Resolve sink profile
    if "sink" in result and isinstance(result["sink"], dict):
        result["sink"] = _resolve_profile_in_config(
            result["sink"],
            profiles,
            secrets_provider=secrets_provider,
            secrets_config=secrets_config,
        )

    return result


def _resolve_profile_in_config(
    config: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve a profile reference in a source/sink config.

    Args:
        config: The source or sink configuration.
        profiles: Dictionary of profile name to profile config.
        secrets_provider: Secrets provider for resolving profile secrets.
        secrets_config: Secrets provider configuration.

    Returns:
        The config with profile values merged in.
    """
    profile_name = config.get("profile")
    if not profile_name or profile_name not in profiles:
        return config

    # Get and resolve secrets in the profile
    profile = profiles[profile_name]
    resolved_profile = substitute_variables(
        profile,
        {},
        secrets_provider=secrets_provider,
        secrets_config=secrets_config,
    )

    # Merge: profile values are defaults, explicit config values take precedence
    result = dict(resolved_profile)
    for key, value in config.items():
        if key != "profile":  # Don't include the profile key itself
            result[key] = value

    return result


def load_pipeline_config(
    path: Path | str,
    variables: dict[str, str] | None = None,
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> PipelineConfig:
    """Load and validate a pipeline configuration from YAML.

    Args:
        path: Path to the pipeline YAML file
        variables: Optional mapping of variable names to values
        secrets_provider: Secrets provider type ('env', 'aws', 'azure')
        secrets_config: Configuration options for the secrets provider
        profiles: Connection profiles to resolve 'profile' references

    Returns:
        A validated PipelineConfig instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
        pydantic.ValidationError: If the config doesn't match the schema
        KeyError: If a secret is not found and no default is provided

    Example:
        >>> config = load_pipeline_config(
        ...     "pipelines/daily_sales.yml",
        ...     variables={"RUN_DATE": "2025-01-01"}
        ... )
        >>> print(config.name)
        'daily_sales_etl'
    """
    config_dict = load_yaml_with_variables(
        path,
        variables,
        secrets_provider=secrets_provider,
        secrets_config=secrets_config,
    )

    # Resolve profile references in source/sink
    if profiles:
        config_dict = _resolve_profiles(
            config_dict,
            profiles,
            secrets_provider=secrets_provider,
            secrets_config=secrets_config,
        )

    return PipelineConfig.model_validate(config_dict)


def load_workflow_config(
    path: Path | str,
    variables: dict[str, str] | None = None,
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> WorkflowConfig:
    """Load and validate a workflow configuration from YAML.

    Args:
        path: Path to the workflow YAML file
        variables: Optional mapping of variable names to values
        secrets_provider: Secrets provider type ('env', 'aws', 'azure')
        secrets_config: Configuration options for the secrets provider

    Returns:
        A validated WorkflowConfig instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
        pydantic.ValidationError: If the config doesn't match the schema
        KeyError: If a secret is not found and no default is provided

    Example:
        >>> config = load_workflow_config(
        ...     "workflows/medallion.yml",
        ...     variables={"RUN_DATE": "2025-01-01"}
        ... )
        >>> print(config.name)
        'medallion_etl'
    """
    config_dict = load_yaml_with_variables(
        path,
        variables,
        secrets_provider=secrets_provider,
        secrets_config=secrets_config,
    )
    return WorkflowConfig.model_validate(config_dict)
