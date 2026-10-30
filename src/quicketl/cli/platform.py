"""CLI commands: quicketl platform

Work with platform specs (platform.yml).
"""

from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path
from typing import Annotated, cast

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from quicketl.platform.scaffold import (
    TEMPLATE_SOURCE,
    ScaffoldError,
    default_ref,
    template_name,
)
from quicketl.platform.scaffold import scaffold as scaffold_project
from quicketl.platform.scaffold import update as update_project
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


def _load_spec(path: Path) -> PlatformSpec:
    """Load a spec, or print why it is unusable and exit 1."""
    try:
        return load_platform_spec(path)
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

    \b
    Examples:
      quicketl platform validate
      quicketl platform validate path/to/platform.yml
    """
    spec = _load_spec(spec_file)
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


@app.command()
def scaffold(
    spec_file: Annotated[
        Path,
        typer.Argument(help="Path to the platform spec"),
    ] = Path(PLATFORM_FILE),
    dest: Annotated[
        Path | None,
        typer.Option("--dest", "-d", help="Folder to generate into (default: the spec's folder)"),
    ] = None,
    ref: Annotated[
        str | None,
        typer.Option(
            "--ref", "-r", help="Template git tag or commit (default: v<quicketl version>)"
        ),
    ] = None,
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Template repo URL or local path"),
    ] = TEMPLATE_SOURCE,
) -> None:
    """Generate a platform project from a spec.

    Validates the spec, picks the template for its warehouse and
    orchestrator, and renders it. Needs git installed.

    \b
    Examples:
      quicketl platform scaffold
      quicketl platform scaffold platform.yml --dest ../acme-platform
      quicketl platform scaffold --ref v2.0.0
    """
    spec = _load_spec(spec_file)
    target = dest or spec_file.parent
    try:
        scaffold_project(spec, target, template=template, ref=ref)
    except ScaffoldError as e:
        console.print(f"[red]Error:[/red] {escape(str(e))}")
        raise typer.Exit(1) from None

    copied_spec = target / PLATFORM_FILE
    if not copied_spec.exists():
        shutil.copyfile(spec_file, copied_spec)

    console.print(
        f"[green]Generated[/green] {escape(str(target))} "
        f"from the {template_name(spec)} template ({ref or default_ref()})"
    )
    console.print("Next: read README.md there, then commit the project to git.")


@app.command()
def update(
    project: Annotated[
        Path,
        typer.Argument(help="Generated project folder"),
    ] = Path(),
    ref: Annotated[
        str | None,
        typer.Option(
            "--ref", "-r", help="Template git tag or commit (default: v<quicketl version>)"
        ),
    ] = None,
) -> None:
    """Apply platform.yml and template changes to a generated project.

    Reads the project's platform.yml. The project must be a git repo with
    everything committed. Clashes with your own edits are left as inline
    conflict markers to resolve.

    \b
    Examples:
      quicketl platform update
      quicketl platform update ../acme-platform --ref v2.1.0
    """
    spec = _load_spec(project / PLATFORM_FILE)
    try:
        update_project(spec, project, ref=ref)
    except ScaffoldError as e:
        console.print(f"[red]Error:[/red] {escape(str(e))}")
        raise typer.Exit(1) from None

    console.print(f"[green]Updated[/green] {escape(str(project))} ({ref or default_ref()})")
    console.print("Next: review the changes with git diff and resolve any conflict markers.")
