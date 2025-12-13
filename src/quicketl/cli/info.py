"""CLI command: quicketl info

Display information about ETLX installation and available backends.
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - required at runtime for Typer
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from quicketl._version import __version__
from quicketl.engines.backends import list_backends

console = Console()
app = typer.Typer(help="Display ETLX information")


@app.callback(invoke_without_command=True)
def info(
    backends: Annotated[
        bool,
        typer.Option(
            "--backends",
            "-b",
            help="Show available backends",
        ),
    ] = False,
    check_imports: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Check which backends are importable",
        ),
    ] = False,
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="Show info about a specific pipeline config",
        ),
    ] = None,
) -> None:
    """Display ETLX version and configuration information.

    Examples:
        quicketl info                  # Show version info
        quicketl info --backends       # List available backends
        quicketl info --check          # Check backend availability
        quicketl info --config p.yml   # Show pipeline info
    """
    if config_file:
        _show_pipeline_info(config_file)
    elif backends or check_imports:
        _show_backends(check_imports)
    else:
        _show_version_info()


def _show_version_info() -> None:
    """Display version and installation info."""
    panel = Panel(
        f"[bold]ETLX Framework[/bold]\n"
        f"Version: {__version__}\n"
        f"Python ETL/ELT framework with Ibis backend support",
        title="quicketl",
        border_style="blue",
    )
    console.print(panel)

    console.print("\n[bold]Commands:[/bold]")
    console.print("  quicketl run <config>       Run a pipeline")
    console.print("  quicketl validate <config>  Validate configuration")
    console.print("  quicketl init <name>        Initialize new project")
    console.print("  quicketl info               Show this information")
    console.print("  quicketl info --backends    List available backends")


def _show_backends(check_imports: bool) -> None:
    """Display available backends."""
    table = Table(title="Available Backends")
    table.add_column("Backend", style="cyan")
    table.add_column("Name")
    table.add_column("Description")

    if check_imports:
        table.add_column("Status")

    for backend_info in list_backends():
        backend_id = backend_info["id"]

        status = ""
        if check_imports:
            status = _check_backend(backend_id)

        row = [
            backend_id,
            backend_info["name"],
            backend_info["description"],
        ]

        if check_imports:
            row.append(status)

        table.add_row(*row)

    console.print(table)

    if not check_imports:
        console.print("\nUse [cyan]quicketl info --check[/cyan] to verify backend availability")


def _check_backend(backend_name: str) -> str:
    """Check if a backend can be imported."""
    # Map backend names to ibis module names and install extras
    BACKEND_INFO: dict[str, dict[str, str | None]] = {
        "duckdb": {"module": "duckdb", "extra": "duckdb"},
        "polars": {"module": "polars", "extra": "polars"},
        "datafusion": {"module": "datafusion", "extra": "datafusion"},
        "pandas": {"module": "pandas", "extra": "pandas"},
        "spark": {"module": "pyspark", "extra": "spark", "note": "Requires Java 8/11/17"},
        "bigquery": {"module": "bigquery", "extra": "bigquery"},
        "snowflake": {"module": "snowflake", "extra": "snowflake"},
        "trino": {"module": "trino", "extra": "trino"},
        "postgres": {"module": "postgres", "extra": "postgres"},
        "mysql": {"module": "mysql", "extra": "mysql"},
        "clickhouse": {"module": "clickhouse", "extra": "clickhouse"},
        "sqlite": {"module": "sqlite", "extra": None},  # Built into ibis
    }

    info = BACKEND_INFO.get(backend_name)
    if not info:
        return "[dim]Unknown backend[/dim]"

    module_name = info["module"]
    extra = info["extra"]
    note = info.get("note", "")

    # Type narrowing - module is always present
    assert module_name is not None

    try:
        import ibis

        # Check if ibis has the backend module
        if not hasattr(ibis, module_name):
            # Escape brackets for Rich markup
            install_hint = f"pip install quicketl\\[{extra}]" if extra else "built-in"
            return f"[red]Not installed[/red] ({install_hint})"

        # For backends that can connect without credentials, test the connection
        backend_module = getattr(ibis, module_name)

        # These backends can create in-memory connections
        if backend_name in ("duckdb", "polars", "datafusion", "sqlite"):
            backend_module.connect()
            return "[green]OK[/green]"

        # Pandas needs a dictionary to connect
        if backend_name == "pandas":
            backend_module.connect({})
            return "[green]OK[/green]"

        # For backends requiring credentials, just verify the module exists
        return "[yellow]Available[/yellow]"

    except ImportError as e:
        # Get the missing package name, with fallback
        missing = e.name if e.name else "dependencies"
        # Escape brackets for Rich markup
        install_hint = f"pip install quicketl\\[{extra}]" if extra else ""
        hint_suffix = f" ({install_hint})" if install_hint else ""
        note_suffix = f" [dim]{note}[/dim]" if note else ""
        return f"[red]Missing: {missing}[/red]{hint_suffix}{note_suffix}"

    except Exception as e:
        # Show specific error type for debugging
        return f"[yellow]{type(e).__name__}: {e!s:.50}[/yellow]"


def _show_pipeline_info(config_file: Path) -> None:
    """Display information about a pipeline configuration."""
    from quicketl.config.loader import load_pipeline_config

    try:
        config = load_pipeline_config(str(config_file))

        panel = Panel(
            f"[bold]{config.name}[/bold]",
            subtitle=config.description or "No description",
            border_style="blue",
        )
        console.print(panel)

        # Source info
        console.print("\n[bold]Source:[/bold]")
        source_dict = config.source.model_dump()
        for key, value in source_dict.items():
            if value:
                console.print(f"  {key}: {value}")

        # Transforms
        console.print(f"\n[bold]Transforms:[/bold] ({len(config.transforms)})")
        for i, t in enumerate(config.transforms):
            t_type = t.model_dump().get("type", t.__class__.__name__)
            console.print(f"  [{i + 1}] {t_type}")

        # Checks
        console.print(f"\n[bold]Checks:[/bold] ({len(config.checks)})")
        for i, c in enumerate(config.checks):
            c_type = c.model_dump().get("type", c.__class__.__name__)
            console.print(f"  [{i + 1}] {c_type}")

        # Sink info
        console.print("\n[bold]Sink:[/bold]")
        sink_dict = config.sink.model_dump()
        for key, value in sink_dict.items():
            if value:
                console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
