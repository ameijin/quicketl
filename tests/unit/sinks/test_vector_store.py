"""Tests for vector store sinks.

This module tests:
- Pinecone vector store sink
- pgvector (PostgreSQL) vector store sink
- Qdrant vector store sink
- Config validation for all providers
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestVectorStoreSink:
    """Tests for vector store sink config validation."""

    def test_pinecone_sink_config_validation(self):
        """Pinecone sink validates required config fields."""
        from quicketl.sinks.vector import PineconeSink

        # Valid config
        sink = PineconeSink(
            api_key="test-key",
            index="test-index",
            id_column="doc_id",
            vector_column="embedding",
        )
        assert sink.index == "test-index"
        assert sink.id_column == "doc_id"

    def test_pgvector_sink_config_validation(self):
        """pgvector sink validates required config fields."""
        from quicketl.sinks.vector import PgVectorSink

        # Valid config
        sink = PgVectorSink(
            connection_string="postgresql://localhost/test",
            table="embeddings",
            id_column="doc_id",
            vector_column="embedding",
        )
        assert sink.table == "embeddings"
        assert sink.id_column == "doc_id"

    def test_qdrant_sink_config_validation(self):
        """Qdrant sink validates required config fields."""
        from quicketl.sinks.vector import QdrantSink

        # Valid config
        sink = QdrantSink(
            url="http://localhost:6333",
            collection="test-collection",
            id_column="doc_id",
            vector_column="embedding",
        )
        assert sink.collection == "test-collection"
        assert sink.id_column == "doc_id"


class TestPineconeSink:
    """Tests for Pinecone vector store sink."""

    def test_pinecone_upsert_vectors(self):
        """Pinecone sink upserts vectors to index."""
        pytest.importorskip("pinecone")

        from quicketl.sinks.vector import PineconeSink

        with patch("quicketl.sinks.vector.pinecone.Pinecone") as mock_pc:
            mock_index = MagicMock()
            mock_pc.return_value.Index.return_value = mock_index

            sink = PineconeSink(
                api_key="test-key",
                index="test-index",
                id_column="doc_id",
                vector_column="embedding",
            )

            # Test data
            data = [
                {"doc_id": "1", "embedding": [0.1, 0.2, 0.3]},
                {"doc_id": "2", "embedding": [0.4, 0.5, 0.6]},
            ]

            sink.write(data)

            # Verify upsert was called
            mock_index.upsert.assert_called_once()
            call_args = mock_index.upsert.call_args
            vectors = call_args[1]["vectors"]
            assert len(vectors) == 2

    def test_pinecone_with_metadata(self):
        """Pinecone sink includes metadata columns."""
        pytest.importorskip("pinecone")

        from quicketl.sinks.vector import PineconeSink

        with patch("quicketl.sinks.vector.pinecone.Pinecone") as mock_pc:
            mock_index = MagicMock()
            mock_pc.return_value.Index.return_value = mock_index

            sink = PineconeSink(
                api_key="test-key",
                index="test-index",
                id_column="doc_id",
                vector_column="embedding",
                metadata_columns=["title", "category"],
            )

            data = [
                {
                    "doc_id": "1",
                    "embedding": [0.1, 0.2],
                    "title": "Doc 1",
                    "category": "A",
                },
            ]

            sink.write(data)

            call_args = mock_index.upsert.call_args
            vectors = call_args[1]["vectors"]
            assert vectors[0]["metadata"]["title"] == "Doc 1"
            assert vectors[0]["metadata"]["category"] == "A"


class TestPgVectorSink:
    """Tests for pgvector (PostgreSQL) vector store sink."""

    def test_pgvector_insert_vectors(self):
        """pgvector sink inserts vectors to table."""
        pytest.importorskip("psycopg2")

        from quicketl.sinks.vector import PgVectorSink

        with patch("quicketl.sinks.vector.pgvector.psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            sink = PgVectorSink(
                connection_string="postgresql://localhost/test",
                table="embeddings",
                id_column="doc_id",
                vector_column="embedding",
            )

            data = [
                {"doc_id": "1", "embedding": [0.1, 0.2, 0.3]},
                {"doc_id": "2", "embedding": [0.4, 0.5, 0.6]},
            ]

            sink.write(data)

            # Verify insert was called
            assert mock_cursor.execute.called
            mock_conn.commit.assert_called_once()

    def test_pgvector_upsert_mode(self):
        """pgvector sink supports upsert mode."""
        pytest.importorskip("psycopg2")

        from quicketl.sinks.vector import PgVectorSink

        with patch("quicketl.sinks.vector.pgvector.psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            sink = PgVectorSink(
                connection_string="postgresql://localhost/test",
                table="embeddings",
                id_column="doc_id",
                vector_column="embedding",
                upsert=True,
            )

            data = [{"doc_id": "1", "embedding": [0.1, 0.2, 0.3]}]

            sink.write(data)

            # Verify ON CONFLICT clause in SQL
            call_args = mock_cursor.execute.call_args[0][0]
            assert "ON CONFLICT" in call_args


class TestQdrantSink:
    """Tests for Qdrant vector store sink."""

    def test_qdrant_upsert_vectors(self):
        """Qdrant sink upserts vectors to collection."""
        pytest.importorskip("qdrant_client")

        from quicketl.sinks.vector import QdrantSink

        with patch("quicketl.sinks.vector.qdrant.QdrantClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            sink = QdrantSink(
                url="http://localhost:6333",
                collection="test-collection",
                id_column="doc_id",
                vector_column="embedding",
            )

            data = [
                {"doc_id": "1", "embedding": [0.1, 0.2, 0.3]},
                {"doc_id": "2", "embedding": [0.4, 0.5, 0.6]},
            ]

            sink.write(data)

            mock_client.upsert.assert_called_once()


class TestVectorSinkRegistry:
    """Tests for vector sink factory."""

    def test_get_sink_pinecone(self):
        """Factory returns Pinecone sink."""
        pytest.importorskip("pinecone")

        from quicketl.sinks.vector import get_vector_sink

        with patch("pinecone.Pinecone"):
            sink = get_vector_sink(
                provider="pinecone",
                api_key="test-key",
                index="test-index",
                id_column="doc_id",
                vector_column="embedding",
            )
            assert sink is not None

    def test_get_sink_unknown_raises_error(self):
        """Factory raises error for unknown provider."""
        from quicketl.sinks.vector import get_vector_sink

        with pytest.raises(ValueError, match="Unknown vector store provider"):
            get_vector_sink(
                provider="unknown",
                id_column="doc_id",
                vector_column="embedding",
            )
