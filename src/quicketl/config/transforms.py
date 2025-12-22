"""Transform step configuration models.

Defines the 12 core transform operations as a Pydantic discriminated union.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class SelectTransform(BaseModel):
    """Select specific columns from the data.

    Example YAML:
        - op: select
          columns: [id, name, amount]
    """

    op: Literal["select"] = "select"
    columns: list[str] = Field(..., description="Columns to select")


class RenameTransform(BaseModel):
    """Rename columns.

    Example YAML:
        - op: rename
          mapping:
            old_name: new_name
            another_old: another_new
    """

    op: Literal["rename"] = "rename"
    mapping: dict[str, str] = Field(
        ...,
        description="Mapping of old column names to new names",
    )


class FilterTransform(BaseModel):
    """Filter rows using a SQL-like predicate.

    Example YAML:
        - op: filter
          predicate: amount > 100 AND status = 'active'
    """

    op: Literal["filter"] = "filter"
    predicate: str = Field(..., description="SQL-like filter predicate")


class DeriveColumnTransform(BaseModel):
    """Create a new computed column.

    Example YAML:
        - op: derive_column
          name: revenue
          expr: quantity * unit_price
    """

    op: Literal["derive_column"] = "derive_column"
    name: str = Field(..., description="Name for the new column")
    expr: str = Field(..., description="SQL-like expression for the column value")


class CastTransform(BaseModel):
    """Cast column types.

    Example YAML:
        - op: cast
          columns:
            id: string
            amount: float64
            created_at: datetime
    """

    op: Literal["cast"] = "cast"
    columns: dict[str, str] = Field(
        ...,
        description="Mapping of column names to target types",
    )


class FillNullTransform(BaseModel):
    """Replace null values with defaults.

    Example YAML:
        - op: fill_null
          columns:
            discount: 0
            notes: "N/A"
    """

    op: Literal["fill_null"] = "fill_null"
    columns: dict[str, Any] = Field(
        ...,
        description="Mapping of column names to fill values",
    )


class DedupTransform(BaseModel):
    """Remove duplicate rows.

    Example YAML:
        - op: dedup
          columns: [id]  # Dedupe based on id column

        # Or dedupe on all columns:
        - op: dedup
    """

    op: Literal["dedup"] = "dedup"
    columns: list[str] | None = Field(
        default=None,
        description="Columns to consider for deduplication (None = all)",
    )


class SortTransform(BaseModel):
    """Sort rows by specified columns.

    Example YAML:
        - op: sort
          by: [created_at, id]
          descending: true
    """

    op: Literal["sort"] = "sort"
    by: list[str] = Field(..., description="Columns to sort by")
    descending: bool = Field(default=False, description="Sort in descending order")


class JoinTransform(BaseModel):
    """Join with another data source.

    Example YAML:
        - op: join
          right: customers  # Reference to another source
          on: [customer_id]
          how: left
    """

    op: Literal["join"] = "join"
    right: str = Field(..., description="Reference to the right dataset")
    on: list[str] = Field(..., description="Join key columns")
    how: Literal["inner", "left", "right", "outer"] = Field(
        default="inner",
        description="Join type",
    )


class AggregateTransform(BaseModel):
    """Group and aggregate data.

    Example YAML:
        - op: aggregate
          group_by: [region, category]
          aggs:
            total_revenue: sum(amount)
            order_count: count(*)
            avg_order: mean(amount)
    """

    op: Literal["aggregate"] = "aggregate"
    group_by: list[str] = Field(..., description="Columns to group by")
    aggs: dict[str, str] = Field(
        ...,
        description="Mapping of output column names to aggregation expressions",
    )


class UnionTransform(BaseModel):
    """Vertically concatenate multiple datasets.

    Example YAML:
        - op: union
          sources: [dataset1, dataset2]
    """

    op: Literal["union"] = "union"
    sources: list[str] = Field(
        ...,
        description="References to datasets to union",
    )


class LimitTransform(BaseModel):
    """Limit to first N rows.

    Example YAML:
        - op: limit
          n: 1000
    """

    op: Literal["limit"] = "limit"
    n: int = Field(..., description="Maximum number of rows", gt=0)


class WindowColumn(BaseModel):
    """Configuration for a single window column.

    Attributes:
        name: Name for the new column.
        func: Window function (row_number, rank, dense_rank, lag, lead, sum, avg, min, max).
        column: Source column for functions that need it (lag, lead, sum, etc.).
        offset: Offset for lag/lead functions.
        partition_by: Columns to partition by.
        order_by: Columns or order specs to order by within partition.
        default: Default value for lag/lead when no row exists.
    """

    name: str = Field(..., description="Name for the new column")
    func: Literal[
        "row_number", "rank", "dense_rank", "lag", "lead",
        "sum", "avg", "min", "max", "count", "first", "last"
    ] = Field(..., description="Window function to apply")
    column: str | None = Field(default=None, description="Source column for aggregation functions")
    offset: int = Field(default=1, description="Offset for lag/lead functions")
    partition_by: list[str] = Field(default_factory=list, description="Columns to partition by")
    order_by: list[str | dict[str, Any]] = Field(
        default_factory=list,
        description="Columns or {column, descending} specs to order by",
    )
    default: Any = Field(default=None, description="Default value for lag/lead")


class WindowTransform(BaseModel):
    """Apply window functions over partitions.

    Example YAML:
        - op: window
          columns:
            - name: row_num
              func: row_number
              partition_by: [customer_id]
              order_by: [order_date]
            - name: prev_amount
              func: lag
              column: amount
              offset: 1
              partition_by: [customer_id]
              order_by: [order_date]
    """

    op: Literal["window"] = "window"
    columns: list[WindowColumn | dict[str, Any]] = Field(
        ...,
        description="Window column specifications",
    )


class PivotTransform(BaseModel):
    """Pivot (reshape) data from long to wide format.

    Example YAML:
        - op: pivot
          index: [region, quarter]
          columns: product
          values: revenue
          aggfunc: sum
    """

    op: Literal["pivot"] = "pivot"
    index: list[str] = Field(..., description="Columns to keep as row identifiers")
    columns: str = Field(..., description="Column whose unique values become new columns")
    values: str = Field(..., description="Column whose values populate the new columns")
    aggfunc: str | list[str] = Field(
        default="first",
        description="Aggregation function(s) to apply",
    )


class UnpivotTransform(BaseModel):
    """Unpivot (melt) data from wide to long format.

    Example YAML:
        - op: unpivot
          id_vars: [id, name]
          value_vars: [jan_sales, feb_sales, mar_sales]
          var_name: month
          value_name: sales
    """

    op: Literal["unpivot"] = "unpivot"
    id_vars: list[str] = Field(..., description="Columns to keep as identifiers")
    value_vars: list[str] = Field(..., description="Columns to unpivot into rows")
    var_name: str = Field(default="variable", description="Name for the variable column")
    value_name: str = Field(default="value", description="Name for the value column")


class HashKeyTransform(BaseModel):
    """Generate a hash key from one or more columns.

    Example YAML:
        - op: hash_key
          name: customer_hash
          columns: [customer_id, order_id]
          algorithm: md5
    """

    op: Literal["hash_key"] = "hash_key"
    name: str = Field(..., description="Name for the new hash column")
    columns: list[str] = Field(..., description="Columns to include in the hash")
    algorithm: Literal["md5", "sha256", "sha1"] = Field(
        default="md5",
        description="Hash algorithm to use",
    )
    separator: str = Field(default="|", description="Separator between column values")


class CoalesceTransform(BaseModel):
    """Return first non-null value from a list of columns.

    Example YAML:
        - op: coalesce
          name: email
          columns: [primary_email, secondary_email, fallback_email]
          default: "unknown@example.com"
    """

    op: Literal["coalesce"] = "coalesce"
    name: str = Field(..., description="Name for the new column")
    columns: list[str] = Field(..., description="Columns to coalesce, in priority order")
    default: Any = Field(default=None, description="Default value if all columns are null")


class ChunkTransformConfig(BaseModel):
    """Split text into chunks for RAG pipelines.

    This transform explodes each row into multiple rows, one per chunk.
    Metadata columns are preserved across all chunks from the same source row.

    Requires: quicketl[chunking] for sentence strategy, or tiktoken for token counting.

    Example YAML:
        - op: chunk
          column: document_text
          strategy: recursive
          chunk_size: 512
          overlap: 50
          output_column: chunk_text
    """

    op: Literal["chunk"] = "chunk"
    column: str = Field(..., description="Text column to chunk")
    strategy: Literal["fixed", "sentence", "recursive"] = Field(
        default="fixed",
        description="Chunking strategy",
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
        description="Count tokens instead of characters (requires tiktoken)",
    )
    tokenizer: str = Field(
        default="cl100k_base",
        description="Tokenizer for token counting",
    )
    separators: list[str] | None = Field(
        default=None,
        description="Separators for recursive strategy",
    )


class EmbedTransformConfig(BaseModel):
    """Generate embeddings for text columns.

    Supports OpenAI and HuggingFace embedding providers.

    Requires: quicketl[embeddings-openai] or quicketl[embeddings-huggingface]

    Example YAML:
        - op: embed
          provider: openai
          model: text-embedding-3-small
          input_columns: [title, description]
          output_column: embedding
          batch_size: 100
          api_key: ${secret:openai/api_key}
    """

    op: Literal["embed"] = "embed"
    provider: Literal["openai", "huggingface"] = Field(
        ...,
        description="Embedding provider",
    )
    model: str = Field(..., description="Model name")
    input_columns: list[str] = Field(..., description="Columns to embed")
    output_column: str = Field(default="embedding", description="Output column name")
    batch_size: int = Field(default=100, description="Batch size for API calls", gt=0)
    api_key: str | None = Field(default=None, description="API key if required")
    max_retries: int = Field(default=3, description="Max retry attempts", ge=0)


# Discriminated union for all transform types
TransformStep = Annotated[
    SelectTransform
    | RenameTransform
    | FilterTransform
    | DeriveColumnTransform
    | CastTransform
    | FillNullTransform
    | DedupTransform
    | SortTransform
    | JoinTransform
    | AggregateTransform
    | UnionTransform
    | LimitTransform
    | WindowTransform
    | PivotTransform
    | UnpivotTransform
    | HashKeyTransform
    | CoalesceTransform
    | ChunkTransformConfig
    | EmbedTransformConfig,
    Field(discriminator="op"),
]
