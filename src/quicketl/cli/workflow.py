"""CLI command: quicketl workflow

Execute and manage QuickETL workflows.
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - required at runtime for Typer
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from quicketl.logging import configure_logging
from quicketl.pipeline.result import WorkflowStatus
from quicketl.workflow import Workflow

console = Console()
app = typer.Typer(help="Run and manage workflows")


def parse_variables(var_strings: list[str]) -> dict[str, str]:
    """Parse KEY=VALUE variable strings."""
    variables = {}
    for var in var_strings:
        if "=" not in var:
            raise typer.BadParameter(f"Invalid variable format: {var}. Use KEY=VALUE")
        key, value = var.split("=", 1)
        variables[key] = value
    return variables


@app.command("run")
def run(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to workflow YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
    var: Annotated[
        list[str] | None,
        typer.Option(
            "--var",
            "-v",
            help="Set variable (KEY=VALUE), can be repeated",
        ),
    ] = None,
    env: Annotated[
        str | None,
        typer.Option(
            "--env",
            help="Environment name from quicketl.yml (dev, staging, prod)",
        ),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            "-p",
            help="Connection profile name from quicketl.yml",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Execute transforms but skip writing to sinks",
        ),
    ] = False,
    parallel_workers: Annotated[
        int | None,
        typer.Option(
            "--workers",
            "-w",
            help="Maximum parallel workers for parallel stages",
        ),
    ] = None,
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
    """Execute a QuickETL workflow.

    Workflows orchestrate multiple pipelines with dependency management
    and optional parallel execution.

    Examples:
        quicketl workflow run workflows/medallion.yml
        quicketl workflow run workflows/etl.yml --var DATE=2025-01-01
        quicketl workflow run workflows/etl.yml --env prod
        quicketl workflow run workflows/etl.yml --dry-run
        quicketl workflow run workflows/etl.yml --workers 4
    """
    configure_logging(level="DEBUG" if verbose else "INFO")
    variables = parse_variables(var or [])

    # Load project config for --env and --profile
    _resolve_project_config(env, profile, variables)

    try:
        workflow = Workflow.from_yaml(config_file, variables=variables)

        if not json_output:
            console.print(f"\nRunning workflow: [bold]{workflow.name}[/bold]")
            if workflow.description:
                console.print(f"  {workflow.description}")
            console.print(f"  Stages: {len(workflow._stages)}")
            total = sum(len(s.pipelines) for s in workflow._stages)
            console.print(f"  Pipelines: {total}")
            console.print()

        result = workflow.run(
            dry_run=dry_run,
            max_workers=parallel_workers,
        )

        if json_output:
            import json

            console.print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            _display_result(result)

        # Exit with appropriate code
        if result.status == WorkflowStatus.FAILED:
            raise typer.Exit(1)
        elif result.status == WorkflowStatus.PARTIAL:
            raise typer.Exit(2)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from None


@app.command("validate")
def validate(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to workflow YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Show detailed validation output",
        ),
    ] = False,
) -> None:
    """Validate a workflow configuration without running it.

    Checks:
      - YAML syntax is valid
      - All required fields are present
      - Stage dependencies are valid (no cycles, no missing deps)
      - All referenced pipeline files exist

    Examples:
        quicketl workflow validate workflows/medallion.yml
        quicketl workflow validate workflows/etl.yml --verbose
    """
    try:
        workflow = Workflow.from_yaml(config_file)

        # Check that all pipeline files exist
        missing: list[str] = []
        for stage in workflow._stages:
            for pipeline_ref in stage.pipelines:
                pipeline_path = workflow._base_path / pipeline_ref.path
                if not pipeline_path.exists():
                    missing.append(pipeline_ref.path)

        if missing:
            console.print(
                Panel(
                    "[bold red]INVALID[/bold red]\n\n"
                    "Missing pipeline files:\n" + "\n".join(f"  - {m}" for m in missing),
                    title="Validation Failed",
                )
            )
            raise typer.Exit(1)

        # Show structure if verbose
        if verbose:
            tree = Tree(f"[bold]{workflow.name}[/bold]")
            for stage in workflow._stages:
                deps = f" (depends: {', '.join(stage.depends_on)})" if stage.depends_on else ""
                parallel = " [parallel]" if stage.parallel else ""
                branch = tree.add(f"[cyan]{stage.name}[/cyan]{deps}{parallel}")
                for p in stage.pipelines:
                    branch.add(f"[dim]{p.path}[/dim]")
            console.print(tree)
            console.print()

        console.print(
            Panel(
                "[bold green]VALID[/bold green]",
                title="Validation Passed",
            )
        )

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(
            Panel(
                f"[bold red]INVALID[/bold red]\n\n{e}",
                title="Validation Failed",
            )
        )
        raise typer.Exit(1) from None


@app.command("info")
def info(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to workflow YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
) -> None:
    """Show workflow structure and information.

    Examples:
        quicketl workflow info workflows/medallion.yml
    """
    try:
        workflow = Workflow.from_yaml(config_file)

        console.print(f"\n[bold]Workflow: {workflow.name}[/bold]")
        if workflow.description:
            console.print(f"  {workflow.description}")
        console.print()

        # Show execution order
        from quicketl.config.workflow import WorkflowConfig

        config = WorkflowConfig(
            name=workflow.name,
            description=workflow.description,
            variables=workflow.variables,
            stages=workflow._stages,
            fail_fast=workflow.fail_fast,
        )
        execution_order = config.get_execution_order()

        console.print("[bold]Execution Order:[/bold]")
        for i, stage_group in enumerate(execution_order, 1):
            console.print(f"  {i}. {', '.join(stage_group)}")
        console.print()

        # Show stages table
        table = Table(title="Stages")
        table.add_column("Stage", style="cyan")
        table.add_column("Pipelines", justify="right")
        table.add_column("Parallel")
        table.add_column("Depends On")

        for stage in workflow._stages:
            table.add_row(
                stage.name,
                str(len(stage.pipelines)),
                "Yes" if stage.parallel else "No",
                ", ".join(stage.depends_on) or "-",
            )

        console.print(table)

        # Show variables if any
        if workflow.variables:
            console.print("\n[bold]Variables:[/bold]")
            for key, value in workflow.variables.items():
                console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from None


@app.command("generate")
def generate(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to workflow YAML configuration file",
            exists=True,
            readable=True,
        ),
    ],
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Target orchestrator (airflow, prefect)",
        ),
    ] = "airflow",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (prints to stdout if not specified)",
        ),
    ] = None,
    dag_id: Annotated[
        str | None,
        typer.Option(
            "--dag-id",
            help="DAG/flow ID (defaults to workflow name)",
        ),
    ] = None,
    schedule: Annotated[
        str | None,
        typer.Option(
            "--schedule",
            "-s",
            help="Cron schedule (Airflow only)",
        ),
    ] = None,
) -> None:
    """Generate orchestration code from a workflow.

    Generates Airflow DAGs or Prefect flows from workflow YAML files.
    This allows you to develop and test locally, then deploy to
    production orchestrators.

    Examples:
        quicketl workflow generate workflows/etl.yml --target airflow
        quicketl workflow generate workflows/etl.yml --target airflow -o dags/etl_dag.py
        quicketl workflow generate workflows/etl.yml --target prefect
        quicketl workflow generate workflows/etl.yml -t airflow --schedule "0 0 * * *"
    """
    from quicketl.config.loader import load_workflow_config
    from quicketl.workflow.generators import generate_airflow_dag, generate_prefect_flow

    try:
        config = load_workflow_config(config_file)

        # Determine base path relative to workflow file
        base_path = str(config_file.parent)

        if target.lower() == "airflow":
            code = generate_airflow_dag(
                config,
                dag_id=dag_id,
                schedule=schedule,
                base_path=base_path,
            )
        elif target.lower() == "prefect":
            code = generate_prefect_flow(
                config,
                flow_name=dag_id,
                base_path=base_path,
            )
        else:
            console.print(f"[red]Error:[/red] Unknown target: {target}")
            console.print("Supported targets: airflow, prefect")
            raise typer.Exit(1)

        if output:
            output.write_text(code)
            console.print(f"[green]Generated {target} code:[/green] {output}")
        else:
            console.print(code)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from None


def _display_result(result) -> None:
    """Display workflow result in a formatted way."""
    # Status panel
    if result.status == WorkflowStatus.SUCCESS:
        status_style = "green"
        status_text = "SUCCESS"
    elif result.status == WorkflowStatus.PARTIAL:
        status_style = "yellow"
        status_text = "PARTIAL"
    else:
        status_style = "red"
        status_text = "FAILED"

    panel = Panel(
        f"[bold {status_style}]{status_text}[/bold {status_style}]",
        title=f"Workflow: {result.workflow_name}",
        subtitle=f"Duration: {result.duration_ms:.1f}ms",
    )
    console.print(panel)

    # Stages table
    if result.stage_results:
        table = Table(title="Stages")
        table.add_column("Stage", style="cyan")
        table.add_column("Status")
        table.add_column("Pipelines", justify="right")
        table.add_column("Duration", justify="right")

        for stage in result.stage_results:
            status_str = "[green]OK[/green]" if stage.succeeded else "[red]FAIL[/red]"

            pipelines_str = f"{stage.pipelines_succeeded}/{len(stage.pipeline_results)}"
            table.add_row(
                stage.stage_name,
                status_str,
                pipelines_str,
                f"{stage.duration_ms:.1f}ms",
            )

        console.print(table)

    # Summary
    console.print(
        f"\nPipelines: {result.pipelines_succeeded}/{result.total_pipelines} succeeded"
    )

    if result.error:
        console.print(f"\n[red]Error:[/red] {result.error}")


def _resolve_project_config(
    env: str | None,
    profile: str | None,
    variables: dict[str, str],
) -> None:
    """Load project config and resolve --env/--profile flags.

    Mutates `variables` dict to inject profile fields.
    """
    if env is None and profile is None:
        return

    from quicketl.config.project import find_project_config, load_project_config

    project_path = find_project_config()
    if project_path is None:
        console.print(
            "[yellow]Warning:[/yellow] quicketl.yml not found. "
            "--env and --profile require a project config file."
        )
        return

    project = load_project_config(project_path)

    # Resolve environment
    if env is not None:
        from quicketl.config.environments import load_environment

        try:
            load_environment(project.model_dump(), env)
        except KeyError:
            console.print(f"[red]Error:[/red] Environment '{env}' not found in {project_path}")
            raise typer.Exit(1) from None

    # Resolve profile
    if profile is not None:
        from quicketl.config.profiles import load_profiles

        try:
            registry = load_profiles(project.model_dump())
            conn_profile = registry.get(profile)
            variables["PROFILE_TYPE"] = conn_profile.type
            if conn_profile.model_extra:
                for key, value in conn_profile.model_extra.items():
                    variables[f"PROFILE_{key.upper()}"] = str(value)
        except KeyError:
            console.print(f"[red]Error:[/red] Profile '{profile}' not found in {project_path}")
            raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
