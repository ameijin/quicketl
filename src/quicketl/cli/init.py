"""CLI command: quicketl init

Initialize a new ETLX project or pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Initialize a new ETLX project or pipeline")


SAMPLE_PIPELINE = '''# Example ETLX Pipeline Configuration
# Run this pipeline with: quicketl run pipelines/sample.yml
name: {name}
description: Sample ETL pipeline - processes sales data

# Engine to use for processing (duckdb is fast and included by default)
engine: duckdb

# Data source configuration
source:
  type: file
  path: data/sales.csv
  format: csv

# Transform steps (applied in order)
transforms:
  # Filter out negative amounts
  - op: filter
    predicate: amount > 0

  # Add computed columns
  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1

  - op: derive_column
    name: category_upper
    expr: upper(category)

  # Aggregate by category
  - op: aggregate
    group_by: [category]
    aggs:
      total_sales: sum(amount)
      total_with_tax: sum(total_with_tax)
      order_count: count(*)

  # Sort by total sales descending
  - op: sort
    by: [total_sales]
    descending: true

# Quality checks (run after transforms)
checks:
  - type: not_null
    columns: [category, total_sales]
  - type: row_count
    min: 1

# Output destination
sink:
  type: file
  path: data/output/sales_summary.parquet
  format: parquet
'''

PROJECT_STRUCTURE = '''# {name}

An ETLX data pipeline project.

## Quick Start

```bash
# Run the sample pipeline
quicketl run pipelines/sample.yml

# View the output
cat data/output/sales_summary.parquet  # or use DuckDB/pandas to read
```

## Project Structure

```
{name}/
├── pipelines/           # Pipeline YAML configurations
│   └── sample.yml       # Sample pipeline (ready to run!)
├── data/
│   ├── sales.csv        # Sample input data
│   └── output/          # Pipeline outputs
├── scripts/             # Custom Python scripts
└── .env                 # Environment variables
```

## Common Commands

```bash
# Run a pipeline
quicketl run pipelines/sample.yml

# Run with variables
quicketl run pipelines/sample.yml --var DATE=2025-01-01

# Validate configuration without running
quicketl validate pipelines/sample.yml

# Dry run (transforms but no output)
quicketl run pipelines/sample.yml --dry-run

# Create a new pipeline
quicketl init my_pipeline -p
```

## Environment Variables

Set variables in `.env` or export them:
```bash
export DATABASE_URL="postgresql://localhost/mydb"
```

Reference in YAML with `${{VAR_NAME}}`:
```yaml
source:
  type: database
  connection: ${{DATABASE_URL}}
```

## Learn More

- Available transforms: filter, select, derive_column, aggregate, join, sort, etc.
- Quality checks: not_null, unique, row_count, accepted_values, expression
- Run `quicketl info --backends` to see available compute engines
- Run `quicketl schema` to output JSON schema for IDE autocompletion
'''

ENV_TEMPLATE = '''# ETLX Environment Variables
# Reference these in pipeline YAML with ${VAR_NAME}

# Database connections
# DATABASE_URL=postgresql://user:pass@localhost/db

# Cloud storage credentials (if using S3/GCS/Azure)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# GOOGLE_APPLICATION_CREDENTIALS=

# Pipeline variables
# RUN_DATE=2025-01-01
'''

# Sample CSV data for the demo pipeline
SAMPLE_DATA_CSV = '''id,name,category,amount,date
1,Widget A,Electronics,99.99,2025-01-15
2,Widget B,Electronics,149.99,2025-01-15
3,Gadget X,Home,29.99,2025-01-16
4,Gadget Y,Home,49.99,2025-01-16
5,Thingamajig,Electronics,199.99,2025-01-17
6,Doohickey,Office,15.99,2025-01-17
7,Whatchamacallit,Home,89.99,2025-01-18
8,Gizmo,Electronics,299.99,2025-01-18
9,Contraption,Office,45.99,2025-01-19
10,Apparatus,Office,75.99,2025-01-19
11,Invalid Item,Electronics,-10.00,2025-01-20
12,Another Widget,Electronics,125.50,2025-01-20
'''


@app.callback(invoke_without_command=True)
def init(
    name: Annotated[
        str,
        typer.Argument(
            help="Project or pipeline name",
        ),
    ],
    pipeline_only: Annotated[
        bool,
        typer.Option(
            "--pipeline",
            "-p",
            help="Create only a pipeline YAML file (not full project)",
        ),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory (default: current directory)",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing files",
        ),
    ] = False,
) -> None:
    """Initialize a new ETLX project or pipeline.

    Creates project structure with:
    - Sample pipeline configuration
    - Directory structure
    - Environment template

    Examples:
        quicketl init my_project           # Create full project
        quicketl init my_pipeline -p       # Create single pipeline file
        quicketl init my_project -o ./projects/
    """
    base_path = output_dir or Path.cwd()

    if pipeline_only:
        _create_pipeline(name, base_path, force)
    else:
        _create_project(name, base_path, force)


def _create_pipeline(name: str, base_path: Path, force: bool) -> None:
    """Create a single pipeline YAML file."""
    file_name = f"{name}.yml" if not name.endswith(".yml") else name
    file_path = base_path / file_name

    if file_path.exists() and not force:
        console.print(f"[red]Error:[/red] {file_path} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    pipeline_name = name.replace(".yml", "").replace("-", "_")
    content = SAMPLE_PIPELINE.format(name=pipeline_name)

    file_path.write_text(content)
    console.print(f"[green]Created:[/green] {file_path}")
    console.print(f"\nRun with: [cyan]quicketl run {file_path}[/cyan]")


def _create_project(name: str, base_path: Path, force: bool) -> None:
    """Create a full project structure."""
    project_path = base_path / name

    if project_path.exists() and not force:
        console.print(f"[red]Error:[/red] {project_path} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    # Create directories
    dirs = [
        project_path,
        project_path / "pipelines",
        project_path / "data",
        project_path / "data" / "output",
        project_path / "scripts",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create files
    files = {
        project_path / "pipelines" / "sample.yml": SAMPLE_PIPELINE.format(name="sample_pipeline"),
        project_path / "data" / "sales.csv": SAMPLE_DATA_CSV.strip(),
        project_path / "README.md": PROJECT_STRUCTURE.format(name=name),
        project_path / ".env": ENV_TEMPLATE,
        project_path / ".gitignore": "# Data files\ndata/output/\n\n# Environment\n.env\n\n# Python\n__pycache__/\n*.pyc\n",
    }

    for file_path, content in files.items():
        file_path.write_text(content)
        console.print(f"[green]Created:[/green] {file_path}")

    console.print(f"\n[bold green]Project created:[/bold green] {project_path}")
    console.print("\n[bold]Try it now:[/bold]")
    console.print(f"  cd {name} && quicketl run pipelines/sample.yml")
    console.print("\n[dim]This will process the sample sales data and output a summary to data/output/[/dim]")


if __name__ == "__main__":
    app()
