# CLI Reference

QuickETL provides a command-line interface for running and managing pipelines.

## Quick Reference

| Command | Description |
|---------|-------------|
| [`run`](#run) | Execute a pipeline |
| [`validate`](#validate) | Validate configuration |
| [`workflow`](#workflow) | Run and manage multi-pipeline workflows |
| [`init`](#init) | Create new project or pipeline |
| [`platform`](#platform) | Work with platform specs (`platform.yml`) |
| [`info`](#info) | Display version and backend info |
| [`schema`](#schema) | Output JSON schema for IDE support |

## Global Options

```bash
quicketl --version    # Show version
quicketl --help       # Show help
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation, execution, etc.) |

---

## run {#run}

Execute a pipeline from a YAML configuration file.

### Usage

```bash
quicketl run <config_file> [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--engine` | `-e` | Override compute engine |
| `--var` | `-v` | Set variable (KEY=VALUE), can be repeated |
| `--dry-run` | | Execute without writing output |
| `--fail-on-checks` | | Fail on quality check failure (default) |
| `--no-fail-on-checks` | | Continue despite check failures |
| `--verbose` | `-V` | Enable verbose logging |
| `--json` | `-j` | Output result as JSON |
| `--base-dir` | | Folder that relative file paths resolve against. Default: folder of the nearest `quicketl.yml`, else the current folder |

### Examples

```bash
# Basic run
quicketl run pipeline.yml

# With variables
quicketl run pipeline.yml --var DATE=2025-01-15
quicketl run pipeline.yml --var DATE=2025-01-15 --var REGION=north

# Override engine
quicketl run pipeline.yml --engine polars
quicketl run pipeline.yml --engine spark

# Dry run (no output written)
quicketl run pipeline.yml --dry-run

# Continue on check failure
quicketl run pipeline.yml --no-fail-on-checks

# JSON output (for scripting)
quicketl run pipeline.yml --json

# Pin the folder for relative data paths
quicketl run pipelines/sales.yml --base-dir /opt/project
```

### Output

```
Running pipeline: sales_etl
  Engine: duckdb

╭─────────────── Pipeline: sales_etl ───────────────╮
│ SUCCESS                                           │
╰───────────────────── Duration: 245.3ms ───────────╯

Steps
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Step           ┃ Type    ┃ Status ┃ Duration ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ read_source    │ file    │ OK     │   45.2ms │
│ transform_0    │ filter  │ OK     │    0.3ms │
│ quality_checks │ checks  │ OK     │   12.4ms │
│ write_sink     │ file    │ OK     │    8.1ms │
└────────────────┴─────────┴────────┴──────────┘

Quality Checks: PASSED (2/2)
Rows processed: 1000 → Rows written: 950
```

### JSON Output

```json
{
  "pipeline_name": "sales_etl",
  "status": "SUCCESS",
  "duration_ms": 245.3,
  "rows_processed": 1000,
  "rows_written": 950,
  "checks_passed": 3,
  "checks_failed": 0
}
```

---

## validate {#validate}

Validate a pipeline configuration without executing it.

### Usage

```bash
quicketl validate <config_file> [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Show detailed configuration |

### Examples

```bash
# Basic validation
quicketl validate pipeline.yml

# Verbose output
quicketl validate pipeline.yml --verbose
```

### Output

**Valid configuration:**

```
Configuration is valid

Pipeline: sales_etl
  Engine: duckdb
  Source: file (data/sales.parquet)
  Transforms: 3
  Checks: 2
  Sink: file (output/results.parquet)
```

**Invalid configuration:**

```
Configuration is invalid

Errors:
  - transforms -> 0 -> op: Input should be 'select', 'filter', ...
  - sink: Field required
```

### CI/CD Usage

```yaml
# .github/workflows/validate.yml
- name: Validate pipelines
  run: |
    for f in pipelines/*.yml; do
      quicketl validate "$f"
    done
```

---

## workflow {#workflow}

Run and manage multi-pipeline workflows with dependency management and parallel execution.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `run` | Execute a workflow |
| `validate` | Validate workflow configuration |
| `info` | Show workflow structure and execution order |
| `generate` | Generate Airflow DAG or Prefect flow |

### workflow run

Execute a workflow from a YAML configuration file.

```bash
quicketl workflow run <config_file> [options]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--var` | `-v` | Set variable (KEY=VALUE), can be repeated |
| `--dry-run` | | Execute without writing output |
| `--workers` | `-w` | Maximum parallel workers for parallel stages |
| `--verbose` | `-V` | Enable verbose logging |
| `--json` | `-j` | Output result as JSON |
| `--base-dir` | | Folder that relative file paths in each pipeline resolve against. Default: folder of the nearest `quicketl.yml`, else the current folder |

#### Examples

```bash
# Basic run
quicketl workflow run workflows/medallion.yml

# With variables
quicketl workflow run workflows/etl.yml --var DATE=2025-01-15

# Dry run
quicketl workflow run workflows/etl.yml --dry-run

# Limit parallel workers
quicketl workflow run workflows/etl.yml --workers 4

# JSON output for scripting
quicketl workflow run workflows/etl.yml --json

# Pin the folder for relative data paths
quicketl workflow run workflows/etl.yml --base-dir /opt/project
```

#### Output

```
Running workflow: medallion_etl
  Stages: 3
  Pipelines: 9

╭────────────────────── Workflow: medallion_etl ──────────────────────╮
│ SUCCESS                                                              │
╰───────────────────────── Duration: 1643.7ms ─────────────────────────╯
                        Stages
┏━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Stage        ┃ Status ┃ Pipelines ┃ Duration ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ bronze       │ OK     │       4/4 │ 1314.2ms │
│ silver_clean │ OK     │       3/3 │  205.9ms │
│ silver_agg   │ OK     │       2/2 │  122.8ms │
└──────────────┴────────┴───────────┴──────────┘
Pipelines: 9/9 succeeded
```

### workflow validate

Validate a workflow configuration without executing it.

```bash
quicketl workflow validate <config_file> [options]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-V` | Show detailed workflow structure |

#### Examples

```bash
# Basic validation
quicketl workflow validate workflows/medallion.yml

# Show structure
quicketl workflow validate workflows/medallion.yml --verbose
```

Validation checks:

- YAML syntax is valid
- All required fields are present
- Stage dependencies are valid (no cycles, no missing deps)
- All referenced pipeline files exist

### workflow info

Display workflow structure and execution order.

```bash
quicketl workflow info <config_file>
```

#### Example

```bash
quicketl workflow info workflows/medallion.yml
```

Output:

```
Workflow: medallion_etl
  Bronze -> Silver medallion architecture pipeline

Execution Order:
  1. bronze
  2. silver_clean, silver_agg
  3. gold

                        Stages
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Stage        ┃ Pipelines ┃ Parallel ┃ Depends On       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ bronze       │         4 │ Yes      │ -                │
│ silver_clean │         3 │ Yes      │ bronze           │
│ silver_agg   │         2 │ No       │ silver_clean     │
│ gold         │         2 │ No       │ silver_agg       │
└──────────────┴───────────┴──────────┴──────────────────┘

Variables:
  DATA_DIR: ./data
```

### workflow generate

Generate orchestration code from a workflow configuration.

```bash
quicketl workflow generate <config_file> [options]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--target` | `-t` | Target orchestrator: `airflow` or `prefect` (default: airflow) |
| `--output` | `-o` | Output file path (prints to stdout if not specified) |
| `--dag-id` | | DAG/flow ID (defaults to workflow name) |
| `--schedule` | `-s` | Cron schedule (Airflow only) |

#### Examples

```bash
# Generate Airflow DAG to stdout
quicketl workflow generate workflows/etl.yml --target airflow

# Save to file with schedule
quicketl workflow generate workflows/etl.yml --target airflow -o dags/etl_dag.py --schedule "0 0 * * *"

# Generate Prefect flow
quicketl workflow generate workflows/etl.yml --target prefect -o flows/etl_flow.py

# Custom DAG ID
quicketl workflow generate workflows/etl.yml --target airflow --dag-id daily_etl_v2
```

See [Workflow Documentation](../guides/workflows/index.md) for complete workflow configuration reference.

---

## init {#init}

Initialize QuickETL in the current directory or create a new project.

### Usage

```bash
quicketl init [name] [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | No | Project name. If omitted, initializes in current directory |

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--pipeline` | `-p` | Create pipeline file only (requires name) |
| `--output` | `-o` | Output directory (default: current) |
| `--force` | `-f` | Overwrite existing files |

### Examples

```bash
# Initialize in current directory (existing project)
quicketl init

# Create new project in subdirectory
quicketl init my_project
cd my_project

# Create pipeline file only
quicketl init my_pipeline -p

# Specify output directory
quicketl init my_project -o ./projects/
```

### In Current Directory

When run without a name, `quicketl init` adds QuickETL structure to your existing project:

```
your_project/
├── quicketl.yml        # Project root marker, never overwritten
├── pipelines/
│   └── sample.yml      # Working sample pipeline
├── data/
│   ├── sales.csv       # Sample data
│   └── output/         # Pipeline outputs
└── .env                # Created only if not present
```

Existing files (`README.md`, `.gitignore`, etc.) are preserved.

### New Project Structure

When run with a name, creates a complete project:

```
my_project/
├── quicketl.yml        # Project root marker
├── pipelines/
│   └── sample.yml      # Working sample pipeline
├── data/
│   ├── sales.csv       # Sample data
│   └── output/         # Pipeline outputs
├── scripts/            # Custom Python scripts
├── README.md
├── .env
└── .gitignore
```

The sample pipeline is immediately runnable:

```bash
quicketl run pipelines/sample.yml
```

---

## platform {#platform}

Work with platform specs. A platform spec (`platform.yml`) describes the data platform you want. See [Platform Spec](../platform/spec.md). These commands are part of the core install and do not need the `pipelines` extra.

### platform init

Write a commented starter `platform.yml` to edit.

```bash
quicketl platform init [directory] [options]
```

`directory` defaults to the current folder and is created if missing.

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Platform name. Default: the folder name, lowercased, with other characters turned into `_` (`acme-data` becomes `acme_data`). |
| `--warehouse` | `-w` | `snowflake` (default), `databricks` or `redshift_serverless` |
| `--force` | `-f` | Overwrite an existing `platform.yml`. Without it, the command stops with exit code 1 and leaves the file alone. |

```bash
quicketl platform init
quicketl platform init acme-data --warehouse databricks
```

The starter spec has one domain (`core`), three roles (`loader`, `transformer`, `analyst`), no SSO, no network rules and no sources. Each section has a comment saying what to change.

### platform validate

Check a platform spec and print a short summary.

```bash
quicketl platform validate [spec_file]
```

`spec_file` defaults to `platform.yml` in the current folder.

```bash
quicketl platform validate
quicketl platform validate examples/06-platform-spec/platform.yml
```

On success it prints the warehouse, environments, layers, and how many domains, roles and sources the spec defines. On failure it lists each problem and exits with code 1. A problem in one field shows where it is, for example `roles -> 1 -> access -> marts: Input should be 'read' or 'write'`. Problems with references between sections, such as a role naming a layer that does not exist, are checked after every field is valid.

### platform scaffold

Generate a project from a spec. Needs `git`.

```bash
quicketl platform scaffold [spec_file] [--dest DIR] [--ref TAG] [--template URL_OR_PATH]
```

### platform update

Apply `platform.yml` and template changes to a generated project. The project must be in git with everything committed.

```bash
quicketl platform update [project] [--ref TAG]
```

Both commands are explained, with every option and common errors, in [Scaffold and Update a Platform](../platform/scaffold.md).

---

## info {#info}

Display QuickETL version and backend information.

### Usage

```bash
quicketl info [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--backends` | `-b` | Show available backends |
| `--check` | `-c` | Check backend availability |

### Examples

```bash
# Version info
quicketl info

# List backends with availability check
quicketl info --backends --check
```

### Output

```
QuickETL v0.1.0
Python 3.12.0
```

With `--backends --check`:

```
Available Backends
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Backend   ┃ Name           ┃ Status         ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ duckdb    │ DuckDB         │ OK             │
│ polars    │ Polars         │ OK             │
│ spark     │ Apache Spark   │ Not installed  │
│ snowflake │ Snowflake      │ Not installed  │
└───────────┴────────────────┴────────────────┘
```

---

## schema {#schema}

Output JSON schema for pipeline configuration (for IDE autocompletion).

### Usage

```bash
quicketl schema [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path (default: stdout) |
| `--indent` | `-i` | JSON indentation level (default: 2) |

### Examples

```bash
# Output to stdout
quicketl schema

# Save to file
quicketl schema -o .quicketl-schema.json
```

### VS Code Integration

```bash
quicketl schema -o .quicketl-schema.json
```

Then in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    ".quicketl-schema.json": ["pipelines/*.yml"]
  }
}
```

---

## Shell Completion

Enable tab completion for commands and options:

```bash
# Bash
quicketl --install-completion bash

# Zsh
quicketl --install-completion zsh

# Fish
quicketl --install-completion fish
```

## Environment Variables

The CLI respects environment variables for configuration:

```bash
export DATABASE_URL=postgresql://localhost/db
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
quicketl run pipeline.yml
```

See [Environment Variables](environment-variables.md) for the full list.
