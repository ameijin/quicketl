"""Sink modules for QuickETL.

Sinks handle writing data to various destinations including
vector stores for RAG pipelines.
"""

from quicketl.sinks.vector import (
    PgVectorSink,
    PineconeSink,
    QdrantSink,
    get_vector_sink,
)

__all__ = [
    "PineconeSink",
    "PgVectorSink",
    "QdrantSink",
    "get_vector_sink",
]
