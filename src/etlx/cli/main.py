"""ETLX CLI main entry point.

Assembles all subcommands into the main Typer application.
"""

from __future__ import annotations

import typer

from etlx._version import __version__
from etlx.cli.info import app as info_app
from etlx.cli.init import app as init_app
from etlx.cli.run import app as run_app
from etlx.cli.schema import app as schema_app
from etlx.cli.validate import app as validate_app

# Create main app
app = typer.Typer(
    name="etlx",
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
        typer.echo(f"etlx version {__version__}")
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
    compute backends (DuckDB, Polars, DataFusion, Spark, pandas)
    powered by Ibis.

    \b
    Commands:
      run       Execute a pipeline
      validate  Validate configuration
      init      Initialize new project
      info      Show ETLX information
      schema    Output JSON schema for IDE support

    \b
    Examples:
      etlx run pipeline.yml
      etlx validate pipeline.yml
      etlx init my_project
      etlx info --backends
      etlx schema -o .etlx-schema.json
    """
    pass


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
