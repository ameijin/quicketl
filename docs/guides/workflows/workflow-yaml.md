# Workflow YAML Configuration

Complete reference for workflow configuration files.

## Schema Overview

```yaml
name: string                    # Required: Workflow name
description: string             # Optional: Description
variables: { key: value }       # Optional: Global variables
fail_fast: boolean              # Optional: Stop on first failure (default: true)
stages:                         # Required: List of stages
  - name: string                # Required: Stage name
    description: string         # Optional: Stage description
    depends_on: [stage_names]   # Optional: Dependencies
    parallel: boolean           # Optional: Run pipelines in parallel (default: false)
    pipelines:                  # Required: List of pipelines
      - path: string            # Required: Path to pipeline YAML
        variables: { k: v }     # Optional: Pipeline-specific variables
```

## Complete Example

```yaml
name: medallion_etl
description: Bronze -> Silver -> Gold medallion architecture pipeline

# Global variables available to all pipelines
variables:
  DATA_DIR: ./data
  RUN_DATE: "2025-01-15"

# Stop workflow on first failure
fail_fast: true

stages:
  # Stage 1: Bronze Layer - Raw Data Ingestion
  - name: bronze
    description: Ingest raw data from source files
    parallel: true  # Run all bronze pipelines concurrently
    pipelines:
      - path: pipelines/bronze/ingest_users.yml
      - path: pipelines/bronze/ingest_events.yml
      - path: pipelines/bronze/ingest_payments.yml
        variables:
          CURRENCY_FILTER: USD  # Override for this pipeline only

  # Stage 2: Silver Layer - Data Cleaning
  - name: silver_clean
    description: Clean and deduplicate bronze data
    depends_on: [bronze]  # Wait for bronze to complete
    parallel: true
    pipelines:
      - path: pipelines/silver/clean_users.yml
      - path: pipelines/silver/clean_events.yml
      - path: pipelines/silver/clean_payments.yml

  # Stage 3: Silver Layer - Aggregation
  - name: silver_agg
    description: Aggregate metrics
    depends_on: [silver_clean]
    parallel: false  # Run sequentially
    pipelines:
      - path: pipelines/silver/agg_revenue_daily.yml
      - path: pipelines/silver/agg_user_metrics.yml

  # Stage 4: Gold Layer - Database Loading
  - name: gold
    description: Load to reporting database
    depends_on: [silver_agg]
    pipelines:
      - path: pipelines/gold/load_revenue.yml
      - path: pipelines/gold/load_user_metrics.yml
```

## Configuration Fields

### Top-Level Fields

#### `name` (required)

Workflow identifier used in CLI output, DAG IDs, and logging.

```yaml
name: daily_etl_workflow
```

#### `description` (optional)

Human-readable description shown in CLI output and generated DAG docstrings.

```yaml
description: Daily ETL pipeline for sales data processing
```

#### `variables` (optional)

Global variables passed to all pipelines. Individual pipeline variables override globals.

```yaml
variables:
  DATA_DIR: /data/lake
  RUN_DATE: "2025-01-15"
  ENVIRONMENT: production
```

Variables are substituted using `${VAR}` syntax in pipeline configs:

```yaml
# In pipeline YAML
source:
  type: file
  path: ${DATA_DIR}/bronze/users.parquet
```

#### `fail_fast` (optional, default: `true`)

Controls behavior when a pipeline fails:

- `true`: Stop workflow immediately on first failure
- `false`: Continue running remaining pipelines, report failures at end

```yaml
fail_fast: false  # Continue despite failures
```

### Stage Fields

#### `name` (required)

Unique stage identifier used in `depends_on` references and CLI output.

```yaml
stages:
  - name: bronze
    # ...
  - name: silver
    depends_on: [bronze]  # Reference by name
```

#### `description` (optional)

Stage description for documentation and DAG generation.

```yaml
- name: silver
  description: Clean, deduplicate, and enrich bronze data
```

#### `depends_on` (optional)

List of stage names that must complete before this stage starts.

```yaml
# Single dependency
- name: silver
  depends_on: [bronze]

# Multiple dependencies
- name: gold
  depends_on: [silver_clean, silver_agg]
```

Dependencies are validated:

- Referenced stages must exist
- No circular dependencies allowed
- Stages execute in topological order

#### `parallel` (optional, default: `false`)

Run pipelines within the stage concurrently:

```yaml
- name: bronze
  parallel: true  # All pipelines run at same time
  pipelines:
    - path: pipelines/bronze/users.yml
    - path: pipelines/bronze/events.yml
    - path: pipelines/bronze/payments.yml
```

Use `parallel: false` (default) for sequential execution when pipelines depend on each other within the same stage.

#### `pipelines` (required)

List of pipeline references to execute in this stage.

```yaml
pipelines:
  - path: pipelines/bronze/users.yml
  - path: pipelines/bronze/events.yml
    variables:
      FILTER_DATE: "2025-01-01"
```

### Pipeline Reference Fields

#### `path` (required)

Path to the pipeline YAML file, relative to the workflow file location.

```yaml
# Workflow at: workflows/medallion.yml
# Pipeline at: pipelines/bronze/users.yml
pipelines:
  - path: ../pipelines/bronze/users.yml  # Relative to workflow file
```

#### `variables` (optional)

Pipeline-specific variables that override global workflow variables.

```yaml
variables:
  RUN_DATE: "2025-01-01"

stages:
  - name: bronze
    pipelines:
      - path: pipelines/users.yml
        variables:
          RUN_DATE: "2025-01-15"  # Overrides global
          BATCH_SIZE: 10000       # Pipeline-specific
```

## Execution Order

Stages are executed based on dependencies using topological sorting:

```yaml
stages:
  - name: gold
    depends_on: [silver_agg, silver_clean]
  - name: bronze
  - name: silver_clean
    depends_on: [bronze]
  - name: silver_agg
    depends_on: [bronze]
```

Execution order:
1. `bronze` (no dependencies)
2. `silver_clean` and `silver_agg` (can run in parallel - both depend only on `bronze`)
3. `gold` (depends on both silver stages)

Check execution order:

```bash
quicketl workflow info workflows/medallion.yml
```

Output:
```
Workflow: medallion_etl

Execution Order:
  1. bronze
  2. silver_clean, silver_agg
  3. gold

Stages
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Stage        ┃ Pipelines ┃ Parallel ┃ Depends On               ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ bronze       │         3 │ Yes      │ -                        │
│ silver_clean │         3 │ Yes      │ bronze                   │
│ silver_agg   │         2 │ No       │ bronze                   │
│ gold         │         2 │ No       │ silver_agg, silver_clean │
└──────────────┴───────────┴──────────┴──────────────────────────┘
```

## Validation

Validate workflow configuration without running:

```bash
quicketl workflow validate workflows/medallion.yml
```

Validation checks:
- YAML syntax
- Required fields present
- Stage dependencies are valid (no cycles, no missing stages)
- All referenced pipeline files exist

Verbose validation shows structure:

```bash
quicketl workflow validate workflows/medallion.yml --verbose
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `quicketl workflow run <file>` | Execute workflow |
| `quicketl workflow validate <file>` | Validate configuration |
| `quicketl workflow info <file>` | Show structure and execution order |
| `quicketl workflow generate <file>` | Generate Airflow/Prefect code |

See [CLI Reference](../../reference/cli.md#workflow) for full options.
