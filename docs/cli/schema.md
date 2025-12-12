# etlx schema

Output JSON schema for pipeline configuration.

## Usage

```bash
etlx schema [options]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path (default: stdout) |
| `--indent` | `-i` | JSON indentation level (default: 2) |

## Examples

### Output to Stdout

```bash
etlx schema
```

### Save to File

```bash
etlx schema -o .etlx-schema.json
```

### Custom Indentation

```bash
etlx schema -o schema.json --indent 4
```

## Use Cases

### VS Code Integration

```bash
etlx schema -o .etlx-schema.json
```

Then in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    ".etlx-schema.json": ["pipelines/*.yml"]
  }
}
```

### Generate for Distribution

```bash
etlx schema -o docs/schema.json --indent 2
```

## Output Format

The schema follows JSON Schema draft-07:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ETLX Pipeline Configuration",
  "type": "object",
  "required": ["name", "source", "sink"],
  "properties": {
    "name": { "type": "string" },
    "engine": { "enum": ["duckdb", "polars", ...] },
    ...
  }
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |

## Related

- [JSON Schema for IDEs](../user-guide/configuration/json-schema.md) - IDE setup guide
