# Vector Store Sinks

Write embeddings to vector databases for similarity search and RAG pipelines.

## Overview

Vector stores are specialized databases optimized for storing and querying high-dimensional vectors (embeddings). QuickETL supports three major vector stores:

| Provider | Type | Best For |
|----------|------|----------|
| [Pinecone](#pinecone) | Managed | Serverless, no infrastructure |
| [pgvector](#pgvector) | Self-hosted | PostgreSQL integration |
| [Qdrant](#qdrant) | Self-hosted/Cloud | Open source, feature-rich |

## Installation

```bash
# Individual providers
pip install "quicketl[vector-pinecone]"
pip install "quicketl[vector-pgvector]"
pip install "quicketl[vector-qdrant]"

# All vector stores
pip install "quicketl[ai]"
```

---

## Pinecone

Fully managed vector database with serverless option.

### Configuration

```yaml
sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:pinecone/api_key}
  index: my-index
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, category, url]
  namespace: production
  batch_size: 100
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `api_key` | Yes | `str` | Pinecone API key |
| `index` | Yes | `str` | Index name |
| `id_column` | Yes | `str` | Column with unique IDs |
| `vector_column` | Yes | `str` | Column with embedding vectors |
| `metadata_columns` | No | `list[str]` | Columns to store as metadata |
| `namespace` | No | `str` | Namespace within index |
| `batch_size` | No | `int` | Vectors per upsert (default: 100) |

### Index Setup

Create your index in the Pinecone console or via API:

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="...")
pc.create_index(
    name="my-index",
    dimension=1536,  # Must match embedding model
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)
```

### Example Pipeline

```yaml
name: pinecone-embeddings
source:
  type: file
  path: documents.json
  format: json

transforms:
  - op: chunk
    column: content
    strategy: recursive
    chunk_size: 512

  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [chunk_text]
    output_column: embedding
    api_key: ${secret:openai/api_key}

sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:pinecone/api_key}
  index: documents
  id_column: id
  vector_column: embedding
  metadata_columns: [chunk_text, title, source_url]
```

---

## pgvector

PostgreSQL extension for vector similarity search. Self-hosted with full SQL support.

### Prerequisites

Enable the pgvector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Create a table for embeddings:

```sql
CREATE TABLE document_embeddings (
    id TEXT PRIMARY KEY,
    embedding vector(1536),  -- Dimension must match model
    title TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX ON document_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Configuration

```yaml
sink:
  type: vector_store
  provider: pgvector
  connection_string: ${secret:postgres/connection_string}
  table: document_embeddings
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, content]
  upsert: true
  batch_size: 100
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `connection_string` | Yes | `str` | PostgreSQL connection string |
| `table` | Yes | `str` | Table name |
| `id_column` | Yes | `str` | Column with unique IDs |
| `vector_column` | Yes | `str` | Column with embedding vectors |
| `metadata_columns` | No | `list[str]` | Additional columns to insert |
| `upsert` | No | `bool` | Use ON CONFLICT (default: false) |
| `batch_size` | No | `int` | Rows per batch (default: 100) |

### Upsert Mode

When `upsert: true`, existing records are updated:

```sql
INSERT INTO table (id, embedding, title)
VALUES ($1, $2, $3)
ON CONFLICT (id)
DO UPDATE SET embedding = EXCLUDED.embedding, title = EXCLUDED.title
```

### Example Pipeline

```yaml
name: pgvector-embeddings
source:
  type: database
  connection: ${secret:source_db}
  query: SELECT id, title, content FROM articles

transforms:
  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [title, content]
    output_column: embedding
    api_key: ${secret:openai/api_key}

sink:
  type: vector_store
  provider: pgvector
  connection_string: ${secret:postgres/connection_string}
  table: article_embeddings
  id_column: id
  vector_column: embedding
  metadata_columns: [title, content]
  upsert: true
```

### Querying

```sql
-- Find similar documents
SELECT id, title, content,
       embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM document_embeddings
ORDER BY distance
LIMIT 10;
```

---

## Qdrant

Open-source vector database with advanced filtering and cloud offering.

### Configuration

```yaml
sink:
  type: vector_store
  provider: qdrant
  url: http://localhost:6333
  collection: documents
  id_column: doc_id
  vector_column: embedding
  metadata_columns: [title, category, url]
  api_key: ${secret:qdrant/api_key}  # For Qdrant Cloud
  batch_size: 100
```

### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `url` | Yes | `str` | Qdrant server URL |
| `collection` | Yes | `str` | Collection name |
| `id_column` | Yes | `str` | Column with unique IDs |
| `vector_column` | Yes | `str` | Column with embedding vectors |
| `metadata_columns` | No | `list[str]` | Columns for payload |
| `api_key` | No | `str` | API key for Qdrant Cloud |
| `batch_size` | No | `int` | Points per batch (default: 100) |

### Collection Setup

Create a collection before running the pipeline:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(url="http://localhost:6333")
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
```

### Running Qdrant Locally

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Example Pipeline

```yaml
name: qdrant-embeddings
source:
  type: file
  path: products.csv
  format: csv

transforms:
  - op: derive_column
    name: search_text
    expr: "concat(name, ' ', description)"

  - op: embed
    provider: huggingface
    model: all-MiniLM-L6-v2
    input_columns: [search_text]
    output_column: embedding

sink:
  type: vector_store
  provider: qdrant
  url: http://localhost:6333
  collection: products
  id_column: product_id
  vector_column: embedding
  metadata_columns: [name, description, category, price]
```

---

## Python API

```python
from quicketl.sinks.vector import (
    PineconeSink,
    PgVectorSink,
    QdrantSink,
    get_vector_sink,
)

# Using factory function
sink = get_vector_sink(
    provider="pinecone",
    api_key="...",
    index="my-index",
    id_column="id",
    vector_column="embedding",
)

# Direct instantiation
sink = PgVectorSink(
    connection_string="postgresql://localhost/db",
    table="embeddings",
    id_column="id",
    vector_column="embedding",
    upsert=True,
)

# Write data
data = [
    {"id": "1", "embedding": [0.1, 0.2, ...], "title": "Doc 1"},
    {"id": "2", "embedding": [0.3, 0.4, ...], "title": "Doc 2"},
]
sink.write(data)
```

---

## Best Practices

### Choosing a Vector Store

| Use Case | Recommended |
|----------|-------------|
| Quick start, no infrastructure | Pinecone |
| Already using PostgreSQL | pgvector |
| Need advanced filtering | Qdrant |
| Self-hosted, open source | Qdrant |
| Serverless, pay-per-use | Pinecone |

### Performance Tips

1. **Batch appropriately** - Larger batches are more efficient but use more memory
2. **Use upsert** - Enables incremental updates without duplicates
3. **Index properly** - Create vector indexes for fast similarity search
4. **Match dimensions** - Ensure index dimension matches embedding model
5. **Monitor memory** - Large embedding datasets can consume significant memory

### Metadata Design

Store useful metadata for filtering and retrieval:

```yaml
metadata_columns:
  - title           # Display in results
  - chunk_text      # Original text for context
  - source_url      # Link to source
  - category        # For filtering
  - created_at      # For time-based queries
```

---

## Related

- [AI Data Preparation](../ai-data-prep.md) - Complete RAG pipeline guide
- [Secrets Management](../secrets.md) - Secure credential handling
- [Database Sinks](database-sinks.md) - Traditional database sinks
