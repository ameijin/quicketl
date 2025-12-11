"""CLI command: etlx validate

Validate an ETLX pipeline configuration file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from etlx.config.loader import load_pipeline_config

console = Console()
app = typer.Typer(help="Validate pipeline configuration")


@app.callback(invoke_without_command=True)
def validate(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to pipeline YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed configuration",
        ),
    ] = False,
) -> None:
    """Validate an ETLX pipeline configuration file.

    Checks:
    - YAML syntax
    - Required fields
    - Type correctness
    - Source/sink configuration
    - Transform/check definitions

    Examples:
        etlx validate pipeline.yml
        etlx validate pipeline.yml --verbose
    """
    try:
        # Load and validate configuration
        config = load_pipeline_config(str(config_file))

        # Success panel
        panel = Panel(
            f"[green]Configuration is valid[/green]",
            title=f"Pipeline: {config.name}",
            border_style="green",
        )
        console.print(panel)

        if verbose:
            _display_config_details(config)
        else:
            # Brief summary
            console.print(f"\n  Engine: {config.engine}")
            console.print(f"  Source: {config.source.type}")
            console.print(f"  Transforms: {len(config.transforms)}")
            console.print(f"  Checks: {len(config.checks)}")
            console.print(f"  Sink: {config.sink.type}")

        raise typer.Exit(0)

    except ValidationError as e:
        panel = Panel(
            f"[red]Configuration is invalid[/red]",
            title="Validation Failed",
            border_style="red",
        )
        console.print(panel)

        # Show validation errors
        console.print("\n[bold red]Errors:[/bold red]")
        for error in e.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            msg = error["msg"]
            console.print(f"  [red]-[/red] {loc}: {msg}")

        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1)


def _display_config_details(config) -> None:
    """Display detailed configuration as a tree."""
    tree = Tree(f"[bold]{config.name}[/bold]")

    # Description
    if config.description:
        tree.add(f"Description: {config.description}")

    # Engine
    tree.add(f"Engine: [cyan]{config.engine}[/cyan]")

    # Source
    source_branch = tree.add("[bold]Source[/bold]")
    source_branch.add(f"Type: {config.source.type}")
    for key, value in config.source.model_dump().items():
        if key != "type" and value:
            source_branch.add(f"{key}: {value}")

    # Transforms
    if config.transforms:
        transforms_branch = tree.add(f"[bold]Transforms[/bold] ({len(config.transforms)})")
        for i, transform in enumerate(config.transforms):
            t_dict = transform.model_dump()
            t_type = t_dict.pop("type", transform.__class__.__name__)
            t_branch = transforms_branch.add(f"[{i + 1}] {t_type}")
            for key, value in t_dict.items():
                if value:
                    t_branch.add(f"{key}: {value}")

    # Checks
    if config.checks:
        checks_branch = tree.add(f"[bold]Checks[/bold] ({len(config.checks)})")
        for i, check in enumerate(config.checks):
            c_dict = check.model_dump()
            c_type = c_dict.pop("type", check.__class__.__name__)
            c_branch = checks_branch.add(f"[{i + 1}] {c_type}")
            for key, value in c_dict.items():
                if value:
                    c_branch.add(f"{key}: {value}")

    # Sink
    sink_branch = tree.add("[bold]Sink[/bold]")
    sink_branch.add(f"Type: {config.sink.type}")
    for key, value in config.sink.model_dump().items():
        if key != "type" and value:
            sink_branch.add(f"{key}: {value}")

    console.print(tree)


if __name__ == "__main__":
    app()
