"""CLI commands: quicketl platform

Work with platform specs (platform.yml).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, cast

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from quicketl.platform.spec import (
    PLATFORM_FILE,
    PlatformSpec,
    PlatformSpecError,
    WarehouseType,
    load_platform_spec,
)
from quicketl.platform.starter import default_platform_name, render_starter_spec

console = Console()
app = typer.Typer(help="Work with platform specs (platform.yml)", no_args_is_help=True)


class WarehouseChoice(str, Enum):
    """CLI choices for `--warehouse`; values match `WarehouseType`."""

    snowflake = "snowflake"
    databricks = "databricks"
    redshift_serverless = "redshift_serverless"


def _print_errors(e: ValidationError) -> None:
    console.print("\n[bold red]Errors:[/bold red]")
    for error in e.errors():
        loc = " -> ".join(str(part) for part in error["loc"]) or "(top level)"
        console.print(f"  [red]-[/red] {escape(loc)}: {escape(error['msg'])}")


@app.command()
def init(
    directory: Annotated[
        Path,
        typer.Argument(help="Folder to write platform.yml into (created if missing)"),
    ] = Path(),
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Platform name (default: from the folder name)"),
    ] = None,
    warehouse: Annotated[
        WarehouseChoice,
        typer.Option("--warehouse", "-w", help="Warehouse the platform runs on"),
    ] = WarehouseChoice.snowflake,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite an existing platform.yml"),
    ] = False,
) -> None:
    """Write a commented starter platform.yml.

    Edit the file, then check it with `quicketl platform validate`.

    \b
    Examples:
      quicketl platform init
      quicketl platform init acme-data --warehouse databricks
      quicketl platform init --name acme_data --force
    """
    target = directory / PLATFORM_FILE
    if target.exists() and not force:
        console.print(
            f"[red]Error:[/red] {escape(str(target))} already exists. Use --force to overwrite it."
        )
        raise typer.Exit(1)

    platform_name = name or default_platform_name(directory.resolve().name)
    text = render_starter_spec(platform_name, cast("WarehouseType", warehouse.value))
    try:
        PlatformSpec.model_validate(yaml.safe_load(text))
    except ValidationError as e:
        console.print("[red]Error:[/red] the starter spec would be invalid.")
        _print_errors(e)
        raise typer.Exit(1) from None

    directory.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {escape(str(target))} for platform {platform_name!r}")
    console.print("Next: edit it, then run [bold]quicketl platform validate[/bold]")


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
        _print_errors(e)
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
