"""Tests for embedding transform.

This module tests:
- OpenAI embedding provider
- HuggingFace embedding provider
- Batching of embedding requests
- Retry on failure
- Multiple column embedding
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestEmbedTransform:
    """Tests for embedding transform."""

    def test_embed_with_openai_provider(self):
        """OpenAI provider generates embeddings for text."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.embed import EmbedTransform

        # Mock the OpenAI client
        with patch("quicketl.transforms.ai.providers.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock embedding response
            mock_embedding = MagicMock()
            mock_embedding.embedding = [0.1, 0.2, 0.3]
            mock_response = MagicMock()
            mock_response.data = [mock_embedding]
            mock_client.embeddings.create.return_value = mock_response

            transform = EmbedTransform(
                provider="openai",
                model="text-embedding-3-small",
                input_columns=["text"],
                output_column="embedding",
                api_key="test-key",
            )

            result = transform.embed_text("Hello world")

            assert result == [0.1, 0.2, 0.3]
            mock_client.embeddings.create.assert_called_once()

    def test_embed_with_huggingface_provider(self):
        """HuggingFace provider generates embeddings locally."""
        pytest.importorskip("sentence_transformers")

        from quicketl.transforms.ai.embed import EmbedTransform

        with patch(
            "quicketl.transforms.ai.providers.huggingface.SentenceTransformer"
        ) as mock_st:
            mock_model = MagicMock()
            mock_st.return_value = mock_model
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]

            transform = EmbedTransform(
                provider="huggingface",
                model="all-MiniLM-L6-v2",
                input_columns=["text"],
                output_column="embedding",
            )

            result = transform.embed_text("Hello world")

            assert result == [0.1, 0.2, 0.3]

    def test_embed_batching(self):
        """Embeddings are generated in batches for efficiency."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.embed import EmbedTransform

        with patch("quicketl.transforms.ai.providers.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock batch embedding response
            mock_embeddings = [
                MagicMock(embedding=[0.1, 0.2]),
                MagicMock(embedding=[0.3, 0.4]),
                MagicMock(embedding=[0.5, 0.6]),
            ]
            mock_response = MagicMock()
            mock_response.data = mock_embeddings
            mock_client.embeddings.create.return_value = mock_response

            transform = EmbedTransform(
                provider="openai",
                model="text-embedding-3-small",
                input_columns=["text"],
                output_column="embedding",
                api_key="test-key",
                batch_size=3,
            )

            texts = ["text1", "text2", "text3"]
            results = transform.embed_batch(texts)

            assert len(results) == 3
            assert results[0] == [0.1, 0.2]
            assert results[1] == [0.3, 0.4]
            assert results[2] == [0.5, 0.6]

    def test_embed_retry_on_failure(self):
        """Embeddings retry on transient failures."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.embed import EmbedTransform

        with patch("quicketl.transforms.ai.providers.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # First call fails, second succeeds
            mock_embedding = MagicMock()
            mock_embedding.embedding = [0.1, 0.2, 0.3]
            mock_response = MagicMock()
            mock_response.data = [mock_embedding]

            mock_client.embeddings.create.side_effect = [
                Exception("Rate limit"),
                mock_response,
            ]

            transform = EmbedTransform(
                provider="openai",
                model="text-embedding-3-small",
                input_columns=["text"],
                output_column="embedding",
                api_key="test-key",
                max_retries=3,
            )

            result = transform.embed_text("Hello world")

            assert result == [0.1, 0.2, 0.3]
            assert mock_client.embeddings.create.call_count == 2

    def test_embed_multiple_columns(self):
        """Multiple input columns are concatenated for embedding."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.embed import EmbedTransform

        with patch("quicketl.transforms.ai.providers.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_embedding = MagicMock()
            mock_embedding.embedding = [0.1, 0.2, 0.3]
            mock_response = MagicMock()
            mock_response.data = [mock_embedding]
            mock_client.embeddings.create.return_value = mock_response

            transform = EmbedTransform(
                provider="openai",
                model="text-embedding-3-small",
                input_columns=["title", "description"],
                output_column="embedding",
                api_key="test-key",
            )

            # Concatenated text should be used
            result = transform.embed_texts(["Title", "Description"])

            assert result == [0.1, 0.2, 0.3]


class TestEmbeddingProviders:
    """Tests for embedding provider implementations."""

    def test_openai_provider_initialization(self):
        """OpenAI provider initializes with API key."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.providers.openai import OpenAIEmbeddingProvider

        with patch("quicketl.transforms.ai.providers.openai.OpenAI") as mock_openai:
            provider = OpenAIEmbeddingProvider(
                model="text-embedding-3-small",
                api_key="test-key",
            )

            mock_openai.assert_called_once_with(api_key="test-key")
            assert provider.model == "text-embedding-3-small"

    def test_provider_from_config(self):
        """Provider can be created from config dict."""
        pytest.importorskip("openai")

        from quicketl.transforms.ai.providers import get_provider

        with patch("quicketl.transforms.ai.providers.openai.OpenAI"):
            provider = get_provider(
                provider="openai",
                model="text-embedding-3-small",
                api_key="test-key",
            )

            assert provider is not None
            assert provider.model == "text-embedding-3-small"

    def test_unknown_provider_raises_error(self):
        """Unknown provider name raises ValueError."""
        from quicketl.transforms.ai.providers import get_provider

        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_provider(provider="unknown", model="model")

    def test_huggingface_provider_initialization(self):
        """HuggingFace provider initializes with model name."""
        pytest.importorskip("sentence_transformers")

        from quicketl.transforms.ai.providers.huggingface import (
            HuggingFaceEmbeddingProvider,
        )

        with patch(
            "quicketl.transforms.ai.providers.huggingface.SentenceTransformer"
        ) as mock_st:
            provider = HuggingFaceEmbeddingProvider(model="all-MiniLM-L6-v2")

            mock_st.assert_called_once_with("all-MiniLM-L6-v2")
            assert provider.model == "all-MiniLM-L6-v2"
