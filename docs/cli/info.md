# etlx info

Display ETLX version and backend information.

## Usage

```bash
etlx info [options]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--backends` | `-b` | Show available backends |
| `--check` | `-c` | Check backend availability |

## Examples

### Version Info

```bash
etlx info
```

Output:

```
ETLX v0.1.0
Python 3.12.0
```

### List Backends

```bash
etlx info --backends
```

### Check Backend Availability

```bash
etlx info --backends --check
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
etlx info --backends --check
```

### Scripting

```bash
if etlx info --backends | grep -q "spark.*OK"; then
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
