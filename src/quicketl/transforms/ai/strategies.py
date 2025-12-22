"""Chunking strategies for text splitting.

Provides different strategies for splitting text into chunks:
- Fixed: Split by character or token count
- Sentence: Split on sentence boundaries
- Recursive: Try multiple separators in order
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ChunkStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        """Split text into chunks.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        ...


class FixedChunkStrategy(ChunkStrategy):
    """Split text by fixed character or token count.

    Attributes:
        chunk_size: Maximum size of each chunk.
        overlap: Number of characters/tokens to overlap between chunks.
        count_tokens: If True, count tokens instead of characters.
        tokenizer: Tokenizer name for token counting (requires tiktoken).
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 0,
        count_tokens: bool = False,
        tokenizer: str = "cl100k_base",
    ) -> None:
        """Initialize the fixed chunk strategy.

        Args:
            chunk_size: Maximum size of each chunk.
            overlap: Number of characters/tokens to overlap.
            count_tokens: If True, count tokens instead of characters.
            tokenizer: Tokenizer name for token counting.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.count_tokens = count_tokens
        self.tokenizer = tokenizer
        self._encoder = None

    def _get_encoder(self):
        """Lazy load the tokenizer encoder."""
        if self._encoder is None and self.count_tokens:
            import tiktoken

            self._encoder = tiktoken.get_encoding(self.tokenizer)
        return self._encoder

    def chunk(self, text: str) -> list[str]:
        """Split text into fixed-size chunks.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        if self.count_tokens:
            return self._chunk_by_tokens(text)
        return self._chunk_by_chars(text)

    def _chunk_by_chars(self, text: str) -> list[str]:
        """Split text by character count."""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunks.append(text[start:end])
            start = end - self.overlap if self.overlap > 0 else end

            # Prevent infinite loop if overlap >= chunk_size
            if self.overlap >= self.chunk_size:
                start = end

        return chunks

    def _chunk_by_tokens(self, text: str) -> list[str]:
        """Split text by token count."""
        encoder = self._get_encoder()
        tokens = encoder.encode(text)

        chunks = []
        start = 0
        total_tokens = len(tokens)

        while start < total_tokens:
            end = min(start + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]
            chunks.append(encoder.decode(chunk_tokens))
            start = end - self.overlap if self.overlap > 0 else end

            # Prevent infinite loop
            if self.overlap >= self.chunk_size:
                start = end

        return chunks


class SentenceChunkStrategy(ChunkStrategy):
    """Split text on sentence boundaries.

    Uses NLTK for sentence tokenization and groups sentences
    up to the chunk size limit.

    Attributes:
        chunk_size: Maximum characters per chunk.
        overlap: Number of sentences to overlap (not chars).
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 0,
    ) -> None:
        """Initialize the sentence chunk strategy.

        Args:
            chunk_size: Maximum characters per chunk.
            overlap: Number of sentences to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._tokenizer = None

    def _get_tokenizer(self):
        """Lazy load NLTK sentence tokenizer."""
        if self._tokenizer is None:
            import nltk

            try:
                self._tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
            except LookupError:
                nltk.download("punkt", quiet=True)
                self._tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
        return self._tokenizer

    def chunk(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        tokenizer = self._get_tokenizer()
        sentences = tokenizer.tokenize(text)

        if not sentences:
            return [text] if text.strip() else []

        chunks = []
        current_chunk: list[str] = []
        current_size = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If adding this sentence exceeds chunk_size, start new chunk
            if current_size + sentence_len > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Handle overlap by keeping last N sentences
                if self.overlap > 0:
                    current_chunk = current_chunk[-self.overlap :]
                    current_size = sum(len(s) for s in current_chunk)
                    # Prevent infinite loop if overlap exceeds chunk_size
                    if current_size >= self.chunk_size:
                        current_chunk = []
                        current_size = 0
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len

        # Add remaining sentences
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class RecursiveChunkStrategy(ChunkStrategy):
    """Recursively split text using multiple separators.

    Tries separators in order (e.g., paragraphs, then sentences,
    then words) to create semantically meaningful chunks.

    Attributes:
        chunk_size: Maximum characters per chunk.
        overlap: Characters to overlap between chunks.
        separators: List of separators to try in order.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 0,
        separators: list[str] | None = None,
    ) -> None:
        """Initialize the recursive chunk strategy.

        Args:
            chunk_size: Maximum characters per chunk.
            overlap: Characters to overlap between chunks.
            separators: List of separators to try in order.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def chunk(self, text: str) -> list[str]:
        """Split text recursively using separators.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separators."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        if not separators:
            # No more separators, fall back to fixed split
            return FixedChunkStrategy(
                chunk_size=self.chunk_size,
                overlap=self.overlap,
            ).chunk(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split on current separator
        parts = text.split(separator)

        chunks = []
        current_chunk = ""

        for part in parts:
            # Add separator back (except for first part)
            test_chunk = current_chunk + separator + part if current_chunk else part

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full, add it
                if current_chunk:
                    chunks.append(current_chunk)

                # If part itself is too large, recurse with remaining separators
                if len(part) > self.chunk_size:
                    sub_chunks = self._recursive_split(part, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks


def get_strategy(
    strategy: str,
    chunk_size: int = 500,
    overlap: int = 0,
    **kwargs,
) -> ChunkStrategy:
    """Get a chunking strategy by name.

    Args:
        strategy: Strategy name ('fixed', 'sentence', 'recursive').
        chunk_size: Maximum size of each chunk.
        overlap: Overlap between chunks.
        **kwargs: Additional strategy-specific arguments.

    Returns:
        The chunking strategy instance.

    Raises:
        ValueError: If strategy name is unknown.
    """
    match strategy:
        case "fixed":
            return FixedChunkStrategy(
                chunk_size=chunk_size,
                overlap=overlap,
                count_tokens=kwargs.get("count_tokens", False),
                tokenizer=kwargs.get("tokenizer", "cl100k_base"),
            )
        case "sentence":
            return SentenceChunkStrategy(
                chunk_size=chunk_size,
                overlap=overlap,
            )
        case "recursive":
            return RecursiveChunkStrategy(
                chunk_size=chunk_size,
                overlap=overlap,
                separators=kwargs.get("separators"),
            )
        case _:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
