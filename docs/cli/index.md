# CLI Reference

ETLX provides a command-line interface for running and managing pipelines.

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
etlx --version    # Show version
etlx --help       # Show help
```

## Quick Start

```bash
# Create project with sample data
etlx init my_project
cd my_project

# Run the sample pipeline
etlx run pipelines/sample.yml

# Validate without running
etlx validate pipelines/sample.yml
```

## Common Usage

### Run Pipeline

```bash
etlx run pipeline.yml
etlx run pipeline.yml --var DATE=2025-01-15
etlx run pipeline.yml --engine polars
etlx run pipeline.yml --dry-run
```

### Validate Configuration

```bash
etlx validate pipeline.yml
etlx validate pipeline.yml --verbose
```

### Check Backends

```bash
etlx info --backends --check
```

### Generate Schema

```bash
etlx schema -o .etlx-schema.json
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
etlx --install-completion bash

# Zsh
etlx --install-completion zsh

# Fish
etlx --install-completion fish
```

## Environment Variables

The CLI respects environment variables for configuration:

```bash
export DATABASE_URL=postgresql://localhost/db
etlx run pipeline.yml
```

See [Environment Variables](../reference/environment-variables.md) for details.
