"""HuggingFace embedding provider using sentence-transformers."""

from __future__ import annotations

from quicketl.transforms.ai.providers.base import AbstractEmbeddingProvider


class HuggingFaceEmbeddingProvider(AbstractEmbeddingProvider):
    """Embedding provider using HuggingFace sentence-transformers.

    Runs models locally for privacy and cost efficiency.

    Attributes:
        model: Model name from HuggingFace Hub.
    """

    def __init__(
        self,
        model: str,
        **kwargs,
    ) -> None:
        """Initialize HuggingFace embedding provider.

        Args:
            model: Model name (e.g., 'all-MiniLM-L6-v2').
            **kwargs: Additional arguments (ignored).
        """
        from sentence_transformers import SentenceTransformer

        self.model = model
        self._model = SentenceTransformer(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]
