"""OpenLineage integration for QuickETL.

Provides data lineage tracking for pipeline execution.
Requires: quicketl[openlineage]
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from openlineage.client import OpenLineageClient
from openlineage.client.event_v2 import Dataset, Job, Run, RunEvent, RunState
from openlineage.client.facet_v2 import (
    column_lineage_dataset,
    schema_dataset,
)


class LineageContext:
    """OpenLineage context for pipeline lineage tracking.

    Manages job events and dataset lineage.

    Attributes:
        namespace: Namespace for the job.
        job_name: Name of the job/pipeline.
    """

    def __init__(
        self,
        namespace: str = "quicketl",
        job_name: str = "pipeline",
        client: OpenLineageClient | None = None,
    ) -> None:
        """Initialize lineage context.

        Args:
            namespace: Namespace for the job.
            job_name: Name of the job/pipeline.
            client: Optional custom OpenLineage client.
        """
        self.namespace = namespace
        self.job_name = job_name
        self._client = client or OpenLineageClient()
        self._run_id = str(uuid4())
        self._inputs: list[Dataset] = []
        self._outputs: list[Dataset] = []

    def _create_job(self) -> Job:
        """Create the job object."""
        return Job(namespace=self.namespace, name=self.job_name)

    def _create_run(self) -> Run:
        """Create the run object."""
        return Run(runId=self._run_id)

    def add_input_dataset(
        self,
        namespace: str,
        name: str,
        schema: dict[str, str] | None = None,
    ) -> None:
        """Add an input dataset to track.

        Args:
            namespace: Dataset namespace (e.g., 's3://bucket').
            name: Dataset name (e.g., 'table_name').
            schema: Optional column schema {col_name: type}.
        """
        facets = {}
        if schema:
            fields = [
                schema_dataset.SchemaDatasetFacetFields(name=col, type=dtype)
                for col, dtype in schema.items()
            ]
            facets["schema"] = schema_dataset.SchemaDatasetFacet(fields=fields)

        dataset = Dataset(namespace=namespace, name=name, facets=facets)
        self._inputs.append(dataset)

    def add_output_dataset(
        self,
        namespace: str,
        name: str,
        schema: dict[str, str] | None = None,
        column_lineage: dict[str, list[str]] | None = None,
    ) -> None:
        """Add an output dataset to track.

        Args:
            namespace: Dataset namespace.
            name: Dataset name.
            schema: Optional column schema.
            column_lineage: Optional column lineage {output_col: [input_cols]}.
        """
        facets: dict[str, Any] = {}

        if schema:
            fields = [
                schema_dataset.SchemaDatasetFacetFields(name=col, type=dtype)
                for col, dtype in schema.items()
            ]
            facets["schema"] = schema_dataset.SchemaDatasetFacet(fields=fields)

        if column_lineage:
            col_lineage_fields = []
            for output_col, input_cols in column_lineage.items():
                input_fields = [
                    column_lineage_dataset.InputField(
                        namespace=self.namespace,
                        name=self.job_name,
                        field=col,
                    )
                    for col in input_cols
                ]
                col_lineage_fields.append(
                    column_lineage_dataset.ColumnLineageDatasetFacetFieldsAdditional(
                        inputFields=input_fields,
                        transformationType="",
                        transformationDescription="",
                    )
                )
            # Note: Actual column lineage facet requires more setup

        dataset = Dataset(namespace=namespace, name=name, facets=facets)
        self._outputs.append(dataset)

    def emit_start(self) -> None:
        """Emit job start event."""
        event = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=self._create_run(),
            job=self._create_job(),
            inputs=self._inputs,
            outputs=self._outputs,
        )
        self._client.emit(event)

    def emit_complete(self) -> None:
        """Emit job complete event."""
        event = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=self._create_run(),
            job=self._create_job(),
            inputs=self._inputs,
            outputs=self._outputs,
        )
        self._client.emit(event)

    def emit_fail(self, error_message: str | None = None) -> None:
        """Emit job fail event.

        Args:
            error_message: Optional error message.
        """
        event = RunEvent(
            eventType=RunState.FAIL,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=self._create_run(),
            job=self._create_job(),
            inputs=self._inputs,
            outputs=self._outputs,
        )
        self._client.emit(event)
