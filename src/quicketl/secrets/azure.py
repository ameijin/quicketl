"""Azure Key Vault secrets provider.

Requires: pip install quicketl[secrets-azure]
"""

from __future__ import annotations

from quicketl.secrets.base import AbstractSecretsProvider

try:
    from azure.core.exceptions import ResourceNotFoundError
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False
    DefaultAzureCredential = None  # type: ignore[assignment, misc]
    SecretClient = None  # type: ignore[assignment, misc]
    ResourceNotFoundError = Exception  # type: ignore[assignment, misc]


class AzureSecretsProvider(AbstractSecretsProvider):
    """Secrets provider for Azure Key Vault.

    Requires azure-identity and azure-keyvault-secrets packages.
    Install with: pip install quicketl[secrets-azure]

    Args:
        vault_url: The URL of the Azure Key Vault (e.g., 'https://myvault.vault.azure.net').

    Example:
        >>> provider = AzureSecretsProvider(vault_url="https://myvault.vault.azure.net")
        >>> provider.get_secret("my-database-password")
        'secret_value'
    """

    def __init__(self, vault_url: str) -> None:
        """Initialize Azure Key Vault provider.

        Args:
            vault_url: The URL of the Azure Key Vault.

        Raises:
            ImportError: If azure packages are not installed.
        """
        if not HAS_AZURE:
            raise ImportError(
                "azure-identity and azure-keyvault-secrets are required for Azure secrets provider. "
                "Install with: pip install quicketl[secrets-azure]"
            )

        credential = DefaultAzureCredential()
        self._client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(
        self,
        path: str,
        *,
        _key: str | None = None,
        default: str | None = None,
    ) -> str:
        """Get a secret from Azure Key Vault.

        Args:
            path: The secret name in Key Vault.
            _key: Ignored for Azure provider (interface compatibility).
            default: Default value if secret not found.

        Returns:
            The secret value.

        Raises:
            KeyError: If secret not found and no default provided.
        """
        try:
            secret = self._client.get_secret(path)
            return secret.value or ""

        except ResourceNotFoundError as e:
            if default is not None:
                return default
            raise KeyError(f"Secret not found: {path}") from e
