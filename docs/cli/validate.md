# etlx validate

Validate a pipeline configuration without executing it.

## Usage

```bash
etlx validate <config_file> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `config_file` | Yes | Path to pipeline YAML file |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Show detailed configuration |

## Examples

### Basic Validation

```bash
etlx validate pipeline.yml
```

### Verbose Output

```bash
etlx validate pipeline.yml --verbose
```

## Output

### Valid Configuration

```
Configuration is valid

Pipeline: sales_etl
  Engine: duckdb
  Source: file (data/sales.parquet)
  Transforms: 3
  Checks: 2
  Sink: file (output/results.parquet)
```

### Invalid Configuration

```
Configuration is invalid

Errors:
  - transforms -> 0 -> op: Input should be 'select', 'filter', ...
    [input_value='invalid_op']
  - sink: Field required
```

## Use Cases

### CI/CD Validation

```yaml
# .github/workflows/validate.yml
- name: Validate pipelines
  run: |
    for f in pipelines/*.yml; do
      etlx validate "$f"
    done
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

for file in $(git diff --cached --name-only | grep 'pipelines/.*\.yml$'); do
  etlx validate "$file" || exit 1
done
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Configuration valid |
| 1 | Configuration invalid |

## Related

- [run](run.md) - Execute validated pipeline
- [Pipeline YAML](../user-guide/configuration/pipeline-yaml.md) - Configuration reference
