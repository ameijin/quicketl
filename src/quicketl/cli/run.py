"""CLI command: quicketl run

Execute a QuickETL pipeline from a YAML configuration file.
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - required at runtime for Typer
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from quicketl.logging import configure_logging
from quicketl.pipeline import Pipeline, PipelineStatus

console = Console()
app = typer.Typer(help="Run a QuickETL pipeline")


def parse_variables(var_strings: list[str]) -> dict[str, str]:
    """Parse KEY=VALUE variable strings."""
    variables = {}
    for var in var_strings:
        if "=" not in var:
            raise typer.BadParameter(f"Invalid variable format: {var}. Use KEY=VALUE")
        key, value = var.split("=", 1)
        variables[key] = value
    return variables


@app.callback(invoke_without_command=True)
def run(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to pipeline YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
    engine: Annotated[
        str | None,
        typer.Option(
            "--engine",
            "-e",
            help="Override engine (duckdb, polars, datafusion, spark)",
        ),
    ] = None,
    var: Annotated[
        list[str] | None,
        typer.Option(
            "--var",
            "-v",
            help="Set variable (KEY=VALUE), can be repeated",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Execute transforms but skip writing to sink",
        ),
    ] = False,
    fail_on_checks: Annotated[
        bool,
        typer.Option(
            "--fail-on-checks/--no-fail-on-checks",
            help="Fail pipeline if quality checks fail",
        ),
    ] = True,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Enable verbose logging",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output result as JSON",
        ),
    ] = False,
) -> None:
    """Execute a QuickETL pipeline.

    Examples:
        quicketl run pipeline.yml
        quicketl run pipeline.yml --engine duckdb
        quicketl run pipeline.yml --var DATE=2025-01-01 --var ENV=prod
        quicketl run pipeline.yml --dry-run
    """
    # Configure logging
    configure_logging(level="DEBUG" if verbose else "INFO")

    # Parse variables
    variables = parse_variables(var or [])

    try:
        # Load pipeline
        pipeline = Pipeline.from_yaml(config_file, variables=variables)

        # Override engine if specified
        if engine:
            pipeline.engine_name = engine

        if not json_output:
            console.print(f"\nRunning pipeline: [bold]{pipeline.name}[/bold]")
            if pipeline.description:
                console.print(f"  {pipeline.description}")
            console.print(f"  Engine: {pipeline.engine_name}")
            console.print()

        # Execute pipeline
        result = pipeline.run(
            fail_on_check_failure=fail_on_checks,
            dry_run=dry_run,
        )

        # Output results
        if json_output:
            import json

            console.print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            _display_result(result)

        # Exit with appropriate code
        if result.status == PipelineStatus.FAILED:
            raise typer.Exit(1) from None
        elif result.status == PipelineStatus.PARTIAL:
            raise typer.Exit(2)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from None


def _display_result(result) -> None:
    """Display pipeline result in a formatted way."""
    # Status panel
    if result.status == PipelineStatus.SUCCESS:
        status_style = "green"
        status_text = "SUCCESS"
    elif result.status == PipelineStatus.PARTIAL:
        status_style = "yellow"
        status_text = "PARTIAL"
    else:
        status_style = "red"
        status_text = "FAILED"

    panel = Panel(
        f"[bold {status_style}]{status_text}[/bold {status_style}]",
        title=f"Pipeline: {result.pipeline_name}",
        subtitle=f"Duration: {result.duration_ms:.1f}ms",
    )
    console.print(panel)

    # Steps table
    if result.step_results:
        table = Table(title="Steps")
        table.add_column("Step", style="cyan")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Duration", justify="right")

        for step in result.step_results:
            status_str = "[green]OK[/green]" if step.succeeded else "[red]FAIL[/red]"
            if step.error:
                status_str = f"[red]FAIL: {step.error[:30]}...[/red]" if len(step.error) > 30 else f"[red]FAIL: {step.error}[/red]"
            table.add_row(
                step.step_name,
                step.step_type,
                status_str,
                f"{step.duration_ms:.1f}ms",
            )

        console.print(table)

    # Quality checks
    if result.check_results:
        checks = result.check_results
        check_status = "[green]PASSED[/green]" if checks["all_passed"] else "[red]FAILED[/red]"
        console.print(
            f"\nQuality Checks: {check_status} "
            f"({checks['passed']}/{checks['total']} passed)"
        )

    # Summary
    console.print(f"\nRows processed: {result.rows_processed:,}")
    if result.rows_written > 0:
        console.print(f"Rows written: {result.rows_written:,}")

    if result.error:
        console.print(f"\n[red]Error:[/red] {result.error}")


if __name__ == "__main__":
    app()
