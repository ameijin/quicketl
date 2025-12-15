"""Workflow execution.

Provides the Workflow class for running multiple pipelines with
dependency management and staged execution.
"""

from __future__ import annotations

import concurrent.futures
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from quicketl.config.loader import substitute_variables
from quicketl.config.workflow import PipelineRef, WorkflowConfig, WorkflowStage
from quicketl.logging import get_logger
from quicketl.pipeline import Pipeline, PipelineResult
from quicketl.pipeline.result import StageResult, WorkflowResult, WorkflowStatus

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class Workflow:
    """Workflow orchestration for multiple pipelines.

    Executes pipelines in stages with dependency management.
    Supports parallel execution within stages.

    Examples:
        # From YAML configuration
        >>> workflow = Workflow.from_yaml("workflows/medallion.yml")
        >>> result = workflow.run()

        # Programmatic creation
        >>> workflow = Workflow("my_workflow")
        >>> workflow.add_stage("bronze", ["pipeline1.yml", "pipeline2.yml"])
        >>> workflow.add_stage("silver", ["pipeline3.yml"], depends_on=["bronze"])
        >>> result = workflow.run()
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        variables: dict[str, str] | None = None,
        fail_fast: bool = True,
    ) -> None:
        """Initialize a new workflow.

        Args:
            name: Workflow name
            description: Optional description
            variables: Global variables for all pipelines
            fail_fast: Stop on first failure
        """
        self.name = name
        self.description = description
        self.variables = variables or {}
        self.fail_fast = fail_fast
        self._stages: list[WorkflowStage] = []
        self._base_path: Path = Path(".")

    @classmethod
    def from_config(cls, config: WorkflowConfig, base_path: Path | None = None) -> Workflow:
        """Create a workflow from a WorkflowConfig.

        Args:
            config: Validated workflow configuration
            base_path: Base path for resolving relative pipeline paths

        Returns:
            Workflow instance
        """
        workflow = cls(
            name=config.name,
            description=config.description,
            variables=config.variables,
            fail_fast=config.fail_fast,
        )
        workflow._stages = config.stages
        if base_path:
            workflow._base_path = base_path
        return workflow

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        variables: dict[str, str] | None = None,
    ) -> Workflow:
        """Load a workflow from a YAML file.

        Args:
            path: Path to workflow YAML file
            variables: Optional variable overrides

        Returns:
            Workflow instance
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Substitute variables
        config_dict = substitute_variables(raw_config, variables)

        # Validate config
        config = WorkflowConfig.model_validate(config_dict)

        # Merge variables
        merged_vars = {**config.variables}
        if variables:
            merged_vars.update(variables)
        config.variables = merged_vars

        # Create workflow with base path for resolving relative paths
        workflow = cls.from_config(config, base_path=path.parent)
        return workflow

    # =========================================================================
    # Builder Methods
    # =========================================================================

    def add_stage(
        self,
        name: str,
        pipelines: list[str | PipelineRef],
        depends_on: list[str] | None = None,
        parallel: bool = False,
        description: str = "",
    ) -> Workflow:
        """Add a stage to the workflow.

        Args:
            name: Stage name
            pipelines: List of pipeline paths or PipelineRef objects
            depends_on: Names of stages that must complete first
            parallel: Whether to run pipelines in parallel
            description: Optional stage description

        Returns:
            self for chaining
        """
        refs = []
        for p in pipelines:
            if isinstance(p, str):
                refs.append(PipelineRef(path=p))
            else:
                refs.append(p)

        stage = WorkflowStage(
            name=name,
            description=description,
            pipelines=refs,
            parallel=parallel,
            depends_on=depends_on or [],
        )
        self._stages.append(stage)
        return self

    def with_variables(self, variables: dict[str, str]) -> Workflow:
        """Set or update runtime variables.

        Args:
            variables: Key-value variable pairs

        Returns:
            self for chaining
        """
        self.variables.update(variables)
        return self

    # =========================================================================
    # Execution
    # =========================================================================

    def run(
        self,
        variables: dict[str, str] | None = None,
        dry_run: bool = False,
        max_workers: int | None = None,
    ) -> WorkflowResult:
        """Execute the workflow.

        Args:
            variables: Runtime variable overrides
            dry_run: If True, execute transforms but skip sink writes
            max_workers: Maximum parallel workers (default: CPU count)

        Returns:
            WorkflowResult with execution details
        """
        if variables:
            self.variables.update(variables)

        start_time = datetime.now(UTC)
        stage_results: list[StageResult] = []
        total_pipelines = sum(len(s.pipelines) for s in self._stages)
        pipelines_succeeded = 0
        pipelines_failed = 0
        error: str | None = None

        logger.info(
            "workflow_start",
            name=self.name,
            stages=len(self._stages),
            pipelines=total_pipelines,
        )

        # Get execution order
        config = WorkflowConfig(
            name=self.name,
            description=self.description,
            variables=self.variables,
            stages=self._stages,
            fail_fast=self.fail_fast,
        )
        execution_order = config.get_execution_order()

        # Execute stages in order
        try:
            for stage_group in execution_order:
                for stage_name in stage_group:
                    stage = next(s for s in self._stages if s.name == stage_name)

                    stage_result = self._run_stage(
                        stage,
                        dry_run=dry_run,
                        max_workers=max_workers,
                    )
                    stage_results.append(stage_result)

                    pipelines_succeeded += stage_result.pipelines_succeeded
                    pipelines_failed += stage_result.pipelines_failed

                    # Check for failure
                    if not stage_result.succeeded:
                        if self.fail_fast and not stage.continue_on_failure:
                            error = f"Stage '{stage_name}' failed"
                            raise StopIteration

        except StopIteration:
            pass
        except Exception as e:
            error = str(e)
            logger.error("workflow_error", name=self.name, error=error)

        end_time = datetime.now(UTC)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Determine status
        if error or pipelines_failed > 0:
            if pipelines_succeeded > 0:
                status = WorkflowStatus.PARTIAL
            else:
                status = WorkflowStatus.FAILED
        else:
            status = WorkflowStatus.SUCCESS

        logger.info(
            "workflow_complete",
            name=self.name,
            status=status.value,
            pipelines_succeeded=pipelines_succeeded,
            pipelines_failed=pipelines_failed,
            duration_ms=duration_ms,
        )

        return WorkflowResult(
            workflow_name=self.name,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            stage_results=stage_results,
            total_pipelines=total_pipelines,
            pipelines_succeeded=pipelines_succeeded,
            pipelines_failed=pipelines_failed,
            error=error,
            metadata={"dry_run": dry_run},
        )

    def _run_stage(
        self,
        stage: WorkflowStage,
        dry_run: bool = False,
        max_workers: int | None = None,
    ) -> StageResult:
        """Execute a single stage."""
        start_time = datetime.now(UTC)
        pipeline_results: list[PipelineResult] = []
        error: str | None = None

        logger.info(
            "stage_start",
            workflow=self.name,
            stage=stage.name,
            pipelines=len(stage.pipelines),
            parallel=stage.parallel,
        )

        try:
            if stage.parallel and len(stage.pipelines) > 1:
                # Parallel execution
                pipeline_results = self._run_pipelines_parallel(
                    stage.pipelines,
                    dry_run=dry_run,
                    max_workers=max_workers,
                    continue_on_failure=stage.continue_on_failure,
                )
            else:
                # Sequential execution
                pipeline_results = self._run_pipelines_sequential(
                    stage.pipelines,
                    dry_run=dry_run,
                    continue_on_failure=stage.continue_on_failure,
                )

        except Exception as e:
            error = str(e)
            logger.error("stage_error", stage=stage.name, error=error)

        end_time = datetime.now(UTC)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Determine status
        all_succeeded = all(r.succeeded for r in pipeline_results)
        if error or not all_succeeded:
            status = "failed"
        else:
            status = "success"

        logger.info(
            "stage_complete",
            workflow=self.name,
            stage=stage.name,
            status=status,
            duration_ms=duration_ms,
        )

        return StageResult(
            stage_name=stage.name,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            pipeline_results=pipeline_results,
            error=error,
        )

    def _run_pipelines_sequential(
        self,
        pipeline_refs: list[PipelineRef],
        dry_run: bool = False,
        continue_on_failure: bool = False,
    ) -> list[PipelineResult]:
        """Run pipelines sequentially."""
        results: list[PipelineResult] = []

        for ref in pipeline_refs:
            result = self._run_single_pipeline(ref, dry_run=dry_run)
            results.append(result)

            if result.failed and not continue_on_failure:
                break

        return results

    def _run_pipelines_parallel(
        self,
        pipeline_refs: list[PipelineRef],
        dry_run: bool = False,
        max_workers: int | None = None,
        continue_on_failure: bool = False,
    ) -> list[PipelineResult]:
        """Run pipelines in parallel."""
        results: list[PipelineResult] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._run_single_pipeline, ref, dry_run): ref
                for ref in pipeline_refs
            }

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

                if result.failed and not continue_on_failure and self.fail_fast:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break

        return results

    def _run_single_pipeline(
        self,
        ref: PipelineRef,
        dry_run: bool = False,
    ) -> PipelineResult:
        """Run a single pipeline."""
        # Resolve path relative to workflow file
        pipeline_path = self._base_path / ref.path

        # Merge variables
        merged_vars = {**self.variables, **ref.variables}

        logger.info(
            "pipeline_start",
            workflow=self.name,
            pipeline=ref.resolved_name,
            path=str(pipeline_path),
        )

        try:
            pipeline = Pipeline.from_yaml(pipeline_path, variables=merged_vars)
            result = pipeline.run(dry_run=dry_run)
        except Exception as e:
            # Create a failed result
            from quicketl.pipeline.result import PipelineResultBuilder

            builder = PipelineResultBuilder(pipeline_name=ref.resolved_name)
            builder.set_error(str(e))
            result = builder.build()

        return result

    # =========================================================================
    # Inspection
    # =========================================================================

    def info(self) -> dict[str, Any]:
        """Get workflow information.

        Returns:
            Dictionary with workflow details
        """
        return {
            "name": self.name,
            "description": self.description,
            "variables": self.variables,
            "stages": [
                {
                    "name": s.name,
                    "pipelines": [p.path for p in s.pipelines],
                    "parallel": s.parallel,
                    "depends_on": s.depends_on,
                }
                for s in self._stages
            ],
        }

    def __repr__(self) -> str:
        total_pipelines = sum(len(s.pipelines) for s in self._stages)
        return (
            f"Workflow(name={self.name!r}, stages={len(self._stages)}, "
            f"pipelines={total_pipelines})"
        )


def run_workflow(
    path: str | Path,
    variables: dict[str, str] | None = None,
    dry_run: bool = False,
    max_workers: int | None = None,
) -> WorkflowResult:
    """Convenience function to run a workflow from YAML.

    Args:
        path: Path to workflow YAML file
        variables: Runtime variable overrides
        dry_run: If True, execute transforms but skip sink writes
        max_workers: Maximum parallel workers

    Returns:
        WorkflowResult

    Examples:
        >>> result = run_workflow("workflows/medallion.yml")
        >>> result = run_workflow(
        ...     "workflows/medallion.yml",
        ...     variables={"RUN_DATE": "2025-01-01"}
        ... )
    """
    workflow = Workflow.from_yaml(path, variables=variables)
    return workflow.run(dry_run=dry_run, max_workers=max_workers)
