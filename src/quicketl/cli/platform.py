"""CLI commands: quicketl platform

Work with platform specs (platform.yml).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from quicketl.platform.spec import PLATFORM_FILE, PlatformSpecError, load_platform_spec

console = Console()
app = typer.Typer(help="Work with platform specs (platform.yml)", no_args_is_help=True)


@app.command()
def validate(
    spec_file: Annotated[
        Path,
        typer.Argument(help="Path to the platform spec"),
    ] = Path(PLATFORM_FILE),
) -> None:
    """Check a platform spec and print a short summary.

    Checks YAML syntax, required fields, names, and that every role and
    source refers to a layer or domain the spec defines.

    Examples:
        quicketl platform validate
        quicketl platform validate path/to/platform.yml
    """
    try:
        spec = load_platform_spec(spec_file)
    except PlatformSpecError as e:
        console.print(f"[red]Error:[/red] {escape(str(e))}")
        raise typer.Exit(1) from None
    except ValidationError as e:
        console.print(
            Panel(
                "[red]Platform spec is invalid[/red]",
                title="Validation Failed",
                border_style="red",
            )
        )
        console.print("\n[bold red]Errors:[/bold red]")
        for error in e.errors():
            loc = " -> ".join(str(part) for part in error["loc"]) or "(top level)"
            console.print(f"  [red]-[/red] {escape(loc)}: {escape(error['msg'])}")
        raise typer.Exit(1) from None

    console.print(
        Panel(
            "[green]Platform spec is valid[/green]",
            title=f"Platform: {spec.name}",
            border_style="green",
        )
    )
    console.print(f"\n  Warehouse: {spec.warehouse.type}")
    console.print(f"  Environments: {', '.join(spec.environments)}")
    console.print(f"  Layers: {', '.join(spec.layers)}")
    console.print(f"  Domains: {len(spec.domains)}")
    console.print(f"  Roles: {len(spec.roles)}")
    console.print(f"  Sources: {len(spec.sources)}")
    console.print(f"  SSO: {spec.sso.provider}")
    console.print(f"  Orchestrator: {spec.orchestrator.type} on {spec.orchestrator.hosting}")
