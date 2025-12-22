"""Pinecone vector store sink."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from quicketl.sinks.vector.base import AbstractVectorSink


class PineconeSink(BaseModel, AbstractVectorSink):
    """Vector store sink for Pinecone.

    Attributes:
        api_key: Pinecone API key.
        index: Index name.
        id_column: Column containing vector IDs.
        vector_column: Column containing embedding vectors.
        metadata_columns: Columns to include as metadata.
        namespace: Optional namespace within the index.
        batch_size: Number of vectors per upsert batch.
    """

    api_key: str = Field(..., description="Pinecone API key")
    index: str = Field(..., description="Index name")
    id_column: str = Field(..., description="Column containing vector IDs")
    vector_column: str = Field(..., description="Column containing embeddings")
    metadata_columns: list[str] = Field(
        default_factory=list,
        description="Columns to include as metadata",
    )
    namespace: str | None = Field(default=None, description="Namespace within index")
    batch_size: int = Field(default=100, description="Vectors per batch", gt=0)

    model_config = {"extra": "forbid"}

    _client: Any = None
    _index: Any = None

    def _get_index(self):
        """Get or create Pinecone index client."""
        if self._index is None:
            from pinecone import Pinecone

            self._client = Pinecone(api_key=self.api_key)
            self._index = self._client.Index(self.index)
        return self._index

    def write(self, data: list[dict[str, Any]]) -> None:
        """Write vectors to Pinecone.

        Args:
            data: List of dicts with id, vector, and optional metadata.
        """
        index = self._get_index()

        vectors = []
        for row in data:
            vector_data = {
                "id": str(row[self.id_column]),
                "values": row[self.vector_column],
            }

            if self.metadata_columns:
                metadata = {
                    col: row[col]
                    for col in self.metadata_columns
                    if col in row
                }
                vector_data["metadata"] = metadata

            vectors.append(vector_data)

        # Upsert in batches
        for i in range(0, len(vectors), self.batch_size):
            batch = vectors[i : i + self.batch_size]
            kwargs = {"vectors": batch}
            if self.namespace:
                kwargs["namespace"] = self.namespace
            index.upsert(**kwargs)
