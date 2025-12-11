"""ETLX Pipeline execution.

Provides the Pipeline class and utilities for running ETL pipelines.
"""

from etlx.pipeline.context import ExecutionContext
from etlx.pipeline.pipeline import Pipeline, run_pipeline
from etlx.pipeline.result import (
    PipelineResult,
    PipelineResultBuilder,
    PipelineStatus,
    StepResult,
)

__all__ = [
    # Core classes
    "Pipeline",
    "ExecutionContext",
    # Results
    "PipelineResult",
    "PipelineResultBuilder",
    "PipelineStatus",
    "StepResult",
    # Convenience functions
    "run_pipeline",
]
