"""Embedding transform for generating vector representations of text.

Supports multiple embedding providers (OpenAI, HuggingFace) with
batching and retry logic.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from quicketl.transforms.ai.providers import get_provider

if TYPE_CHECKING:
    import ibis.expr.types as ir

    from quicketl.transforms.ai.providers.base import AbstractEmbeddingProvider


class EmbedTransform(BaseModel):
    """Transform that generates embeddings for text columns.

    Attributes:
        provider: Embedding provider ('openai', 'huggingface').
        model: Model name for the provider.
        input_columns: Columns to embed (concatenated if multiple).
        output_column: Name for the embedding column.
        batch_size: Number of texts to embed per API call.
        api_key: API key for the provider (if required).
        max_retries: Maximum retry attempts on failure.
        retry_delay: Delay between retries in seconds.

    Example YAML:
        - op: embed
          provider: openai
          model: text-embedding-3-small
          input_columns: [title, description]
          output_column: embedding
          batch_size: 100
          api_key: ${secret:openai/api_key}
    """

    provider: str = Field(..., description="Embedding provider name")
    model: str = Field(..., description="Model name")
    input_columns: list[str] = Field(..., description="Columns to embed")
    output_column: str = Field(default="embedding", description="Output column name")
    batch_size: int = Field(default=100, description="Batch size for API calls", gt=0)
    api_key: str | None = Field(default=None, description="API key if required")
    max_retries: int = Field(default=3, description="Max retry attempts", ge=0)
    retry_delay: float = Field(default=1.0, description="Delay between retries", ge=0)

    model_config = {"extra": "forbid"}

    _provider_instance: AbstractEmbeddingProvider | None = None

    def _get_provider(self) -> AbstractEmbeddingProvider:
        """Get or create the embedding provider instance."""
        if self._provider_instance is None:
            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._provider_instance = get_provider(
                provider=self.provider,
                model=self.model,
                **kwargs,
            )
        return self._provider_instance

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text with retry logic.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        return self._embed_with_retry([text])[0]

    def embed_texts(self, texts: list[str]) -> list[float]:
        """Generate embedding for concatenated texts.

        Args:
            texts: List of text values to concatenate and embed.

        Returns:
            Embedding vector.
        """
        combined = " ".join(str(t) for t in texts if t)
        return self.embed_text(combined)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        return self._embed_with_retry(texts)

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with retry logic.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            Exception: If all retries fail.
        """
        provider = self._get_provider()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return provider.embed(texts)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        raise last_error  # type: ignore

    def apply(self, table: ir.Table) -> ir.Table:
        """Apply embedding transform to a table.

        Args:
            table: Input Ibis table.

        Returns:
            Table with embedding column added.
        """
        import ibis

        # Convert to pandas for row-wise processing
        df = table.to_pandas()

        # Process in batches
        all_embeddings = []
        batch_texts = []

        for _, row in df.iterrows():
            # Concatenate input columns
            text_parts = [str(row[col]) for col in self.input_columns if row[col]]
            combined_text = " ".join(text_parts)
            batch_texts.append(combined_text)

            # Process batch when full
            if len(batch_texts) >= self.batch_size:
                embeddings = self.embed_batch(batch_texts)
                all_embeddings.extend(embeddings)
                batch_texts = []

        # Process remaining texts
        if batch_texts:
            embeddings = self.embed_batch(batch_texts)
            all_embeddings.extend(embeddings)

        # Add embeddings column
        df[self.output_column] = all_embeddings

        return ibis.memtable(df)

    def __call__(self, table: ir.Table) -> ir.Table:
        """Make the transform callable."""
        return self.apply(table)
