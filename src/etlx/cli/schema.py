"""CLI command: etlx schema

Output JSON schema for pipeline configuration (IDE support).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from etlx.config.models import PipelineConfig

console = Console()
app = typer.Typer(help="Output JSON schema for pipeline configuration")


@app.callback(invoke_without_command=True)
def schema(
    output: Annotated[
        Optional[Path],
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
    """Output JSON schema for ETLX pipeline configuration.

    The schema can be used for IDE autocompletion and validation
    in YAML/JSON editors.

    Examples:
        etlx schema                           # Print to stdout
        etlx schema -o etlx-schema.json       # Write to file
        etlx schema --indent 4                # Custom indentation

    Usage with VS Code (YAML):
        1. Run: etlx schema -o .etlx-schema.json
        2. Add to your pipeline YAML:
           # yaml-language-server: $schema=.etlx-schema.json
    """
    # Generate JSON schema from Pydantic model
    json_schema = PipelineConfig.model_json_schema()

    # Add schema metadata
    json_schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    json_schema["title"] = "ETLX Pipeline Configuration"
    json_schema["description"] = "Schema for ETLX pipeline YAML configuration files"

    # Format output
    schema_json = json.dumps(json_schema, indent=indent)

    if output:
        output.write_text(schema_json)
        console.print(f"[green]Schema written to:[/green] {output}")
    else:
        console.print(schema_json)


if __name__ == "__main__":
    app()
