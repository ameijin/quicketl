"""Workflow configuration models for QuickETL.

Workflows orchestrate multiple pipelines with dependency management,
parallel execution, and staged execution.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PipelineRef(BaseModel):
    """Reference to a pipeline within a workflow stage.

    Example YAML:
        pipelines:
          - path: pipelines/bronze/ingest_users.yml
          - path: pipelines/bronze/ingest_events.yml
            name: events  # Optional custom name
    """

    path: str = Field(..., description="Path to pipeline YAML file")
    name: str | None = Field(
        default=None,
        description="Optional name override (defaults to filename)",
    )
    variables: dict[str, str] = Field(
        default_factory=dict,
        description="Pipeline-specific variable overrides",
    )

    @property
    def resolved_name(self) -> str:
        """Get the pipeline name (custom or derived from path)."""
        if self.name:
            return self.name
        # Extract filename without extension
        return self.path.rsplit("/", 1)[-1].rsplit(".", 1)[0]


class WorkflowStage(BaseModel):
    """A stage in a workflow containing one or more pipelines.

    Stages execute sequentially, but pipelines within a stage can
    run in parallel.

    Example YAML:
        stages:
          - name: bronze
            parallel: true
            pipelines:
              - path: pipelines/bronze/ingest_users.yml
              - path: pipelines/bronze/ingest_events.yml
          - name: silver
            depends_on: [bronze]
            pipelines:
              - path: pipelines/silver/clean_users.yml
    """

    name: str = Field(..., description="Stage name (used for dependencies)")
    description: str = Field(default="", description="Stage description")
    pipelines: list[PipelineRef] = Field(
        ...,
        description="Pipelines to execute in this stage",
        min_length=1,
    )
    parallel: bool = Field(
        default=False,
        description="Whether to run pipelines in parallel",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Stage names that must complete before this stage",
    )
    continue_on_failure: bool = Field(
        default=False,
        description="Whether to continue if a pipeline fails",
    )


class WorkflowConfig(BaseModel):
    """Complete workflow configuration.

    A workflow defines a sequence of stages, each containing pipelines
    to execute. Stages run sequentially based on dependencies, while
    pipelines within a stage can run in parallel.

    Example YAML:
        name: medallion_etl
        description: Bronze -> Silver -> Gold data pipeline

        variables:
          RUN_DATE: "2025-01-01"

        stages:
          - name: bronze
            parallel: true
            pipelines:
              - path: pipelines/bronze/ingest_users.yml
              - path: pipelines/bronze/ingest_events.yml
              - path: pipelines/bronze/ingest_payments.yml

          - name: silver
            depends_on: [bronze]
            parallel: true
            pipelines:
              - path: pipelines/silver/clean_users.yml
              - path: pipelines/silver/clean_events.yml
              - path: pipelines/silver/clean_payments.yml

          - name: silver_agg
            depends_on: [silver]
            pipelines:
              - path: pipelines/silver/agg_revenue.yml
    """

    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    variables: dict[str, str] = Field(
        default_factory=dict,
        description="Global variables for all pipelines",
    )
    stages: list[WorkflowStage] = Field(
        ...,
        description="Workflow stages in execution order",
        min_length=1,
    )
    fail_fast: bool = Field(
        default=True,
        description="Stop workflow on first failure",
    )

    model_config = {
        "extra": "forbid",
    }

    @field_validator("stages")
    @classmethod
    def validate_dependencies(cls, stages: list[WorkflowStage]) -> list[WorkflowStage]:
        """Validate that all stage dependencies exist."""
        stage_names = {s.name for s in stages}
        for stage in stages:
            for dep in stage.depends_on:
                if dep not in stage_names:
                    raise ValueError(
                        f"Stage '{stage.name}' depends on unknown stage '{dep}'"
                    )
        return stages

    def get_execution_order(self) -> list[list[str]]:
        """Get stages in execution order (topological sort).

        Returns:
            List of stage name groups. Stages in the same group
            have their dependencies satisfied and could theoretically
            run in parallel.
        """
        # Build dependency graph
        remaining = {s.name: set(s.depends_on) for s in self.stages}
        order: list[list[str]] = []

        while remaining:
            # Find stages with no remaining dependencies
            ready = [name for name, deps in remaining.items() if not deps]
            if not ready:
                # Circular dependency
                raise ValueError(
                    f"Circular dependency detected among stages: {list(remaining.keys())}"
                )

            order.append(ready)

            # Remove completed stages from dependency lists
            for name in ready:
                del remaining[name]
            for deps in remaining.values():
                deps -= set(ready)

        return order
