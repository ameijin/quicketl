"""OpenAI embedding provider."""

from __future__ import annotations

from quicketl.transforms.ai.providers.base import AbstractEmbeddingProvider


class OpenAIEmbeddingProvider(AbstractEmbeddingProvider):
    """Embedding provider using OpenAI API.

    Attributes:
        model: OpenAI model name (e.g., 'text-embedding-3-small').
        api_key: OpenAI API key.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize OpenAI embedding provider.

        Args:
            model: OpenAI model name.
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            **kwargs: Additional arguments (ignored).
        """
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        response = self._client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [data.embedding for data in response.data]
