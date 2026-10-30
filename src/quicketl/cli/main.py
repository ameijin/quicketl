"""QuickETL CLI main entry point.

Assembles all subcommands into the main Typer application.
"""

from __future__ import annotations

import typer

from quicketl._version import __version__
from quicketl.cli.info import app as info_app
from quicketl.cli.init import init
from quicketl.cli.run import run
from quicketl.cli.schema import app as schema_app
from quicketl.cli.validate import validate
from quicketl.cli.workflow import app as workflow_app

# Create main app
app = typer.Typer(
    name="quicketl",
    help="QuickETL - Python ETL/ELT Framework",
    no_args_is_help=True,
    add_completion=True,
)

# Register subcommands
# Single-command modules are registered as commands (not sub-Typers) so that
# options may follow the positional argument.
app.command("run", short_help="Run a QuickETL pipeline")(run)
app.command("validate", short_help="Validate pipeline configuration")(validate)
app.add_typer(workflow_app, name="workflow")
app.command("init", short_help="Initialize a new QuickETL project or pipeline")(init)
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
    """QuickETL - Python ETL/ELT Framework.

    A configuration-driven ETL framework with support for multiple
    compute backends (DuckDB, Polars, DataFusion, Spark, pandas).

    \b
    Quick Start:
      quicketl init                       # Initialize in current directory
      quicketl run pipelines/sample.yml   # Run a single pipeline
      quicketl workflow run workflow.yml  # Run a multi-pipeline workflow

    \b
    Commands:
      run       Execute a single pipeline from YAML config
      validate  Validate pipeline configuration without running
      workflow  Run and manage multi-pipeline workflows
      init      Create new project or pipeline
      info      Show version and available backends
      schema    Output JSON schema for IDE autocompletion

    \b
    Examples:
      quicketl run pipeline.yml --var DATE=2025-01-01
      quicketl run pipeline.yml --dry-run
      quicketl workflow run workflows/etl.yml
      quicketl workflow run workflows/etl.yml --workers 4
      quicketl validate pipeline.yml --verbose
      quicketl init my_project
      quicketl info --backends --check
    """
    pass


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
