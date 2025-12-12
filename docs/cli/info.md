# quicketl info

Display QuickETL version and backend information.

## Usage

```bash
quicketl info [options]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--backends` | `-b` | Show available backends |
| `--check` | `-c` | Check backend availability |

## Examples

### Version Info

```bash
quicketl info
```

Output:

```
QuickETL v0.1.0
Python 3.12.0
```

### List Backends

```bash
quicketl info --backends
```

### Check Backend Availability

```bash
quicketl info --backends --check
```

Output:

```
Available Backends
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Backend    ┃ Name            ┃ Description                  ┃ Status         ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ duckdb     │ DuckDB          │ Fast in-process database     │ OK             │
│ polars     │ Polars          │ Rust-powered DataFrames      │ OK             │
│ spark      │ Apache Spark    │ Distributed compute          │ Not installed  │
│ snowflake  │ Snowflake       │ Cloud data warehouse         │ Not installed  │
└────────────┴─────────────────┴──────────────────────────────┴────────────────┘
```

## Use Cases

### Verify Installation

```bash
quicketl info --backends --check
```

### Scripting

```bash
if quicketl info --backends | grep -q "spark.*OK"; then
  echo "Spark is available"
fi
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

## Related

- [Installation](../getting-started/installation.md) - Install backends
- [Backends](../user-guide/backends/index.md) - Backend details
