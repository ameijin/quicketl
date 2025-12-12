"""ETLX CLI main entry point.

Assembles all subcommands into the main Typer application.
"""

from __future__ import annotations

import typer

from quicketl._version import __version__
from quicketl.cli.info import app as info_app
from quicketl.cli.init import app as init_app
from quicketl.cli.run import app as run_app
from quicketl.cli.schema import app as schema_app
from quicketl.cli.validate import app as validate_app

# Create main app
app = typer.Typer(
    name="quicketl",
    help="ETLX - Python ETL/ELT Framework",
    no_args_is_help=True,
    add_completion=True,
)

# Register subcommands
app.add_typer(run_app, name="run")
app.add_typer(validate_app, name="validate")
app.add_typer(init_app, name="init")
app.add_typer(info_app, name="info")
app.add_typer(schema_app, name="schema")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"quicketl version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """ETLX - Python ETL/ELT Framework.

    A configuration-driven ETL framework with support for multiple
    compute backends (DuckDB, Polars, DataFusion, Spark, pandas).

    \b
    Quick Start:
      quicketl init my_project        # Create project with sample data
      cd my_project
      quicketl run pipelines/sample.yml   # Run the sample pipeline

    \b
    Commands:
      run       Execute a pipeline from YAML config
      validate  Validate configuration without running
      init      Create new project or pipeline
      info      Show version and available backends
      schema    Output JSON schema for IDE autocompletion

    \b
    Examples:
      quicketl run pipeline.yml --var DATE=2025-01-01
      quicketl run pipeline.yml --dry-run
      quicketl validate pipeline.yml --verbose
      quicketl init my_project
      quicketl init my_pipeline -p
      quicketl info --backends --check
    """
    pass


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
