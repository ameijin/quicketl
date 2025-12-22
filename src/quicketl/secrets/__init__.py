"""Secrets management for QuickETL.

This module provides a pluggable secrets management system with
support for multiple backends:

- **env**: Environment variables (default, no dependencies)
- **aws**: AWS Secrets Manager (requires quicketl[secrets-aws])
- **azure**: Azure Key Vault (requires quicketl[secrets-azure])

Example:
    >>> from quicketl.secrets import get_secret, get_provider
    >>>
    >>> # Simple usage with default env provider
    >>> password = get_secret("DATABASE_PASSWORD")
    >>>
    >>> # Using AWS Secrets Manager
    >>> password = get_secret(
    ...     "db/credentials",
    ...     provider="aws",
    ...     key="password"
    ... )
    >>>
    >>> # Get a provider for multiple lookups
    >>> provider = get_provider("azure", vault_url="https://myvault.vault.azure.net")
    >>> api_key = provider.get_secret("api-key")
"""

from __future__ import annotations

from typing import Any

from quicketl.secrets.base import AbstractSecretsProvider
from quicketl.secrets.env import EnvSecretsProvider
from quicketl.secrets.registry import SecretsProviderRegistry, get_provider

__all__ = [
    "AbstractSecretsProvider",
    "EnvSecretsProvider",
    "SecretsProviderRegistry",
    "get_provider",
    "get_secret",
]


def get_secret(
    path: str,
    *,
    provider: str = "env",
    key: str | None = None,
    default: str | None = None,
    **provider_config: Any,
) -> str:
    """Get a secret value using the specified provider.

    This is a convenience function for one-off secret lookups.
    For multiple lookups, use get_provider() to get a provider instance.

    Args:
        path: The path or name of the secret.
        provider: The provider type ('env', 'aws', 'azure').
        key: Optional key to extract from a JSON secret.
        default: Optional default value if secret not found.
        **provider_config: Additional configuration for the provider.

    Returns:
        The secret value.

    Raises:
        KeyError: If the secret is not found and no default provided.

    Example:
        >>> import os
        >>> os.environ["MY_SECRET"] = "secret_value"
        >>> get_secret("MY_SECRET")
        'secret_value'

        >>> get_secret("MISSING", default="fallback")
        'fallback'
    """
    secrets_provider = get_provider(provider, **provider_config)
    return secrets_provider.get_secret(path, key=key, default=default)
