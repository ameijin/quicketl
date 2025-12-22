"""Connection profile management.

Enables reusable connection profiles that can be referenced
in pipeline source/sink configurations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConnectionProfile(BaseModel):
    """A reusable connection profile.

    Profiles can be defined in quicketl.yml and referenced in
    pipeline configurations by name.

    Attributes:
        type: The connection type (e.g., 'snowflake', 'postgres').
        Extra attributes are allowed and stored as connection parameters.
    """

    type: str
    # Allow any additional connection parameters
    model_config = {"extra": "allow"}

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to extra fields."""
        # Pydantic v2 stores extra fields in model_extra property
        if hasattr(self, "model_extra") and self.model_extra and name in self.model_extra:
            return self.model_extra[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


class ProfileRegistry:
    """Registry for connection profiles.

    Provides lookup and caching for connection profiles.

    Example:
        >>> registry = ProfileRegistry({
        ...     "snowflake_prod": {"type": "snowflake", "account": "myaccount"}
        ... })
        >>> profile = registry.get("snowflake_prod")
        >>> profile.account
        'myaccount'
    """

    def __init__(self, profiles: dict[str, dict[str, Any]]) -> None:
        """Initialize the profile registry.

        Args:
            profiles: Dictionary of profile name to profile config.
        """
        self._raw_profiles = profiles
        self._cached_profiles: dict[str, ConnectionProfile] = {}

    def get(self, name: str) -> ConnectionProfile:
        """Get a connection profile by name.

        Args:
            name: The profile name.

        Returns:
            The ConnectionProfile instance.

        Raises:
            KeyError: If the profile is not found.
        """
        if name in self._cached_profiles:
            return self._cached_profiles[name]

        if name not in self._raw_profiles:
            raise KeyError(f"Profile not found: {name}")

        profile = ConnectionProfile.model_validate(self._raw_profiles[name])
        self._cached_profiles[name] = profile
        return profile

    def list(self) -> list[str]:
        """List all available profile names.

        Returns:
            List of profile names.
        """
        return list(self._raw_profiles.keys())


def load_profiles(
    config: dict[str, Any],
    *,
    secrets_provider: str | None = None,
    secrets_config: dict[str, Any] | None = None,
) -> ProfileRegistry:
    """Load connection profiles from configuration.

    Args:
        config: Configuration containing 'profiles' key.
        secrets_provider: Optional secrets provider for resolving references.
        secrets_config: Optional secrets provider configuration.

    Returns:
        A ProfileRegistry with loaded profiles.

    Example:
        >>> config = {
        ...     "profiles": {
        ...         "postgres_prod": {"type": "postgres", "host": "localhost"}
        ...     }
        ... }
        >>> profiles = load_profiles(config)
        >>> profile = profiles.get("postgres_prod")
    """
    profiles_config = config.get("profiles", {})

    # Resolve any secret references in profile values
    if secrets_provider and profiles_config:
        from quicketl.config.loader import substitute_variables

        profiles_config = substitute_variables(
            profiles_config,
            {},
            secrets_provider=secrets_provider,
            secrets_config=secrets_config or {},
        )

    return ProfileRegistry(profiles_config)
