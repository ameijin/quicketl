"""Pipeline execution.

Provides the Pipeline class for running ETL pipelines from configuration
or using the builder pattern.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    import ibis.expr.types as ir

    from quicketl.config.checks import CheckConfig
    from quicketl.config.models import PipelineConfig, SinkConfig, SourceConfig
    from quicketl.config.transforms import TransformStep

from quicketl.config.loader import load_pipeline_config
from quicketl.engines import ETLXEngine
from quicketl.logging import get_logger
from quicketl.pipeline.context import ExecutionContext
from quicketl.pipeline.result import (
    PipelineResult,
    PipelineResultBuilder,
    StepResult,
)
from quicketl.quality import CheckSuiteResult, run_checks

logger = get_logger(__name__)


class Pipeline:
    """ETL Pipeline execution.

    Can be created from YAML configuration or built programmatically.

    Examples:
        # From YAML configuration
        >>> pipeline = Pipeline.from_yaml("pipeline.yml")
        >>> result = pipeline.run()

        # Programmatic builder pattern
        >>> pipeline = (
        ...     Pipeline("my_pipeline")
        ...     .source(FileSource(path="data.parquet"))
        ...     .transform(FilterTransform(predicate="amount > 0"))
        ...     .check(NotNullCheck(columns=["id"]))
        ...     .sink(FileSink(path="output.parquet"))
        ... )
        >>> result = pipeline.run()
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        engine: str = "duckdb",
    ) -> None:
        """Initialize a new pipeline.

        Args:
            name: Pipeline name
            description: Optional description
            engine: Backend engine name
        """
        self.name = name
        self.description = description
        self.engine_name = engine
        self._source: SourceConfig | None = None
        self._sources: dict[str, SourceConfig] = {}
        self._transforms: list[TransformStep] = []
        self._checks: list[CheckConfig] = []
        self._sink: SinkConfig | None = None
        self._variables: dict[str, str] = {}

    @classmethod
    def from_config(cls, config: PipelineConfig) -> Pipeline:
        """Create a pipeline from a PipelineConfig.

        Args:
            config: Validated pipeline configuration

        Returns:
            Pipeline instance
        """
        pipeline = cls(
            name=config.name,
            description=config.description,
            engine=config.engine,
        )
        pipeline._source = config.source
        pipeline._sources = config.sources
        pipeline._transforms = config.transforms
        pipeline._checks = config.checks
        pipeline._sink = config.sink
        return pipeline

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        variables: dict[str, str] | None = None,
    ) -> Pipeline:
        """Load a pipeline from a YAML file.

        Args:
            path: Path to YAML file
            variables: Optional variable overrides

        Returns:
            Pipeline instance
        """
        config = load_pipeline_config(str(path), variables=variables)
        pipeline = cls.from_config(config)
        if variables:
            pipeline._variables = variables
        return pipeline

    # =========================================================================
    # Builder Methods
    # =========================================================================

    def source(self, config: SourceConfig) -> Pipeline:
        """Set the data source.

        Args:
            config: Source configuration

        Returns:
            self for chaining
        """
        self._source = config
        return self

    def transform(self, step: TransformStep) -> Pipeline:
        """Add a transform step.

        Args:
            step: Transform configuration

        Returns:
            self for chaining
        """
        self._transforms.append(step)
        return self

    def transforms(self, steps: list[TransformStep]) -> Pipeline:
        """Add multiple transform steps.

        Args:
            steps: List of transform configurations

        Returns:
            self for chaining
        """
        self._transforms.extend(steps)
        return self

    def check(self, config: CheckConfig) -> Pipeline:
        """Add a quality check.

        Args:
            config: Check configuration

        Returns:
            self for chaining
        """
        self._checks.append(config)
        return self

    def checks(self, configs: list[CheckConfig]) -> Pipeline:
        """Add multiple quality checks.

        Args:
            configs: List of check configurations

        Returns:
            self for chaining
        """
        self._checks.extend(configs)
        return self

    def sink(self, config: SinkConfig) -> Pipeline:
        """Set the data sink.

        Args:
            config: Sink configuration

        Returns:
            self for chaining
        """
        self._sink = config
        return self

    def with_variables(self, variables: dict[str, str]) -> Pipeline:
        """Set runtime variables.

        Args:
            variables: Key-value variable pairs

        Returns:
            self for chaining
        """
        self._variables.update(variables)
        return self

    # =========================================================================
    # Execution
    # =========================================================================

    def run(
        self,
        variables: dict[str, str] | None = None,
        fail_on_check_failure: bool = True,
        dry_run: bool = False,
    ) -> PipelineResult:
        """Execute the pipeline.

        Args:
            variables: Runtime variable overrides
            fail_on_check_failure: Whether to fail if quality checks fail
            dry_run: If True, execute transforms but skip sink write

        Returns:
            PipelineResult with execution details
        """
        if variables:
            self._variables.update(variables)

        # Create execution context
        ExecutionContext(variables=self._variables)
        builder = PipelineResultBuilder(
            pipeline_name=self.name,
            metadata={"engine": self.engine_name, "dry_run": dry_run},
        )

        logger.info(
            "pipeline_start",
            name=self.name,
            engine=self.engine_name,
            transforms=len(self._transforms),
            checks=len(self._checks),
        )

        try:
            # Validate configuration - need either source or sources
            has_single_source = self._source is not None
            has_multi_source = bool(self._sources)
            if not has_single_source and not has_multi_source:
                raise ValueError("Pipeline source not configured")
            if self._sink is None and not dry_run:
                raise ValueError("Pipeline sink not configured")

            # Initialize engine
            engine = ETLXEngine(backend=self.engine_name)

            # Load all sources into context
            table_context: dict[str, ir.Table] = {}

            if has_multi_source:
                # Multi-source mode: load all named sources
                primary_name = next(iter(self._sources.keys()))
                for name, source_config in self._sources.items():
                    start = time.perf_counter()
                    logger.debug("reading_source", source_name=name, source_type=source_config.type)
                    table_context[name] = engine.read_source(source_config)
                    duration_ms = (time.perf_counter() - start) * 1000
                    builder.add_step(
                        StepResult(
                            step_name=f"read_source_{name}",
                            step_type=source_config.type,
                            status="success",
                            duration_ms=duration_ms,
                        )
                    )
                # Primary table is the first named source
                table = table_context[primary_name]
            else:
                # Single-source mode (backward compatible)
                table = self._run_read_step(engine, builder)

            # Step 2: Run transforms (with context for join/union)
            table = self._run_transform_steps(engine, table, builder, table_context)

            # Get row count after transforms
            builder.rows_processed = table.count().execute()

            # Step 3: Run quality checks
            if self._checks:
                check_result = self._run_check_step(
                    table, builder, fail_on_check_failure=fail_on_check_failure
                )
                if not check_result.all_passed and fail_on_check_failure:
                    builder.set_error(f"Quality checks failed: {check_result.summary()}")
                    return builder.build()

            # Step 4: Write to sink
            if not dry_run and self._sink:
                write_result = self._run_write_step(engine, table, builder)
                builder.rows_written = write_result.rows_written

            logger.info(
                "pipeline_complete",
                name=self.name,
                rows_processed=builder.rows_processed,
                rows_written=builder.rows_written,
            )

        except Exception as e:
            logger.error("pipeline_error", name=self.name, error=str(e))
            builder.set_error(str(e))

        return builder.build()

    def _run_read_step(
        self,
        engine: ETLXEngine,
        builder: PipelineResultBuilder,
    ) -> ir.Table:
        """Execute the source read step."""
        assert self._source is not None, "Source must be configured"
        start = time.perf_counter()

        logger.debug("reading_source", source_type=self._source.type)
        table = engine.read_source(self._source)

        duration_ms = (time.perf_counter() - start) * 1000
        builder.add_step(
            StepResult(
                step_name="read_source",
                step_type=self._source.type,
                status="success",
                duration_ms=duration_ms,
            )
        )

        return table

    def _run_transform_steps(
        self,
        engine: ETLXEngine,
        table: ir.Table,
        builder: PipelineResultBuilder,
        context: dict[str, ir.Table] | None = None,
    ) -> ir.Table:
        """Execute all transform steps.

        Args:
            engine: ETL engine
            table: Primary input table
            builder: Result builder
            context: Named tables for join/union operations
        """
        for i, transform in enumerate(self._transforms):
            start = time.perf_counter()
            step_name = f"transform_{i}_{transform.op}"

            try:
                logger.debug("applying_transform", step=step_name, type=transform.op)
                table = engine.apply_transform(table, transform, context)

                duration_ms = (time.perf_counter() - start) * 1000
                builder.add_step(
                    StepResult(
                        step_name=step_name,
                        step_type=transform.op,
                        status="success",
                        duration_ms=duration_ms,
                    )
                )

            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                builder.add_step(
                    StepResult(
                        step_name=step_name,
                        step_type=transform.op,
                        status="failed",
                        duration_ms=duration_ms,
                        error=str(e),
                    )
                )
                raise

        return table

    def _run_check_step(
        self,
        table: ir.Table,
        builder: PipelineResultBuilder,
        fail_on_check_failure: bool = True,
    ) -> CheckSuiteResult:
        """Execute quality checks."""
        start = time.perf_counter()

        logger.debug("running_checks", count=len(self._checks))
        result = run_checks(table, self._checks)

        duration_ms = (time.perf_counter() - start) * 1000

        # Determine step status:
        # - If checks pass, step is "success"
        # - If checks fail and fail_on_check_failure=True, step is "failed"
        # - If checks fail and fail_on_check_failure=False, step is "success" (non-blocking)
        if result.all_passed:
            step_status = "success"
        elif fail_on_check_failure:
            step_status = "failed"
        else:
            step_status = "success"  # Check failure is non-blocking

        builder.add_step(
            StepResult(
                step_name="quality_checks",
                step_type="checks",
                status=step_status,
                duration_ms=duration_ms,
                details={
                    "total": result.total_checks,
                    "passed": result.passed_checks,
                    "failed": result.failed_checks,
                },
            )
        )

        builder.set_check_results(
            {
                "all_passed": result.all_passed,
                "total": result.total_checks,
                "passed": result.passed_checks,
                "failed": result.failed_checks,
                "results": [
                    {
                        "type": r.check_type,
                        "passed": r.passed,
                        "message": r.message,
                    }
                    for r in result.results
                ],
            }
        )

        return result

    def _run_write_step(
        self,
        engine: ETLXEngine,
        table: ir.Table,
        builder: PipelineResultBuilder,
    ) -> Any:
        """Execute the sink write step."""
        assert self._sink is not None, "Sink must be configured"
        start = time.perf_counter()

        logger.debug("writing_sink", sink_type=self._sink.type)
        result = engine.write_sink(table, self._sink)

        duration_ms = (time.perf_counter() - start) * 1000
        builder.add_step(
            StepResult(
                step_name="write_sink",
                step_type=self._sink.type,
                status="success",
                duration_ms=duration_ms,
                details={"rows_written": result.rows_written},
            )
        )

        return result

    # =========================================================================
    # Inspection
    # =========================================================================

    def info(self) -> dict[str, Any]:
        """Get pipeline information.

        Returns:
            Dictionary with pipeline details
        """
        return {
            "name": self.name,
            "description": self.description,
            "engine": self.engine_name,
            "source": self._source.model_dump() if self._source else None,
            "transforms": [t.model_dump() for t in self._transforms],
            "checks": [c.model_dump() for c in self._checks],
            "sink": self._sink.model_dump() if self._sink else None,
        }

    def __repr__(self) -> str:
        return (
            f"Pipeline(name={self.name!r}, engine={self.engine_name!r}, "
            f"transforms={len(self._transforms)}, checks={len(self._checks)})"
        )


def run_pipeline(
    path: str | Path,
    variables: dict[str, str] | None = None,
    engine: str | None = None,
    fail_on_check_failure: bool = True,
    dry_run: bool = False,
) -> PipelineResult:
    """Convenience function to run a pipeline from YAML.

    Args:
        path: Path to pipeline YAML file
        variables: Runtime variable overrides
        engine: Override engine from config
        fail_on_check_failure: Whether to fail if quality checks fail
        dry_run: If True, execute transforms but skip sink write

    Returns:
        PipelineResult

    Examples:
        >>> result = run_pipeline("pipeline.yml")
        >>> result = run_pipeline("pipeline.yml", variables={"DATE": "2025-01-01"})
    """
    pipeline = Pipeline.from_yaml(path, variables=variables)

    if engine:
        pipeline.engine_name = engine

    return pipeline.run(
        fail_on_check_failure=fail_on_check_failure,
        dry_run=dry_run,
    )
