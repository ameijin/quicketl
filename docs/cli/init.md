# quicketl init

Initialize a new QuickETL project or pipeline file.

## Usage

```bash
quicketl init <name> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Project or pipeline name |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--pipeline` | `-p` | Create pipeline file only (not full project) |
| `--output` | `-o` | Output directory (default: current) |
| `--force` | `-f` | Overwrite existing files |

## Examples

### Create Project

```bash
quicketl init my_project
cd my_project
```

Creates:

```
my_project/
├── pipelines/
│   └── sample.yml      # Working sample pipeline
├── data/
│   └── sales.csv       # Sample data
├── README.md
├── .env
└── .gitignore
```

### Create Pipeline Only

```bash
quicketl init my_pipeline -p
```

Creates: `my_pipeline.yml`

### Specify Output Directory

```bash
quicketl init my_project -o ./projects/
```

### Force Overwrite

```bash
quicketl init my_project --force
```

## Project Contents

### Sample Pipeline

The generated `sample.yml` is runnable immediately:

```bash
cd my_project
quicketl run pipelines/sample.yml
```

### Sample Data

`data/sales.csv` contains sample records for testing.

### Environment Template

`.env` contains placeholder environment variables.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (directory exists, etc.) |

## Related

- [Quick Start](../getting-started/quickstart.md) - Using generated project
- [Project Structure](../getting-started/project-structure.md) - Organization best practices
