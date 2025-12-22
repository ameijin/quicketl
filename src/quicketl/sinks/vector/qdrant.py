"""Qdrant vector store sink."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from quicketl.sinks.vector.base import AbstractVectorSink


class QdrantSink(BaseModel, AbstractVectorSink):
    """Vector store sink for Qdrant.

    Attributes:
        url: Qdrant server URL.
        collection: Collection name.
        id_column: Column containing vector IDs.
        vector_column: Column containing embeddings.
        metadata_columns: Columns to include as payload.
        api_key: Optional API key for Qdrant Cloud.
        batch_size: Number of vectors per upsert batch.
    """

    url: str = Field(..., description="Qdrant server URL")
    collection: str = Field(..., description="Collection name")
    id_column: str = Field(..., description="Column containing vector IDs")
    vector_column: str = Field(..., description="Column containing embeddings")
    metadata_columns: list[str] = Field(
        default_factory=list,
        description="Columns to include as payload",
    )
    api_key: str | None = Field(default=None, description="API key for Qdrant Cloud")
    batch_size: int = Field(default=100, description="Vectors per batch", gt=0)

    model_config = {"extra": "forbid"}

    _client: Any = None

    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            from qdrant_client import QdrantClient

            kwargs = {"url": self.url}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._client = QdrantClient(**kwargs)
        return self._client

    def write(self, data: list[dict[str, Any]]) -> None:
        """Write vectors to Qdrant.

        Args:
            data: List of dicts with id, vector, and optional metadata.
        """
        from qdrant_client.models import PointStruct

        client = self._get_client()

        points = []
        for row in data:
            payload = {}
            if self.metadata_columns:
                payload = {
                    col: row[col]
                    for col in self.metadata_columns
                    if col in row
                }

            point = PointStruct(
                id=str(row[self.id_column]),
                vector=row[self.vector_column],
                payload=payload,
            )
            points.append(point)

        # Upsert in batches
        for i in range(0, len(points), self.batch_size):
            batch = points[i : i + self.batch_size]
            client.upsert(
                collection_name=self.collection,
                points=batch,
            )
