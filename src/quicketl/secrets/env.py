"""Environment variable secrets provider.

This is the default provider that reads secrets from environment variables.
No additional dependencies required.
"""

from __future__ import annotations

import os

from quicketl.secrets.base import AbstractSecretsProvider


class EnvSecretsProvider(AbstractSecretsProvider):
    """Secrets provider that reads from environment variables.

    This is the default provider requiring no additional dependencies.
    Useful for local development and CI/CD environments.

    Args:
        prefix: Optional prefix to prepend to all secret names.

    Example:
        >>> provider = EnvSecretsProvider()
        >>> os.environ["MY_SECRET"] = "secret_value"
        >>> provider.get_secret("MY_SECRET")
        'secret_value'

        >>> provider = EnvSecretsProvider(prefix="APP_")
        >>> os.environ["APP_DB_PASSWORD"] = "password"
        >>> provider.get_secret("DB_PASSWORD")
        'password'
    """

    def __init__(self, prefix: str = "") -> None:
        """Initialize the environment secrets provider.

        Args:
            prefix: Optional prefix to prepend to all secret names.
        """
        self.prefix = prefix

    def get_secret(
        self,
        path: str,
        *,
        _key: str | None = None,
        default: str | None = None,
    ) -> str:
        """Get a secret from environment variables.

        Args:
            path: The environment variable name (without prefix).
            _key: Ignored for env provider (interface compatibility).
            default: Default value if variable not set.

        Returns:
            The environment variable value.

        Raises:
            KeyError: If variable not found and no default provided.
        """
        full_name = f"{self.prefix}{path}"
        value = os.environ.get(full_name)

        if value is not None:
            return value

        if default is not None:
            return default

        raise KeyError(f"Secret not found: {full_name}")
