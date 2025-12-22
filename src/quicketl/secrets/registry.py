"""Secrets provider registry and factory.

This module provides a registry for secrets providers and
factory functions for creating provider instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quicketl.secrets.env import EnvSecretsProvider

if TYPE_CHECKING:
    from quicketl.secrets.base import AbstractSecretsProvider


class SecretsProviderRegistry:
    """Registry for secrets providers.

    Manages provider instances and provides factory methods
    for creating providers by name.

    Example:
        >>> registry = SecretsProviderRegistry()
        >>> provider = registry.get("env")
        >>> isinstance(provider, EnvSecretsProvider)
        True
    """

    def __init__(self) -> None:
        """Initialize the provider registry."""
        self._providers: dict[str, AbstractSecretsProvider] = {}

    def get(
        self,
        provider_type: str,
        **config: Any,
    ) -> AbstractSecretsProvider:
        """Get or create a secrets provider by type.

        Args:
            provider_type: The type of provider ('env', 'aws', 'azure', 'vault').
            **config: Configuration options passed to the provider constructor.

        Returns:
            The secrets provider instance.

        Raises:
            ValueError: If the provider type is unknown.
        """
        # Check cache first (simple caching without config)
        if provider_type in self._providers and not config:
            return self._providers[provider_type]

        # Create new provider
        provider = self._create_provider(provider_type, **config)

        # Cache if no config (simple case)
        if not config:
            self._providers[provider_type] = provider

        return provider

    def _create_provider(
        self,
        provider_type: str,
        **config: Any,
    ) -> AbstractSecretsProvider:
        """Create a new provider instance.

        Args:
            provider_type: The type of provider to create.
            **config: Configuration for the provider.

        Returns:
            A new provider instance.

        Raises:
            ValueError: If the provider type is unknown.
        """
        if provider_type == "env":
            return EnvSecretsProvider(**config)

        if provider_type == "aws":
            from quicketl.secrets.aws import AWSSecretsProvider

            return AWSSecretsProvider(**config)

        if provider_type == "azure":
            from quicketl.secrets.azure import AzureSecretsProvider

            return AzureSecretsProvider(**config)

        raise ValueError(
            f"Unknown secrets provider: '{provider_type}'. "
            f"Available providers: env, aws, azure"
        )


# Global registry instance
_registry = SecretsProviderRegistry()


def get_provider(
    provider_type: str = "env",
    **config: Any,
) -> AbstractSecretsProvider:
    """Get a secrets provider by type.

    This is the main entry point for getting secrets providers.

    Args:
        provider_type: The type of provider ('env', 'aws', 'azure').
        **config: Configuration options for the provider.

    Returns:
        The secrets provider instance.

    Example:
        >>> provider = get_provider("env")
        >>> provider.get_secret("MY_VAR")
        'value'
    """
    return _registry.get(provider_type, **config)
