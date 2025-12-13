"""CLI command: quicketl schema

Output JSON schema for pipeline configuration (IDE support).
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 - required at runtime for Typer
from typing import Annotated

import typer
from rich.console import Console

from quicketl.config.models import PipelineConfig

console = Console()
app = typer.Typer(help="Output JSON schema for pipeline configuration")


@app.callback(invoke_without_command=True)
def schema(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: stdout)",
        ),
    ] = None,
    indent: Annotated[
        int,
        typer.Option(
            "--indent",
            "-i",
            help="JSON indentation level",
        ),
    ] = 2,
) -> None:
    """Output JSON schema for QuickETL pipeline configuration.

    The schema can be used for IDE autocompletion and validation
    in YAML/JSON editors.

    Examples:
        quicketl schema                           # Print to stdout
        quicketl schema -o quicketl-schema.json   # Write to file
        quicketl schema --indent 4                # Custom indentation

    Usage with VS Code (YAML):
        1. Run: quicketl schema -o .quicketl-schema.json
        2. Add to your pipeline YAML:
           # yaml-language-server: $schema=.quicketl-schema.json
    """
    # Generate JSON schema from Pydantic model
    json_schema = PipelineConfig.model_json_schema()

    # Add schema metadata
    json_schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    json_schema["title"] = "QuickETL Pipeline Configuration"
    json_schema["description"] = "Schema for QuickETL pipeline YAML configuration files"

    # Format output
    schema_json = json.dumps(json_schema, indent=indent)

    if output:
        output.write_text(schema_json)
        console.print(f"[green]Schema written to:[/green] {output}")
    else:
        console.print(schema_json)


if __name__ == "__main__":
    app()
