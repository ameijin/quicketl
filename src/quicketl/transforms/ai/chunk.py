"""Text chunking transform for document processing.

Splits text into smaller chunks suitable for embedding and retrieval.
Supports multiple chunking strategies: fixed, sentence, recursive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from quicketl.transforms.ai.strategies import get_strategy

if TYPE_CHECKING:
    import ibis.expr.types as ir


class ChunkTransform(BaseModel):
    """Transform that splits text into chunks.

    This transform explodes each row into multiple rows, one per chunk.
    Metadata columns are preserved across all chunks from the same source row.

    Attributes:
        column: The text column to chunk.
        strategy: Chunking strategy ('fixed', 'sentence', 'recursive').
        chunk_size: Maximum size of each chunk (chars or tokens).
        overlap: Overlap between consecutive chunks.
        output_column: Name for the chunked text column.
        add_chunk_index: Whether to add a chunk_index column.
        count_tokens: If True, chunk_size refers to tokens not chars.
        tokenizer: Tokenizer name for token counting.
        separators: Separators for recursive strategy.

    Example YAML:
        - op: chunk
          column: document_text
          strategy: recursive
          chunk_size: 512
          overlap: 50
          output_column: chunk_text
    """

    column: str = Field(..., description="Text column to chunk")
    strategy: str = Field(
        default="fixed",
        description="Chunking strategy: 'fixed', 'sentence', 'recursive'",
    )
    chunk_size: int = Field(default=500, description="Maximum chunk size", gt=0)
    overlap: int = Field(default=0, description="Overlap between chunks", ge=0)
    output_column: str = Field(
        default="chunk_text",
        description="Name for the output chunk column",
    )
    add_chunk_index: bool = Field(
        default=False,
        description="Add a chunk_index column",
    )
    count_tokens: bool = Field(
        default=False,
        description="Count tokens instead of characters",
    )
    tokenizer: str = Field(
        default="cl100k_base",
        description="Tokenizer for token counting",
    )
    separators: list[str] | None = Field(
        default=None,
        description="Separators for recursive strategy",
    )

    model_config = {"extra": "forbid"}

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks using the configured strategy.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        chunker = get_strategy(
            self.strategy,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
            count_tokens=self.count_tokens,
            tokenizer=self.tokenizer,
            separators=self.separators,
        )
        return chunker.chunk(text)

    def apply(self, table: ir.Table) -> ir.Table:
        """Apply chunking transform to a table.

        Each row is exploded into multiple rows, one per chunk.
        All other columns are preserved as metadata.

        Args:
            table: Input Ibis table.

        Returns:
            Table with rows exploded into chunks.
        """
        import ibis

        # Get all columns except the text column
        metadata_cols = [c for c in table.columns if c != self.column]

        # Convert to pandas for row-wise processing
        # (Ibis doesn't have native UDF support for exploding rows)
        df = table.to_pandas()

        result_rows = []
        for _, row in df.iterrows():
            text = row[self.column]
            if text is None or (isinstance(text, str) and not text.strip()):
                # Empty text: produce single row with empty chunk
                chunk_row = {col: row[col] for col in metadata_cols}
                chunk_row[self.output_column] = ""
                if self.add_chunk_index:
                    chunk_row["chunk_index"] = 0
                result_rows.append(chunk_row)
            else:
                chunks = self.chunk_text(str(text))
                for idx, chunk in enumerate(chunks):
                    chunk_row = {col: row[col] for col in metadata_cols}
                    chunk_row[self.output_column] = chunk
                    if self.add_chunk_index:
                        chunk_row["chunk_index"] = idx
                    result_rows.append(chunk_row)

        # Convert back to Ibis table
        import pandas as pd

        result_df = pd.DataFrame(result_rows)
        return ibis.memtable(result_df)

    def __call__(self, table: ir.Table) -> ir.Table:
        """Make the transform callable.

        Args:
            table: Input Ibis table.

        Returns:
            Transformed table.
        """
        return self.apply(table)
