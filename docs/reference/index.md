# Reference

Technical reference documentation for ETLX.

## Reference Guides

| Guide | Description |
|-------|-------------|
| [Expressions](expressions.md) | SQL expression syntax |
| [Data Types](data-types.md) | Type system and mapping |
| [Environment Variables](environment-variables.md) | Configuration variables |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

## Expression Language

ETLX uses SQL-compatible expressions for filters, derived columns, and checks:

```yaml
transforms:
  - op: filter
    predicate: amount > 100 AND status = 'active'

  - op: derive_column
    name: total
    expr: quantity * price * (1 - discount)
```

[Expression Reference →](expressions.md)

## Data Types

Standard types that map across all backends:

| Type | Description |
|------|-------------|
| `string` | Text data |
| `int` | Integer numbers |
| `float` | Floating-point |
| `bool` | Boolean |
| `date` | Calendar date |
| `timestamp` | Date and time |
| `decimal` | Precise decimal |

[Data Types Reference →](data-types.md)

## Environment Variables

Configure connections and credentials via environment:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_USER=etlx
export AWS_REGION=us-east-1
```

[Environment Variables →](environment-variables.md)

## Troubleshooting

Common issues and solutions:

- Installation problems
- Configuration errors
- Runtime failures
- Performance issues

[Troubleshooting Guide →](troubleshooting.md)
