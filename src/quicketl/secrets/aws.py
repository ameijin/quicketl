"""AWS Secrets Manager provider.

Requires: pip install quicketl[secrets-aws]
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from quicketl.secrets.base import AbstractSecretsProvider

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None  # type: ignore[assignment]
    ClientError = Exception  # type: ignore[assignment, misc]


class AWSSecretsProvider(AbstractSecretsProvider):
    """Secrets provider for AWS Secrets Manager.

    Requires boto3 package. Install with: pip install quicketl[secrets-aws]

    Args:
        region_name: AWS region name (e.g., 'us-east-1').
        profile_name: Optional AWS profile name.

    Example:
        >>> provider = AWSSecretsProvider(region_name="us-east-1")
        >>> provider.get_secret("my/database/credentials")
        '{"username": "admin", "password": "secret"}'

        >>> provider.get_secret("my/database/credentials", key="password")
        'secret'
    """

    def __init__(
        self,
        region_name: str | None = None,
        profile_name: str | None = None,
    ) -> None:
        """Initialize AWS Secrets Manager provider.

        Args:
            region_name: AWS region name.
            profile_name: Optional AWS profile name for credentials.

        Raises:
            ImportError: If boto3 is not installed.
        """
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 is required for AWS secrets provider. "
                "Install with: pip install quicketl[secrets-aws]"
            )

        session_kwargs: dict[str, Any] = {}
        if profile_name:
            session_kwargs["profile_name"] = profile_name

        session = boto3.Session(**session_kwargs)
        self._client = session.client("secretsmanager", region_name=region_name)

    def get_secret(
        self,
        path: str,
        *,
        key: str | None = None,
        default: str | None = None,
    ) -> str:
        """Get a secret from AWS Secrets Manager.

        Args:
            path: The secret name or ARN.
            key: Optional key to extract from JSON secret.
            default: Default value if secret not found.

        Returns:
            The secret value, or specific key from JSON secret.

        Raises:
            KeyError: If secret not found and no default provided.
        """
        try:
            response = self._client.get_secret_value(SecretId=path)
            secret_string = response["SecretString"]

            if key is not None:
                # Parse as JSON and extract specific key
                try:
                    secret_data = json.loads(secret_string)
                    return str(secret_data[key])
                except (json.JSONDecodeError, KeyError) as e:
                    raise KeyError(
                        f"Key '{key}' not found in secret '{path}'"
                    ) from e

            return secret_string

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ResourceNotFoundException", "InvalidParameterException"):
                if default is not None:
                    return default
                raise KeyError(f"Secret not found: {path}") from e
            raise
