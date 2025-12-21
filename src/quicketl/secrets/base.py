"""Abstract base class for secrets providers.

This module defines the interface that all secrets providers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractSecretsProvider(ABC):
    """Abstract base class for secrets providers.

    All secrets providers must implement this interface to enable
    pluggable secrets management across different backends.

    Example:
        >>> class MyProvider(AbstractSecretsProvider):
        ...     def get_secret(self, path: str, **kwargs) -> str:
        ...         return "secret_value"
    """

    @abstractmethod
    def get_secret(
        self,
        path: str,
        *,
        key: str | None = None,
        default: str | None = None,
    ) -> str:
        """Retrieve a secret value by path.

        Args:
            path: The path or name of the secret to retrieve.
            key: Optional key to extract from a JSON secret.
            default: Optional default value if secret not found.

        Returns:
            The secret value as a string.

        Raises:
            KeyError: If the secret is not found and no default is provided.
        """
        ...
