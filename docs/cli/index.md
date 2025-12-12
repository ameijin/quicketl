# CLI Reference

QuickETL provides a command-line interface for running and managing pipelines.

## Commands

| Command | Description |
|---------|-------------|
| [`run`](run.md) | Execute a pipeline |
| [`validate`](validate.md) | Validate configuration |
| [`init`](init.md) | Create new project or pipeline |
| [`info`](info.md) | Display version and backend info |
| [`schema`](schema.md) | Output JSON schema |

## Global Options

```bash
quicketl --version    # Show version
quicketl --help       # Show help
```

## Quick Start

```bash
# Create project with sample data
quicketl init my_project
cd my_project

# Run the sample pipeline
quicketl run pipelines/sample.yml

# Validate without running
quicketl validate pipelines/sample.yml
```

## Common Usage

### Run Pipeline

```bash
quicketl run pipeline.yml
quicketl run pipeline.yml --var DATE=2025-01-15
quicketl run pipeline.yml --engine polars
quicketl run pipeline.yml --dry-run
```

### Validate Configuration

```bash
quicketl validate pipeline.yml
quicketl validate pipeline.yml --verbose
```

### Check Backends

```bash
quicketl info --backends --check
```

### Generate Schema

```bash
quicketl schema -o .quicketl-schema.json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation, execution, etc.) |
| 2 | Command not found |

## Shell Completion

Enable tab completion:

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
quicketl run pipeline.yml
```

See [Environment Variables](../reference/environment-variables.md) for details.
