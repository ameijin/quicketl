"""Abstract base class for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractEmbeddingProvider(ABC):
    """Abstract base class for embedding providers.

    Subclasses must implement the embed method to generate embeddings.
    """

    model: str

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).
        """
        ...

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector.
        """
        return self.embed([text])[0]
