# Workflows

Workflows orchestrate multiple pipelines with dependency management, parallel execution, and DAG generation for production orchestrators like Airflow and Prefect.

## Why Workflows?

While individual pipelines handle single data transformations, real-world ETL systems typically involve:

- **Multi-stage processing**: Bronze → Silver → Gold medallion architecture
- **Dependencies**: Pipeline B depends on Pipeline A completing first
- **Parallel execution**: Independent pipelines running concurrently
- **Production orchestration**: Deploying to Airflow, Prefect, or cloud schedulers

Workflows solve these problems with a single YAML definition that works both locally and in production.

## Quick Start

### 1. Create a Workflow

```yaml
# workflows/medallion.yml
name: medallion_etl
description: Bronze -> Silver data pipeline

stages:
  - name: bronze
    parallel: true
    pipelines:
      - path: pipelines/bronze/ingest_users.yml
      - path: pipelines/bronze/ingest_events.yml
      - path: pipelines/bronze/ingest_payments.yml

  - name: silver
    depends_on: [bronze]
    parallel: true
    pipelines:
      - path: pipelines/silver/clean_users.yml
      - path: pipelines/silver/clean_events.yml
```

### 2. Run Locally

```bash
quicketl workflow run workflows/medallion.yml
```

Output:
```
Running workflow: medallion_etl
  Stages: 2
  Pipelines: 5

╭────────────────────── Workflow: medallion_etl ──────────────────────╮
│ SUCCESS                                                              │
╰───────────────────────── Duration: 1234.5ms ─────────────────────────╯
                        Stages
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Stage  ┃ Status ┃ Pipelines ┃ Duration ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ bronze │ OK     │       3/3 │  812.3ms │
│ silver │ OK     │       2/2 │  421.2ms │
└────────┴────────┴───────────┴──────────┘
Pipelines: 5/5 succeeded
```

### 3. Generate Production DAG

```bash
# Generate Airflow DAG
quicketl workflow generate workflows/medallion.yml --target airflow -o dags/medallion_dag.py

# Generate Prefect flow
quicketl workflow generate workflows/medallion.yml --target prefect -o flows/medallion_flow.py
```

## Key Features

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg .middle } **Stage Dependencies**

    ---

    Define execution order with `depends_on`. Stages wait for dependencies to complete before starting.

-   :material-lightning-bolt:{ .lg .middle } **Parallel Execution**

    ---

    Run independent pipelines concurrently within a stage with `parallel: true`.

-   :material-airplane:{ .lg .middle } **DAG Generation**

    ---

    Generate Airflow DAGs or Prefect flows from your workflow YAML.

-   :material-variable:{ .lg .middle } **Variables**

    ---

    Define global variables inherited by all pipelines, with per-pipeline overrides.

</div>

## Workflow vs Individual Pipelines

| Aspect | Individual Pipelines | Workflows |
|--------|---------------------|-----------|
| Scope | Single transformation | Multiple coordinated pipelines |
| Dependencies | None | Stage-based with `depends_on` |
| Parallelism | Single pipeline | Multiple pipelines in parallel |
| Production Deploy | Manual DAG creation | Auto-generated DAGs |
| Local Dev | `quicketl run` | `quicketl workflow run` |

## Next Steps

- [Workflow YAML Configuration](workflow-yaml.md) - Complete configuration reference
- [DAG Generation](dag-generation.md) - Generate Airflow and Prefect code
- [Airflow Integration](../integrations/airflow.md) - Deploy to Airflow
