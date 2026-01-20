"""Airflow integration for QuickETL.

Provides a task decorator to run QuickETL pipelines in Airflow DAGs.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any

from quicketl.pipeline import Pipeline

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def quicketl_task(
    config_path: str | Path | None = None,
    engine: str | None = None,
    fail_on_check_failure: bool = True,
) -> Callable:
    """Decorator to create an Airflow task from a QuickETL pipeline.

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
        @quicketl_task(config_path="pipelines/daily_etl.yml")
        def run_daily_etl(**context):
            # Return variables to substitute in pipeline
            return {
                "RUN_DATE": context["ds"],
                "ENV": "production",
            }
        ```

        Using builder pattern:
        ```python
        @quicketl_task()
        def run_custom_pipeline(**context):
            from quicketl.pipeline import Pipeline
            from quicketl.config.models import FileSource, FileSink
            from quicketl.config.transforms import FilterTransform

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
            # Use duck typing: check for run method (works with mocks and Pipeline subclasses)
            if hasattr(result, 'run') and callable(getattr(result, 'run', None)) and not isinstance(result, dict):
                # Function returned a Pipeline-like object
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
                    "quicketl_task requires either a config_path or the decorated "
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
        from quicketl.integrations.airflow import run_pipeline_task

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
