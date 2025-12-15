"""Workflow orchestration for QuickETL.

Provides the Workflow class for running multiple pipelines with
dependency management and staged execution.
"""

from quicketl.workflow.workflow import Workflow, run_workflow

__all__ = ["Workflow", "run_workflow"]
