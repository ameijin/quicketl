# AI Data Preparation

QuickETL provides transforms for building RAG (Retrieval-Augmented Generation) pipelines: text chunking, embeddings generation, and vector store sinks.

## Overview

A typical RAG pipeline:

```
Documents → Chunk → Embed → Vector Store
```

QuickETL handles each step with dedicated transforms:

| Step | Transform/Sink | Purpose |
|------|----------------|---------|
| Chunk | `chunk` | Split text into smaller pieces |
| Embed | `embed` | Generate vector embeddings |
| Store | `vector_store` | Write to Pinecone, pgvector, Qdrant |

## Installation

```bash
# Full AI bundle
pip install "quicketl[ai]"

# Or individual components
pip install "quicketl[chunking]"              # Text chunking
pip install "quicketl[embeddings-openai]"     # OpenAI embeddings
pip install "quicketl[embeddings-huggingface]" # Local embeddings
pip install "quicketl[vector-pinecone]"       # Pinecone
pip install "quicketl[vector-pgvector]"       # PostgreSQL pgvector
pip install "quicketl[vector-qdrant]"         # Qdrant
```

---

## Text Chunking

Split long text into smaller chunks suitable for embedding.

### Quick Start

```yaml
transforms:
  - op: chunk
    column: document_text
    strategy: recursive
    chunk_size: 512
    overlap: 50
    output_column: chunk_text
```

### Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `fixed` | Split by character/token count | Simple, predictable chunks |
| `sentence` | Split on sentence boundaries | Natural language text |
| `recursive` | Try multiple separators | Documents with structure |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | Required | Text column to chunk |
| `strategy` | `str` | `"fixed"` | Chunking strategy |
| `chunk_size` | `int` | `500` | Maximum chunk size |
| `overlap` | `int` | `0` | Overlap between chunks |
| `output_column` | `str` | `"chunk_text"` | Output column name |
| `add_chunk_index` | `bool` | `false` | Add chunk index column |
| `count_tokens` | `bool` | `false` | Count tokens instead of chars |
| `tokenizer` | `str` | `"cl100k_base"` | Tokenizer for token counting |
| `separators` | `list[str]` | `null` | Custom separators for recursive |

### Examples

#### Fixed-Size Chunks

```yaml
- op: chunk
  column: content
  strategy: fixed
  chunk_size: 1000
  overlap: 100
```

#### Sentence-Based Chunks

```yaml
- op: chunk
  column: article_body
  strategy: sentence
  chunk_size: 500
  overlap: 1  # Overlap 1 sentence
```

#### Recursive with Custom Separators

```yaml
- op: chunk
  column: markdown_content
  strategy: recursive
  chunk_size: 512
  overlap: 50
  separators:
    - "\n## "    # H2 headers
    - "\n### "   # H3 headers
    - "\n\n"     # Paragraphs
    - "\n"       # Lines
    - ". "       # Sentences
    - " "        # Words
```

#### Token-Based Chunks

```yaml
- op: chunk
  column: text
  strategy: fixed
  chunk_size: 256
  count_tokens: true
  tokenizer: cl100k_base  # GPT-4 tokenizer
```

---

## Embeddings Generation

Generate vector embeddings from text using OpenAI or HuggingFace models.

### Quick Start

```yaml
transforms:
  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [chunk_text]
    output_column: embedding
    api_key: ${secret:openai/api_key}
```

### Providers

| Provider | Models | Pros | Cons |
|----------|--------|------|------|
| `openai` | text-embedding-3-small/large, ada-002 | High quality, fast | API costs |
| `huggingface` | all-MiniLM-L6-v2, etc. | Free, runs locally | Slower, less accurate |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `str` | Required | `"openai"` or `"huggingface"` |
| `model` | `str` | Required | Model name |
| `input_columns` | `list[str]` | Required | Columns to embed |
| `output_column` | `str` | `"embedding"` | Output column name |
| `batch_size` | `int` | `100` | Texts per API call |
| `api_key` | `str` | `null` | API key (OpenAI) |
| `max_retries` | `int` | `3` | Retry attempts on failure |

### Examples

#### OpenAI Embeddings

```yaml
- op: embed
  provider: openai
  model: text-embedding-3-small
  input_columns: [title, description]
  output_column: embedding
  batch_size: 100
  api_key: ${secret:openai/api_key}
```

#### HuggingFace (Local)

```yaml
- op: embed
  provider: huggingface
  model: all-MiniLM-L6-v2
  input_columns: [chunk_text]
  output_column: embedding
```

#### Multiple Columns

When multiple input columns are specified, they are concatenated with spaces:

```yaml
- op: embed
  provider: openai
  model: text-embedding-3-small
  input_columns: [title, summary, keywords]  # Concatenated
  output_column: combined_embedding
```

---

## Vector Store Sinks

Write embeddings to vector databases for similarity search.

### Supported Stores

| Store | Installation | Best For |
|-------|--------------|----------|
| Pinecone | `quicketl[vector-pinecone]` | Managed, serverless |
| pgvector | `quicketl[vector-pgvector]` | Self-hosted, PostgreSQL |
| Qdrant | `quicketl[vector-qdrant]` | Open source, feature-rich |

### Pinecone

```yaml
sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:pinecone/api_key}
  index: product-embeddings
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, category, url]
  namespace: production  # Optional
```

### pgvector (PostgreSQL)

```yaml
sink:
  type: vector_store
  provider: pgvector
  connection_string: ${secret:postgres/connection_string}
  table: document_embeddings
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, source]
  upsert: true  # Update existing records
```

### Qdrant

```yaml
sink:
  type: vector_store
  provider: qdrant
  url: http://localhost:6333
  collection: documents
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, category]
  api_key: ${secret:qdrant/api_key}  # For Qdrant Cloud
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id_column` | `str` | Column with unique document IDs |
| `vector_column` | `str` | Column with embedding vectors |
| `metadata_columns` | `list[str]` | Columns to store as metadata |
| `batch_size` | `int` | Records per upsert batch |

---

## Complete RAG Pipeline Example

```yaml
# rag-pipeline.yml
name: document-embedding-pipeline
description: Process documents for RAG

source:
  type: file
  path: s3://my-bucket/documents/
  format: json

transforms:
  # Clean and prepare text
  - op: filter
    predicate: content IS NOT NULL AND length(content) > 100

  - op: derive_column
    name: doc_id
    expr: "concat(source, '_', id)"

  # Chunk documents
  - op: chunk
    column: content
    strategy: recursive
    chunk_size: 512
    overlap: 50
    output_column: chunk_text
    add_chunk_index: true

  # Generate embeddings
  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [chunk_text]
    output_column: embedding
    api_key: ${secret:openai/api_key}

  # Select final columns
  - op: select
    columns: [doc_id, chunk_index, chunk_text, embedding, title, url]

sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:pinecone/api_key}
  index: documents
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [chunk_index, chunk_text, title, url]
```

Run the pipeline:

```bash
quicketl run rag-pipeline.yml --env prod
```

---

## Best Practices

### Chunking

1. **Choose chunk size based on model** - OpenAI recommends 512-1024 tokens
2. **Use overlap** - 10-20% overlap prevents losing context at boundaries
3. **Match strategy to content** - Use `recursive` for structured docs, `sentence` for prose

### Embeddings

1. **Batch efficiently** - Larger batches are more efficient but use more memory
2. **Handle rate limits** - Use `max_retries` and consider adding delays
3. **Cache embeddings** - Store embeddings to avoid recomputing unchanged docs

### Vector Stores

1. **Use upsert mode** - Enables incremental updates without duplicates
2. **Include useful metadata** - Store text and source info for retrieval
3. **Monitor index size** - Plan for growth and set up index maintenance

---

## Python API

```python
from quicketl.transforms.ai import ChunkTransform
from quicketl.transforms.ai.embed import EmbedTransform
from quicketl.sinks.vector import PineconeSink

# Chunking
chunker = ChunkTransform(
    column="content",
    strategy="recursive",
    chunk_size=512,
    overlap=50,
)
chunks = chunker.chunk_text("Long document text...")

# Embedding
embedder = EmbedTransform(
    provider="openai",
    model="text-embedding-3-small",
    input_columns=["text"],
    api_key="sk-...",
)
vector = embedder.embed_text("Hello world")

# Vector store
sink = PineconeSink(
    api_key="...",
    index="documents",
    id_column="doc_id",
    vector_column="embedding",
)
sink.write([{"doc_id": "1", "embedding": vector}])
```
