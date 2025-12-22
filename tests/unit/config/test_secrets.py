"""Tests for secrets provider interface and implementations.

This module tests the pluggable secrets management system including:
- Abstract provider interface
- Provider registry
- Environment variable provider (core)
- AWS Secrets Manager provider
- Azure Key Vault provider
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from quicketl.secrets import get_provider, get_secret
from quicketl.secrets.base import AbstractSecretsProvider
from quicketl.secrets.env import EnvSecretsProvider
from quicketl.secrets.registry import SecretsProviderRegistry

# ============================================================================
# Abstract Provider Interface Tests
# ============================================================================


class TestSecretsProviderInterface:
    """Tests for the AbstractSecretsProvider interface."""

    def test_abstract_provider_requires_get_secret_method(self):
        """Abstract provider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AbstractSecretsProvider()  # type: ignore[abstract]

    def test_abstract_provider_defines_get_secret_signature(self):
        """Abstract provider defines get_secret method signature."""
        assert hasattr(AbstractSecretsProvider, "get_secret")
        # Verify it's an abstract method
        assert getattr(AbstractSecretsProvider.get_secret, "__isabstractmethod__", False)

    def test_provider_registry_returns_correct_provider(self):
        """Registry returns the correct provider for each type."""
        registry = SecretsProviderRegistry()

        env_provider = registry.get("env")
        assert isinstance(env_provider, EnvSecretsProvider)

    def test_provider_registry_raises_for_unknown_type(self):
        """Registry raises ValueError for unknown provider type."""
        registry = SecretsProviderRegistry()

        with pytest.raises(ValueError, match="Unknown secrets provider"):
            registry.get("unknown_provider")

    def test_provider_registry_caches_instances(self):
        """Registry caches provider instances for reuse."""
        registry = SecretsProviderRegistry()

        provider1 = registry.get("env")
        provider2 = registry.get("env")

        assert provider1 is provider2


# ============================================================================
# Environment Secrets Provider Tests
# ============================================================================


class TestEnvSecretsProvider:
    """Tests for the EnvSecretsProvider implementation."""

    def test_get_secret_from_env_variable(self, monkeypatch):
        """Get secret from environment variable."""
        monkeypatch.setenv("MY_SECRET", "secret_value")
        provider = EnvSecretsProvider()

        result = provider.get_secret("MY_SECRET")

        assert result == "secret_value"

    def test_get_secret_with_default_value(self, monkeypatch):
        """Get secret uses default when env var missing."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        provider = EnvSecretsProvider()

        result = provider.get_secret("MISSING_VAR", default="fallback")

        assert result == "fallback"

    def test_get_secret_missing_raises_error(self, monkeypatch):
        """Get secret raises error when missing and no default."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        provider = EnvSecretsProvider()

        with pytest.raises(KeyError, match="Secret not found"):
            provider.get_secret("MISSING_VAR")

    def test_get_secret_with_prefix(self, monkeypatch):
        """Get secret with configured prefix."""
        monkeypatch.setenv("APP_DB_PASSWORD", "db_secret")
        provider = EnvSecretsProvider(prefix="APP_")

        result = provider.get_secret("DB_PASSWORD")

        assert result == "db_secret"

    def test_get_secret_empty_value_is_valid(self, monkeypatch):
        """Empty string is a valid secret value."""
        monkeypatch.setenv("EMPTY_SECRET", "")
        provider = EnvSecretsProvider()

        result = provider.get_secret("EMPTY_SECRET")

        assert result == ""


# ============================================================================
# AWS Secrets Manager Provider Tests
# ============================================================================


class TestAWSSecretsProvider:
    """Tests for the AWS Secrets Manager provider."""

    def test_aws_provider_requires_boto3(self):
        """AWS provider requires boto3 package."""
        # This tests that the import works when boto3 is available
        # or raises ImportError with helpful message when not
        try:
            from quicketl.secrets.aws import AWSSecretsProvider

            assert AWSSecretsProvider is not None
        except ImportError as e:
            assert "boto3" in str(e).lower() or "quicketl[secrets-aws]" in str(e)

    def test_get_secret_from_secrets_manager(self):
        """Get secret from AWS Secrets Manager."""
        pytest.importorskip("boto3")
        from quicketl.secrets.aws import AWSSecretsProvider

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": "aws_secret_value"}

        with patch.object(AWSSecretsProvider, "__init__", lambda self, **kw: None):
            provider = AWSSecretsProvider(region_name="us-east-1")
            provider._client = mock_client
            result = provider.get_secret("my/secret/path")

        assert result == "aws_secret_value"
        mock_client.get_secret_value.assert_called_once_with(SecretId="my/secret/path")

    def test_get_json_secret_and_extract_key(self):
        """Get specific key from JSON secret."""
        pytest.importorskip("boto3")
        from quicketl.secrets.aws import AWSSecretsProvider

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"username": "admin", "password": "secret123"}'
        }

        with patch.object(AWSSecretsProvider, "__init__", lambda self, **kw: None):
            provider = AWSSecretsProvider(region_name="us-east-1")
            provider._client = mock_client
            result = provider.get_secret("db/credentials", key="password")

        assert result == "secret123"

    def test_aws_provider_with_custom_region(self):
        """AWS provider uses specified region."""
        boto3 = pytest.importorskip("boto3")

        with patch.object(boto3, "Session") as mock_session:
            mock_session.return_value.client.return_value = MagicMock()
            from quicketl.secrets.aws import AWSSecretsProvider

            AWSSecretsProvider(region_name="eu-west-1")

        mock_session.return_value.client.assert_called_with(
            "secretsmanager", region_name="eu-west-1"
        )

    def test_aws_provider_secret_not_found(self):
        """AWS provider raises error when secret not found."""
        pytest.importorskip("boto3")
        from botocore.exceptions import ClientError

        from quicketl.secrets.aws import AWSSecretsProvider

        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Secret not found"}},
            "GetSecretValue",
        )

        with patch.object(AWSSecretsProvider, "__init__", lambda self, **kw: None):
            provider = AWSSecretsProvider(region_name="us-east-1")
            provider._client = mock_client

            with pytest.raises(KeyError, match="Secret not found"):
                provider.get_secret("nonexistent/secret")


# ============================================================================
# Azure Key Vault Provider Tests
# ============================================================================


class TestAzureSecretsProvider:
    """Tests for the Azure Key Vault provider."""

    def test_azure_provider_requires_azure_packages(self):
        """Azure provider requires azure-identity and azure-keyvault-secrets."""
        try:
            from quicketl.secrets.azure import AzureSecretsProvider

            assert AzureSecretsProvider is not None
        except ImportError as e:
            assert "azure" in str(e).lower() or "quicketl[secrets-azure]" in str(e)

    def test_get_secret_from_key_vault(self):
        """Get secret from Azure Key Vault."""
        pytest.importorskip("azure.identity")
        from quicketl.secrets.azure import AzureSecretsProvider

        mock_secret = MagicMock()
        mock_secret.value = "azure_secret_value"

        mock_client = MagicMock()
        mock_client.get_secret.return_value = mock_secret

        with patch.object(AzureSecretsProvider, "__init__", lambda self, **kw: None):
            provider = AzureSecretsProvider(vault_url="https://myvault.vault.azure.net")
            provider._client = mock_client
            result = provider.get_secret("my-secret")

        assert result == "azure_secret_value"
        mock_client.get_secret.assert_called_once_with("my-secret")

    def test_azure_auth_with_managed_identity(self):
        """Azure provider uses managed identity by default."""
        pytest.importorskip("azure.identity")

        with (
            patch("quicketl.secrets.azure.SecretClient") as mock_client_cls,
            patch("quicketl.secrets.azure.DefaultAzureCredential") as mock_cred,
        ):
            from quicketl.secrets.azure import AzureSecretsProvider

            AzureSecretsProvider(vault_url="https://myvault.vault.azure.net")

        mock_cred.assert_called_once()
        mock_client_cls.assert_called_once()

    def test_azure_provider_secret_not_found(self):
        """Azure provider raises error when secret not found."""
        pytest.importorskip("azure.identity")
        from azure.core.exceptions import ResourceNotFoundError

        from quicketl.secrets.azure import AzureSecretsProvider

        mock_client = MagicMock()
        mock_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")

        with patch.object(AzureSecretsProvider, "__init__", lambda self, **kw: None):
            provider = AzureSecretsProvider(vault_url="https://myvault.vault.azure.net")
            provider._client = mock_client

            with pytest.raises(KeyError, match="Secret not found"):
                provider.get_secret("nonexistent-secret")


# ============================================================================
# Top-Level API Tests
# ============================================================================


class TestSecretsAPI:
    """Tests for the top-level secrets API functions."""

    def test_get_provider_returns_env_by_default(self):
        """get_provider returns EnvSecretsProvider by default."""
        provider = get_provider()
        assert isinstance(provider, EnvSecretsProvider)

    def test_get_provider_with_type(self):
        """get_provider returns correct provider type."""
        provider = get_provider("env")
        assert isinstance(provider, EnvSecretsProvider)

    def test_get_secret_uses_default_provider(self, monkeypatch):
        """get_secret uses default provider when none specified."""
        monkeypatch.setenv("TEST_SECRET", "test_value")

        result = get_secret("TEST_SECRET")

        assert result == "test_value"

    def test_get_secret_with_provider_type(self, monkeypatch):
        """get_secret uses specified provider type."""
        monkeypatch.setenv("TEST_SECRET", "test_value")

        result = get_secret("TEST_SECRET", provider="env")

        assert result == "test_value"
