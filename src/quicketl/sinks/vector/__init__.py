"""Vector store sinks for RAG pipelines.

Supports Pinecone, pgvector (PostgreSQL), and Qdrant.
"""

from __future__ import annotations

from typing import Any

from quicketl.sinks.vector.pgvector import PgVectorSink
from quicketl.sinks.vector.pinecone import PineconeSink
from quicketl.sinks.vector.qdrant import QdrantSink

__all__ = [
    "PineconeSink",
    "PgVectorSink",
    "QdrantSink",
    "get_vector_sink",
]


def get_vector_sink(
    provider: str,
    **kwargs: Any,
) -> PineconeSink | PgVectorSink | QdrantSink:
    """Get a vector store sink by provider name.

    Args:
        provider: Provider name ('pinecone', 'pgvector', 'qdrant').
        **kwargs: Provider-specific configuration.

    Returns:
        The vector store sink instance.

    Raises:
        ValueError: If provider name is unknown.
    """
    match provider:
        case "pinecone":
            return PineconeSink(**kwargs)
        case "pgvector":
            return PgVectorSink(**kwargs)
        case "qdrant":
            return QdrantSink(**kwargs)
        case _:
            raise ValueError(f"Unknown vector store provider: {provider}")
