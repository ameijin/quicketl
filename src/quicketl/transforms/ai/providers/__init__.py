"""Embedding provider registry.

Provides factory function to create embedding providers by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from quicketl.transforms.ai.providers.base import AbstractEmbeddingProvider


def get_provider(
    provider: str,
    model: str,
    **kwargs: Any,
) -> AbstractEmbeddingProvider:
    """Get an embedding provider by name.

    Args:
        provider: Provider name ('openai', 'huggingface').
        model: Model name/identifier.
        **kwargs: Provider-specific configuration.

    Returns:
        The embedding provider instance.

    Raises:
        ValueError: If provider name is unknown.
    """
    match provider:
        case "openai":
            from quicketl.transforms.ai.providers.openai import OpenAIEmbeddingProvider

            return OpenAIEmbeddingProvider(model=model, **kwargs)
        case "huggingface":
            from quicketl.transforms.ai.providers.huggingface import (
                HuggingFaceEmbeddingProvider,
            )

            return HuggingFaceEmbeddingProvider(model=model, **kwargs)
        case _:
            raise ValueError(f"Unknown embedding provider: {provider}")
