"""CLI command: etlx init

Initialize a new ETLX project or pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Initialize a new ETLX project or pipeline")


SAMPLE_PIPELINE = '''# Example ETLX Pipeline Configuration
name: {name}
description: Sample ETL pipeline

# Engine to use for processing
engine: duckdb

# Data source configuration
source:
  type: file
  path: data/input.parquet
  format: parquet

# Transform steps
transforms:
  # Filter rows
  - type: filter
    predicate: amount > 0

  # Add computed column
  - type: derive_column
    name: total_with_tax
    expr: amount * 1.1

  # Select final columns
  - type: select
    columns: [id, name, amount, total_with_tax]

# Quality checks
checks:
  - type: not_null
    columns: [id, name, amount]
  - type: row_count
    min: 1

# Output destination
sink:
  type: file
  path: data/output.parquet
  format: parquet
'''

PROJECT_STRUCTURE = '''# ETLX Project Structure

## Directory Layout
```
{name}/
├── pipelines/           # Pipeline YAML configurations
│   └── sample.yml
├── data/                # Input/output data
│   ├── input/
│   └── output/
├── scripts/             # Custom Python scripts
└── .env                 # Environment variables
```

## Getting Started

1. Edit `pipelines/sample.yml` with your pipeline configuration
2. Run: `etlx run pipelines/sample.yml`
3. Validate: `etlx validate pipelines/sample.yml`

## Environment Variables

Set variables in `.env` or export them:
```bash
export ETLX_DATABASE_URL="postgresql://localhost/mydb"
```

Reference in YAML with `${{VAR_NAME}}`:
```yaml
source:
  type: database
  connection: ${{DATABASE_URL}}
```
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
        Optional[Path],
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
        etlx init my_project           # Create full project
        etlx init my_pipeline -p       # Create single pipeline file
        etlx init my_project -o ./projects/
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
    console.print(f"\nRun with: [cyan]etlx run {file_path}[/cyan]")


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
        project_path / "data" / "input",
        project_path / "data" / "output",
        project_path / "scripts",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create files
    files = {
        project_path / "pipelines" / "sample.yml": SAMPLE_PIPELINE.format(name="sample_pipeline"),
        project_path / "README.md": PROJECT_STRUCTURE.format(name=name),
        project_path / ".env": ENV_TEMPLATE,
        project_path / ".gitignore": "# Data files\ndata/output/\n\n# Environment\n.env\n\n# Python\n__pycache__/\n*.pyc\n",
    }

    for file_path, content in files.items():
        file_path.write_text(content)
        console.print(f"[green]Created:[/green] {file_path}")

    console.print(f"\n[bold green]Project created:[/bold green] {project_path}")
    console.print(f"\nNext steps:")
    console.print(f"  1. cd {name}")
    console.print(f"  2. Edit pipelines/sample.yml")
    console.print(f"  3. etlx run pipelines/sample.yml")


if __name__ == "__main__":
    app()
