# Upgrading to 2.0

This page explains what changes in the install when you move from QuickETL 1.x to 2.0. Read it if `pip install quicketl` stops running your pipelines.

QuickETL 2.0 is not released yet. It will ship as 2.0.0, after 1.7.0. Everything below applies from 2.0.0. Until then, `pip install quicketl` still gives you the full install.

## What changed

Before 2.0, `pip install quicketl` installed the whole data stack. From 2.0.0, it installs only the core:

- pydantic, pyyaml, structlog, typer and rich
- copier, for platform scaffolding

The core install is about 33 MB. These commands work with it:

- `quicketl --help` and `quicketl --version`
- `quicketl info` (without flags)
- `quicketl init`
- `quicketl validate`
- `quicketl schema`
- `quicketl platform init`, `validate`, `scaffold` and `update` (new in 2.0; `scaffold` and `update` also need `git`)

The data stack now lives in the `pipelines` extra (Ibis with DuckDB and Polars, plus fsspec). With it, the install is about 465 MB. You need it for:

- `quicketl run`
- `quicketl workflow` (run, validate, info and generate)
- `quicketl info --backends` and `quicketl info --check`
- The Python API (`from quicketl import Pipeline`)

## Fix the error

If you run a pipeline command on a core install, you see this message and the command exits with code 1:

```text
Error: Pipelines need the pipelines extra. Install it with: pip install 'quicketl[pipelines]'
```

Install the extra:

```bash
pip install 'quicketl[pipelines]'
```

Quote the extra. Shells such as zsh read square brackets as a pattern.

## Backend extras include pipelines

Any extra that only works inside a pipeline includes `pipelines`. If you already install one of these, you do not need to change anything:

`spark`, `pandas`, `datafusion`, `aws`, `gcp`, `azure`, `snowflake`, `bigquery`, `trino`, `postgres`, `mysql`, `clickhouse`, `chunking`, `embeddings-openai`, `embeddings-huggingface`, `vector-pinecone`, `vector-pgvector`, `vector-qdrant` and `contracts`. Because they build on those, `quality`, `ai` and `all` include it too.

These extras do not include `pipelines`: `secrets-aws`, `secrets-azure`, `opentelemetry`, `openlineage` and `docs`. If you use only these, add `pipelines` next to them.

## Update requirements files and CI

Change the line that names QuickETL:

| Before | After |
|--------|-------|
| `quicketl` | `quicketl[pipelines]` |
| `quicketl[snowflake]` | no change (already includes `pipelines`) |

In `requirements.txt`:

```text
quicketl[pipelines]>=2.0
```

In a CI step:

```yaml
- name: Install QuickETL
  run: pip install 'quicketl[pipelines]'
```

CI jobs that only run `quicketl validate` or `quicketl schema` can keep the plain `quicketl` install.

## Update Docker images

Change the install line in your Dockerfile:

```dockerfile
RUN pip install 'quicketl[pipelines]'
```

If you use a backend extra, keep it. For example `RUN pip install 'quicketl[postgres,snowflake]'` already includes `pipelines`.

## Python API

Your code does not change. With the `pipelines` extra installed, this still works:

```python
from quicketl import Pipeline
```

`import quicketl` itself no longer imports Ibis. `Pipeline`, `PipelineResult` and `QuickETLEngine` load the first time you use them. Without the extra, that first use raises an `ImportError` that names the fix:

```text
ImportError: quicketl.Pipeline: Pipelines need the pipelines extra. Install it with: pip install 'quicketl[pipelines]'
```

## Related

- [Installation](installation.md)
- [Troubleshooting](../reference/troubleshooting.md)
