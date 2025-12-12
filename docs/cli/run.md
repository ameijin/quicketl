# quicketl run

Execute a pipeline from a YAML configuration file.

## Usage

```bash
quicketl run <config_file> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `config_file` | Yes | Path to pipeline YAML file |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--engine` | `-e` | Override compute engine |
| `--var` | `-v` | Set variable (KEY=VALUE) |
| `--dry-run` | | Execute without writing output |
| `--fail-on-checks` | | Fail on quality check failure (default) |
| `--no-fail-on-checks` | | Continue despite check failures |
| `--verbose` | `-V` | Enable verbose logging |
| `--json` | `-j` | Output result as JSON |

## Examples

### Basic Run

```bash
quicketl run pipeline.yml
```

### With Variables

```bash
quicketl run pipeline.yml --var DATE=2025-01-15
quicketl run pipeline.yml --var DATE=2025-01-15 --var REGION=north
```

### Override Engine

```bash
quicketl run pipeline.yml --engine polars
quicketl run pipeline.yml --engine spark
```

### Dry Run

Execute transforms without writing to sink:

```bash
quicketl run pipeline.yml --dry-run
```

### Continue on Check Failure

```bash
quicketl run pipeline.yml --no-fail-on-checks
```

### JSON Output

For scripting and automation:

```bash
quicketl run pipeline.yml --json
```

Output:

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

### Verbose Logging

```bash
quicketl run pipeline.yml --verbose
```

## Output

Successful run:

```
Running pipeline: sales_etl
  Process daily sales data
  Engine: duckdb

╭───────────────────────── Pipeline: sales_etl ────────────────────────────────╮
│ SUCCESS                                                                      │
╰─────────────────────────────────── Duration: 245.3ms ────────────────────────╯

Steps
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Step              ┃ Type          ┃ Status ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ read_source       │ file          │ OK     │   45.2ms │
│ transform_0       │ filter        │ OK     │    0.3ms │
│ quality_checks    │ checks        │ OK     │   12.4ms │
│ write_sink        │ file          │ OK     │    8.1ms │
└───────────────────┴───────────────┴────────┴──────────┘

Quality Checks: PASSED (2/2 passed)

Rows processed: 1000
Rows written: 950
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Pipeline failed |

## Related

- [validate](validate.md) - Validate without running
- [Pipeline YAML](../user-guide/configuration/pipeline-yaml.md) - Configuration reference
- [Variable Substitution](../user-guide/configuration/variables.md) - Using `--var`
