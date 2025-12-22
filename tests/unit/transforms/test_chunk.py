"""Tests for text chunking transform.

This module tests:
- Fixed-size chunking with character count
- Fixed-size chunking with overlap
- Sentence-based chunking
- Recursive chunking with separators
- Metadata preservation across chunks
- Chunk index generation
- Empty text handling
"""

from __future__ import annotations

import pytest


class TestChunkTransform:
    """Tests for text chunking transform."""

    def test_fixed_size_chunking(self):
        """Fixed-size chunks split text by character count."""
        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=100,
            overlap=0,
            output_column="chunk_text",
        )

        # Create test data
        long_text = "A" * 250  # 250 characters

        result = transform.chunk_text(long_text)

        # Should produce 3 chunks: 100, 100, 50
        assert len(result) == 3
        assert len(result[0]) == 100
        assert len(result[1]) == 100
        assert len(result[2]) == 50

    def test_fixed_size_with_overlap(self):
        """Fixed-size chunks with overlap share content at boundaries."""
        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=100,
            overlap=20,
            output_column="chunk_text",
        )

        # Create test data with recognizable pattern
        text = "".join([str(i % 10) for i in range(200)])  # "01234567890123..."

        result = transform.chunk_text(text)

        # With overlap, chunks should share 20 chars
        # Chunk 1: chars 0-99
        # Chunk 2: chars 80-179 (overlaps 20 chars with chunk 1)
        # Chunk 3: chars 160-199 (overlaps 20 chars with chunk 2)
        assert len(result) >= 2

        # Verify overlap: end of chunk 1 should match start of chunk 2
        if len(result) >= 2:
            assert result[0][-20:] == result[1][:20]

    def test_sentence_chunking(self):
        """Sentence chunking splits on sentence boundaries."""
        pytest.importorskip("nltk")

        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="sentence",
            chunk_size=100,
            overlap=0,
            output_column="chunk_text",
        )

        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."

        result = transform.chunk_text(text)

        # Each chunk should end at a sentence boundary
        for chunk in result:
            # Chunks should typically end with sentence-ending punctuation
            # (though the last chunk might be partial)
            chunk_stripped = chunk.strip()
            if chunk_stripped:
                assert chunk_stripped[-1] in ".!?" or chunk == result[-1]

    def test_recursive_chunking(self):
        """Recursive chunking tries multiple separators."""
        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="recursive",
            chunk_size=50,
            overlap=0,
            output_column="chunk_text",
            separators=["\n\n", "\n", ". ", " "],
        )

        text = """Paragraph one with some text.

Paragraph two with more text.

Paragraph three."""

        result = transform.chunk_text(text)

        # Should split on paragraph boundaries first
        assert len(result) >= 2

        # Each chunk should be <= chunk_size (or close to it)
        for chunk in result:
            # Allow some slack for boundary handling
            assert len(chunk) <= 60  # chunk_size + buffer

    def test_chunk_preserves_metadata(self):
        """Chunking preserves metadata columns."""
        import ibis

        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=50,
            overlap=0,
            output_column="chunk_text",
        )

        # Create table with metadata
        data = {
            "doc_id": ["doc1", "doc2"],
            "title": ["Title One", "Title Two"],
            "text": ["A" * 100, "B" * 75],
        }
        table = ibis.memtable(data)

        result = transform.apply(table)
        df = result.to_pandas()

        # doc1 should produce 2 chunks, doc2 should produce 2 chunks
        assert len(df) == 4

        # Metadata should be preserved
        doc1_chunks = df[df["doc_id"] == "doc1"]
        assert len(doc1_chunks) == 2
        assert all(doc1_chunks["title"] == "Title One")

        doc2_chunks = df[df["doc_id"] == "doc2"]
        assert len(doc2_chunks) == 2
        assert all(doc2_chunks["title"] == "Title Two")

    def test_chunk_adds_chunk_index(self):
        """Chunking adds chunk index to each row."""
        import ibis

        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=50,
            overlap=0,
            output_column="chunk_text",
            add_chunk_index=True,
        )

        data = {
            "doc_id": ["doc1"],
            "text": ["A" * 150],  # Will produce 3 chunks
        }
        table = ibis.memtable(data)

        result = transform.apply(table)
        df = result.to_pandas()

        # Should have chunk_index column
        assert "chunk_index" in df.columns

        # Indices should be 0, 1, 2
        assert list(df["chunk_index"]) == [0, 1, 2]

    def test_empty_text_handling(self):
        """Empty text produces no chunks or single empty chunk."""
        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=100,
            overlap=0,
            output_column="chunk_text",
        )

        result = transform.chunk_text("")

        # Empty text should produce empty list or single empty chunk
        assert len(result) <= 1

    def test_chunk_with_token_counting(self):
        """Chunking can use token count instead of character count."""
        pytest.importorskip("tiktoken")

        from quicketl.transforms.ai.chunk import ChunkTransform

        transform = ChunkTransform(
            column="text",
            strategy="fixed",
            chunk_size=10,  # 10 tokens
            overlap=0,
            output_column="chunk_text",
            count_tokens=True,
            tokenizer="cl100k_base",  # GPT-4 tokenizer
        )

        # Each word is roughly 1 token
        text = " ".join(["word"] * 25)  # ~25 tokens

        result = transform.chunk_text(text)

        # Should produce ~3 chunks of ~10 tokens each
        assert len(result) >= 2


class TestChunkStrategies:
    """Tests for individual chunking strategies."""

    def test_fixed_strategy_basic(self):
        """Fixed strategy splits by character count."""
        from quicketl.transforms.ai.strategies import FixedChunkStrategy

        strategy = FixedChunkStrategy(chunk_size=10, overlap=0)

        text = "Hello World, this is a test."
        chunks = strategy.chunk(text)

        assert len(chunks) == 3
        assert chunks[0] == "Hello Worl"
        assert chunks[1] == "d, this is"
        assert chunks[2] == " a test."

    def test_sentence_strategy_basic(self):
        """Sentence strategy splits on sentence boundaries."""
        pytest.importorskip("nltk")

        from quicketl.transforms.ai.strategies import SentenceChunkStrategy

        strategy = SentenceChunkStrategy(chunk_size=50, overlap=0)

        text = "First sentence. Second sentence. Third sentence."
        chunks = strategy.chunk(text)

        # Should group sentences up to chunk_size
        assert len(chunks) >= 1
        # Each chunk should contain complete sentences
        assert "First sentence." in chunks[0]

    def test_recursive_strategy_basic(self):
        """Recursive strategy tries separators in order."""
        from quicketl.transforms.ai.strategies import RecursiveChunkStrategy

        strategy = RecursiveChunkStrategy(
            chunk_size=30,
            overlap=0,
            separators=["\n\n", "\n", " "],
        )

        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = strategy.chunk(text)

        # Should split on paragraph boundaries
        assert len(chunks) >= 2
