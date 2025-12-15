"""Pipeline execution results.

Provides structured results from pipeline execution including
step-by-step timings and quality check outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some steps succeeded


@dataclass
class StepResult:
    """Result of a single pipeline step."""

    step_name: str
    step_type: str
    status: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "success"


@dataclass
class PipelineResult:
    """Complete result of a pipeline execution.

    Attributes:
        pipeline_name: Name of the executed pipeline
        status: Overall status (success, failed, partial)
        start_time: When execution started
        end_time: When execution completed
        duration_ms: Total duration in milliseconds
        rows_processed: Number of rows in final output
        rows_written: Number of rows written to sink
        step_results: Results from each step
        check_results: Quality check outcomes
        error: Error message if failed
        metadata: Additional execution metadata
    """

    pipeline_name: str
    status: PipelineStatus
    start_time: datetime
    end_time: datetime
    duration_ms: float
    rows_processed: int = 0
    rows_written: int = 0
    step_results: list[StepResult] = field(default_factory=list)
    check_results: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Whether the pipeline completed successfully."""
        return self.status == PipelineStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Whether the pipeline failed."""
        return self.status == PipelineStatus.FAILED

    @property
    def steps_succeeded(self) -> int:
        """Count of steps that succeeded."""
        return sum(1 for s in self.step_results if s.succeeded)

    @property
    def steps_failed(self) -> int:
        """Count of steps that failed."""
        return sum(1 for s in self.step_results if not s.succeeded)

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Pipeline: {self.pipeline_name}",
            f"Status: {self.status.value.upper()}",
            f"Duration: {self.duration_ms:.1f}ms",
            f"Steps: {self.steps_succeeded}/{len(self.step_results)} succeeded",
        ]

        if self.rows_processed > 0:
            lines.append(f"Rows processed: {self.rows_processed:,}")
        if self.rows_written > 0:
            lines.append(f"Rows written: {self.rows_written:,}")
        if self.error:
            lines.append(f"Error: {self.error}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pipeline_name": self.pipeline_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "rows_processed": self.rows_processed,
            "rows_written": self.rows_written,
            "steps_succeeded": self.steps_succeeded,
            "steps_failed": self.steps_failed,
            "step_results": [
                {
                    "step_name": s.step_name,
                    "step_type": s.step_type,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "details": s.details,
                    "error": s.error,
                }
                for s in self.step_results
            ],
            "check_results": self.check_results,
            "error": self.error,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        return self.summary()


# =============================================================================
# Workflow Results
# =============================================================================


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some stages/pipelines succeeded


@dataclass
class StageResult:
    """Result of a workflow stage execution."""

    stage_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    pipeline_results: list[PipelineResult] = field(default_factory=list)
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "success"

    @property
    def pipelines_succeeded(self) -> int:
        return sum(1 for p in self.pipeline_results if p.succeeded)

    @property
    def pipelines_failed(self) -> int:
        return sum(1 for p in self.pipeline_results if p.failed)


@dataclass
class WorkflowResult:
    """Complete result of a workflow execution.

    Attributes:
        workflow_name: Name of the executed workflow
        status: Overall status (success, failed, partial)
        start_time: When execution started
        end_time: When execution completed
        duration_ms: Total duration in milliseconds
        stage_results: Results from each stage
        total_pipelines: Total number of pipelines
        pipelines_succeeded: Number of successful pipelines
        pipelines_failed: Number of failed pipelines
        error: Error message if failed
    """

    workflow_name: str
    status: WorkflowStatus
    start_time: datetime
    end_time: datetime
    duration_ms: float
    stage_results: list[StageResult] = field(default_factory=list)
    total_pipelines: int = 0
    pipelines_succeeded: int = 0
    pipelines_failed: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Whether the workflow completed successfully."""
        return self.status == WorkflowStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Whether the workflow failed."""
        return self.status == WorkflowStatus.FAILED

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Workflow: {self.workflow_name}",
            f"Status: {self.status.value.upper()}",
            f"Duration: {self.duration_ms:.1f}ms",
            f"Stages: {len(self.stage_results)}",
            f"Pipelines: {self.pipelines_succeeded}/{self.total_pipelines} succeeded",
        ]

        if self.error:
            lines.append(f"Error: {self.error}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "total_pipelines": self.total_pipelines,
            "pipelines_succeeded": self.pipelines_succeeded,
            "pipelines_failed": self.pipelines_failed,
            "stage_results": [
                {
                    "stage_name": s.stage_name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "pipelines_succeeded": s.pipelines_succeeded,
                    "pipelines_failed": s.pipelines_failed,
                    "pipeline_results": [p.to_dict() for p in s.pipeline_results],
                    "error": s.error,
                }
                for s in self.stage_results
            ],
            "error": self.error,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        return self.summary()


@dataclass
class PipelineResultBuilder:
    """Builder for constructing PipelineResult incrementally."""

    pipeline_name: str
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    step_results: list[StepResult] = field(default_factory=list)
    check_results: dict[str, Any] | None = None
    rows_processed: int = 0
    rows_written: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, result: StepResult) -> None:
        """Add a step result."""
        self.step_results.append(result)

    def set_error(self, error: str) -> None:
        """Set error message."""
        self.error = error

    def set_check_results(self, results: dict[str, Any]) -> None:
        """Set quality check results."""
        self.check_results = results

    def build(self) -> PipelineResult:
        """Build the final PipelineResult."""
        end_time = datetime.now(UTC)
        duration_ms = (end_time - self.start_time).total_seconds() * 1000

        # Determine status
        if self.error:
            status = PipelineStatus.FAILED
        elif any(not s.succeeded for s in self.step_results):
            status = PipelineStatus.PARTIAL
        else:
            status = PipelineStatus.SUCCESS

        return PipelineResult(
            pipeline_name=self.pipeline_name,
            status=status,
            start_time=self.start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            rows_processed=self.rows_processed,
            rows_written=self.rows_written,
            step_results=self.step_results,
            check_results=self.check_results,
            error=self.error,
            metadata=self.metadata,
        )
