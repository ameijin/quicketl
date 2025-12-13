# CLI Reference

QuickETL provides a command-line interface for running and managing pipelines.

## Quick Reference

| Command | Description |
|---------|-------------|
| [`run`](#run) | Execute a pipeline |
| [`validate`](#validate) | Validate configuration |
| [`init`](#init) | Create new project or pipeline |
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
