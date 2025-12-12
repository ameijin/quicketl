# Configuration

ETLX pipelines can be configured using YAML files or the Python API. This section covers configuration in detail.

## Overview

<div class="grid cards" markdown>

-   :material-file-document:{ .lg .middle } **Pipeline YAML**

    ---

    Complete YAML schema reference.

    [:octicons-arrow-right-24: Pipeline YAML](pipeline-yaml.md)

-   :material-variable:{ .lg .middle } **Variable Substitution**

    ---

    Dynamic configuration with variables.

    [:octicons-arrow-right-24: Variables](variables.md)

-   :material-code-json:{ .lg .middle } **JSON Schema**

    ---

    IDE autocompletion and validation.

    [:octicons-arrow-right-24: JSON Schema](json-schema.md)

</div>

## Pipeline Structure

Every pipeline has this basic structure:

```yaml
name: pipeline_name           # Required: Unique identifier
description: What it does     # Optional: Human description
engine: duckdb                # Optional: Compute backend (default: duckdb)

source:                       # Required: Where to read data
  type: file
  path: input.parquet

transforms:                   # Optional: List of transformations
  - op: filter
    predicate: amount > 0

checks:                       # Optional: Quality validations
  - type: not_null
    columns: [id]

sink:                         # Required: Where to write data
  type: file
  path: output.parquet
```

## Configuration Validation

ETLX validates configurations using Pydantic:

- **Type checking** - Correct types for all fields
- **Required fields** - Missing fields are reported
- **Unknown fields** - Extra fields cause errors
- **Value constraints** - Invalid values are rejected

Validate without running:

```bash
quicketl validate pipeline.yml
```

## YAML vs Python

| Feature | YAML | Python |
|---------|------|--------|
| Simplicity | Simple, declarative | More verbose |
| Variables | `${VAR}` syntax | Dict or env |
| Dynamic logic | Limited | Full Python |
| Reusability | Copy/paste | Functions, classes |
| Version control | Easy diff | Easy diff |
| IDE support | JSON Schema | Type hints |

**Recommendation**: Use YAML for most pipelines. Use Python when you need:

- Complex conditional logic
- Dynamic pipeline generation
- Integration with existing Python code
- Custom transforms or checks
