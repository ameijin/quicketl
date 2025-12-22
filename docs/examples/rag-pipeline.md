# RAG Pipeline Example

This example demonstrates a complete Retrieval-Augmented Generation (RAG) pipeline using QuickETL.

## Overview

We'll build a pipeline that:

1. Reads documents from cloud storage
2. Chunks text for optimal embedding
3. Generates embeddings with OpenAI
4. Stores vectors in Pinecone

## Prerequisites

```bash
pip install "quicketl[ai]"
```

Set up environment variables or use a secrets provider:

```bash
export OPENAI_API_KEY="sk-..."
export PINECONE_API_KEY="..."
```

## Project Structure

```
my-rag-project/
├── quicketl.yml          # Project configuration
├── pipelines/
│   ├── embed-documents.yml
│   └── embed-incremental.yml
└── data/
    └── documents/
```

## Configuration

### quicketl.yml

```yaml
version: "1.0"

secrets:
  provider: ${env:SECRETS_PROVIDER:-env}

environments:
  dev:
    engine: duckdb

  prod:
    engine: duckdb
    secrets:
      provider: aws
      config:
        region: us-east-1

profiles:
  pinecone_prod:
    provider: pinecone
    index: knowledge-base
```

## Full Pipeline

### embed-documents.yml

```yaml
name: document-embedding-pipeline
description: Process documents for RAG knowledge base

# Source: JSON documents from S3
source:
  type: file
  path: s3://my-bucket/documents/*.json
  format: json

transforms:
  # 1. Filter valid documents
  - op: filter
    predicate: >
      content IS NOT NULL
      AND length(content) > 100
      AND status = 'published'

  # 2. Create unique document ID
  - op: derive_column
    name: doc_id
    expr: "concat(source, '_', id)"

  # 3. Clean and prepare text
  - op: derive_column
    name: clean_content
    expr: "trim(regexp_replace(content, '\\s+', ' '))"

  # 4. Chunk documents
  - op: chunk
    column: clean_content
    strategy: recursive
    chunk_size: 512
    overlap: 50
    output_column: chunk_text
    add_chunk_index: true
    separators:
      - "\n\n"      # Paragraphs
      - "\n"        # Lines
      - ". "        # Sentences
      - " "         # Words

  # 5. Create chunk ID
  - op: derive_column
    name: chunk_id
    expr: "concat(doc_id, '_chunk_', cast(chunk_index as string))"

  # 6. Generate embeddings
  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [chunk_text]
    output_column: embedding
    batch_size: 100
    api_key: ${secret:OPENAI_API_KEY}
    max_retries: 3

  # 7. Select final columns
  - op: select
    columns:
      - chunk_id
      - doc_id
      - chunk_index
      - chunk_text
      - embedding
      - title
      - url
      - category
      - published_at

# Sink: Pinecone vector store
sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:PINECONE_API_KEY}
  index: knowledge-base
  namespace: production
  id_column: chunk_id
  vector_column: embedding
  metadata_columns:
    - doc_id
    - chunk_index
    - chunk_text
    - title
    - url
    - category
    - published_at
  batch_size: 100
```

## Running the Pipeline

```bash
# Development (local files)
quicketl run pipelines/embed-documents.yml --env dev

# Production (S3 + AWS Secrets)
quicketl run pipelines/embed-documents.yml --env prod

# Dry run to preview
quicketl run pipelines/embed-documents.yml --dry-run
```

## Incremental Updates

For updating only changed documents:

### embed-incremental.yml

```yaml
name: incremental-embedding-pipeline
description: Process only new/updated documents

source:
  type: database
  connection: ${secret:SOURCE_DB}
  query: |
    SELECT id, title, content, url, category, updated_at
    FROM documents
    WHERE updated_at > '${var:last_run_time}'
      AND status = 'published'

transforms:
  # Same transforms as above...
  - op: filter
    predicate: content IS NOT NULL AND length(content) > 100

  - op: derive_column
    name: doc_id
    expr: "cast(id as string)"

  - op: chunk
    column: content
    strategy: recursive
    chunk_size: 512
    overlap: 50
    output_column: chunk_text
    add_chunk_index: true

  - op: derive_column
    name: chunk_id
    expr: "concat(doc_id, '_chunk_', cast(chunk_index as string))"

  - op: embed
    provider: openai
    model: text-embedding-3-small
    input_columns: [chunk_text]
    output_column: embedding
    api_key: ${secret:OPENAI_API_KEY}

sink:
  type: vector_store
  provider: pinecone
  api_key: ${secret:PINECONE_API_KEY}
  index: knowledge-base
  id_column: chunk_id
  vector_column: embedding
  metadata_columns: [doc_id, chunk_index, chunk_text, title, url]
```

Run with variables:

```bash
quicketl run pipelines/embed-incremental.yml \
  --var last_run_time="2024-01-01 00:00:00"
```

## Querying the Vector Store

After embedding, query your knowledge base:

```python
from pinecone import Pinecone
from openai import OpenAI

# Initialize clients
pc = Pinecone(api_key="...")
index = pc.Index("knowledge-base")
openai = OpenAI()

# Embed the query
query = "How do I configure authentication?"
query_embedding = openai.embeddings.create(
    input=query,
    model="text-embedding-3-small"
).data[0].embedding

# Search
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    namespace="production",
)

# Display results
for match in results.matches:
    print(f"Score: {match.score:.3f}")
    print(f"Title: {match.metadata['title']}")
    print(f"Text: {match.metadata['chunk_text'][:200]}...")
    print()
```

## Using with LangChain

```python
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# Initialize
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Pinecone.from_existing_index(
    index_name="knowledge-base",
    embedding=embeddings,
    namespace="production",
)

# Create QA chain
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
)

# Ask questions
answer = qa.run("How do I configure authentication?")
print(answer)
```

## Monitoring with Observability

Add tracing and lineage:

```python
from quicketl.telemetry import TracingContext, get_correlation_id
from quicketl.telemetry.openlineage import LineageContext

# Initialize
tracing = TracingContext(service_name="rag-pipeline")
lineage = LineageContext(namespace="quicketl", job_name="document-embedding")

# Track lineage
lineage.add_input_dataset("s3://my-bucket", "documents")
lineage.add_output_dataset("pinecone://knowledge-base", "embeddings")

# Run with tracing
correlation_id = get_correlation_id()
lineage.emit_start()

with tracing.span("rag_pipeline", attributes={"correlation_id": correlation_id}):
    # Run pipeline...
    pass

lineage.emit_complete()
```

## Best Practices

### Chunking

- **512-1024 tokens** is optimal for most embedding models
- **10-20% overlap** prevents losing context at boundaries
- **Recursive strategy** works best for structured documents

### Embeddings

- **Batch processing** is more efficient than single requests
- **text-embedding-3-small** offers good quality/cost balance
- **Cache embeddings** for unchanged documents

### Vector Store

- **Upsert mode** enables incremental updates
- **Store chunk text** in metadata for display
- **Include source URL** for attribution

### Production

- Use **cloud secrets** (AWS/Azure) not environment variables
- Enable **observability** for monitoring
- Schedule **incremental updates** for fresh data

## Related

- [AI Data Preparation Guide](../guides/ai-data-prep.md)
- [Vector Store Sinks](../guides/io/vector-sinks.md)
- [Secrets Management](../guides/secrets.md)
- [Observability](../guides/observability.md)
