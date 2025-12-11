"""Airflow integration for ETLX.

Provides a task decorator to run ETLX pipelines in Airflow DAGs.
"""

from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Any, Callable

from etlx.pipeline import Pipeline, PipelineResult


def etlx_task(
    config_path: str | Path | None = None,
    engine: str | None = None,
    fail_on_check_failure: bool = True,
) -> Callable:
    """Decorator to create an Airflow task from an ETLX pipeline.

    Can be used to wrap a pipeline configuration or a function that
    returns pipeline variables.

    Args:
        config_path: Path to pipeline YAML file (if not using builder pattern)
        engine: Override engine from config
        fail_on_check_failure: Whether to fail if quality checks fail

    Returns:
        Decorator function

    Examples:
        Using with YAML configuration:
        ```python
        @etlx_task(config_path="pipelines/daily_etl.yml")
        def run_daily_etl(**context):
            # Return variables to substitute in pipeline
            return {
                "RUN_DATE": context["ds"],
                "ENV": "production",
            }
        ```

        Using builder pattern:
        ```python
        @etlx_task()
        def run_custom_pipeline(**context):
            from etlx.pipeline import Pipeline
            from etlx.config.models import FileSource, FileSink
            from etlx.config.transforms import FilterTransform

            pipeline = (
                Pipeline("custom_pipeline")
                .source(FileSource(path=f"s3://bucket/data/{context['ds']}.parquet"))
                .transform(FilterTransform(predicate="amount > 0"))
                .sink(FileSink(path=f"s3://bucket/output/{context['ds']}/"))
            )
            return pipeline
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            # Call the wrapped function
            result = func(*args, **kwargs)

            # Determine how to run the pipeline
            if isinstance(result, Pipeline):
                # Function returned a Pipeline object
                pipeline = result
                if engine:
                    pipeline.engine_name = engine
                pipeline_result = pipeline.run(
                    fail_on_check_failure=fail_on_check_failure
                )

            elif isinstance(result, dict) and config_path:
                # Function returned variables dict, use config file
                variables = result
                pipeline = Pipeline.from_yaml(config_path, variables=variables)
                if engine:
                    pipeline.engine_name = engine
                pipeline_result = pipeline.run(
                    fail_on_check_failure=fail_on_check_failure
                )

            elif config_path:
                # No variables returned, just run config
                pipeline = Pipeline.from_yaml(config_path)
                if engine:
                    pipeline.engine_name = engine
                pipeline_result = pipeline.run(
                    fail_on_check_failure=fail_on_check_failure
                )

            else:
                raise ValueError(
                    "etlx_task requires either a config_path or the decorated "
                    "function must return a Pipeline object"
                )

            # Check for failure
            if pipeline_result.failed:
                raise RuntimeError(
                    f"Pipeline '{pipeline_result.pipeline_name}' failed: "
                    f"{pipeline_result.error}"
                )

            # Return result dict for XCom
            return pipeline_result.to_dict()

        return wrapper

    return decorator


def run_pipeline_task(
    config_path: str | Path,
    variables: dict[str, str] | None = None,
    engine: str | None = None,
    fail_on_check_failure: bool = True,
) -> dict[str, Any]:
    """Run an ETLX pipeline as an Airflow task.

    This is a simpler alternative to the decorator pattern.

    Args:
        config_path: Path to pipeline YAML file
        variables: Variable substitutions
        engine: Override engine from config
        fail_on_check_failure: Whether to fail if quality checks fail

    Returns:
        Pipeline result as dict (for XCom)

    Raises:
        RuntimeError: If pipeline fails

    Examples:
        Using with PythonOperator:
        ```python
        from airflow.operators.python import PythonOperator
        from etlx.integrations.airflow import run_pipeline_task

        task = PythonOperator(
            task_id="run_etl",
            python_callable=run_pipeline_task,
            op_kwargs={
                "config_path": "pipelines/daily_etl.yml",
                "variables": {"DATE": "{{ ds }}"},
            },
        )
        ```
    """
    pipeline = Pipeline.from_yaml(config_path, variables=variables)

    if engine:
        pipeline.engine_name = engine

    result = pipeline.run(fail_on_check_failure=fail_on_check_failure)

    if result.failed:
        raise RuntimeError(
            f"Pipeline '{result.pipeline_name}' failed: {result.error}"
        )

    return result.to_dict()
