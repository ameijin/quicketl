# JSON Schema for IDEs

ETLX provides JSON Schema support for IDE autocompletion and validation.

## Generate Schema

Export the JSON schema:

```bash
# To stdout
quicketl schema

# To file
quicketl schema -o .quicketl-schema.json

# With custom indentation
quicketl schema -o .quicketl-schema.json --indent 4
```

## VS Code Setup

### Option 1: YAML Extension Settings

1. Install the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
2. Generate the schema: `etlx schema -o .etlx-schema.json`
3. Add to `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    ".etlx-schema.json": ["pipelines/*.yml", "pipelines/**/*.yml"]
  }
}
```

### Option 2: Inline Schema Reference

Add a schema reference at the top of your YAML file:

```yaml
# yaml-language-server: $schema=.etlx-schema.json
name: my_pipeline
engine: duckdb
...
```

### Option 3: Project-Wide Schema

Create `.vscode/settings.json` in your project:

```json
{
  "yaml.schemas": {
    "https://raw.githubusercontent.com/etlx/etlx/main/schema.json": [
      "pipelines/*.yml"
    ]
  },
  "yaml.customTags": [
    "!include scalar"
  ]
}
```

## PyCharm / IntelliJ Setup

1. Generate the schema: `etlx schema -o .etlx-schema.json`
2. Go to **Settings** → **Languages & Frameworks** → **Schemas and DTDs** → **JSON Schema Mappings**
3. Click **+** to add a new mapping:
   - **Name**: ETLX Pipeline
   - **Schema file or URL**: Select `.etlx-schema.json`
   - **File path pattern**: `pipelines/*.yml`

## Features

With JSON Schema enabled, you get:

### Autocompletion

Type and see suggestions:

```yaml
source:
  type: f  # Suggests: file
```

### Validation

Errors are highlighted:

```yaml
source:
  type: invalid  # Error: must be 'file' or 'database'
```

### Documentation

Hover over fields to see descriptions:

```yaml
transforms:
  - op: filter  # Hover shows: "Filter rows using a SQL-like predicate"
```

### Required Fields

Missing required fields are highlighted:

```yaml
source:
  type: file
  # Error: 'path' is required
```

## Schema Contents

The generated schema includes:

- All source types (`file`, `database`)
- All sink types (`file`, `database`)
- All 12 transform operations
- All 5 quality checks
- All configuration options
- Descriptions for every field

Example schema structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ETLX Pipeline Configuration",
  "type": "object",
  "required": ["name", "source", "sink"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique pipeline identifier"
    },
    "engine": {
      "type": "string",
      "enum": ["duckdb", "polars", "datafusion", "spark", "pandas"],
      "default": "duckdb"
    },
    "transforms": {
      "type": "array",
      "items": {
        "oneOf": [
          { "$ref": "#/definitions/SelectTransform" },
          { "$ref": "#/definitions/FilterTransform" },
          ...
        ]
      }
    }
  }
}
```

## Keeping Schema Updated

Regenerate the schema when ETLX is updated:

```bash
# After upgrading ETLX
pip install --upgrade quicketl
quicketl schema -o .quicketl-schema.json
```

Add to your `Makefile` or scripts:

```makefile
.PHONY: schema
schema:
	etlx schema -o .etlx-schema.json
```

## CI/CD Validation

Validate pipelines in CI:

```yaml title=".github/workflows/validate.yml"
name: Validate Pipelines

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install ETLX
        run: pip install quicketl

      - name: Validate all pipelines
        run: |
          for f in pipelines/*.yml; do
            echo "Validating $f"
            etlx validate "$f"
          done
```

## Troubleshooting

### Schema Not Loading

1. Check the file path in settings matches your pipeline location
2. Ensure the schema file exists and is valid JSON
3. Restart your IDE after changing settings

### Outdated Completions

Regenerate the schema after updating ETLX:

```bash
quicketl schema -o .quicketl-schema.json
```

### Custom Transforms

If you add custom transforms, they won't appear in the schema. The schema covers built-in operations only.

## Related

- [Pipeline YAML](pipeline-yaml.md) - Configuration reference
- [CLI: schema](../../cli/schema.md) - Schema command details
