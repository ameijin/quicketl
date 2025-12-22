"""Tests for workflow execution.

This module tests the Workflow class and workflow orchestration.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from quicketl.config.workflow import PipelineRef, WorkflowConfig, WorkflowStage
from quicketl.pipeline.result import PipelineResult, WorkflowStatus
from quicketl.workflow.workflow import Workflow, run_workflow


class TestWorkflowCreation:
    """Tests for Workflow instantiation and factory methods."""

    def test_workflow_init_sets_attributes(self):
        """Test basic workflow initialization."""
        workflow = Workflow(
            name="test_workflow",
            description="A test workflow",
            variables={"VAR1": "value1"},
            fail_fast=False,
        )

        assert workflow.name == "test_workflow"
        assert workflow.description == "A test workflow"
        assert workflow.variables == {"VAR1": "value1"}
        assert workflow.fail_fast is False

    def test_workflow_init_defaults(self):
        """Test workflow initialization with defaults."""
        workflow = Workflow(name="minimal")

        assert workflow.name == "minimal"
        assert workflow.description == ""
        assert workflow.variables == {}
        assert workflow.fail_fast is True

    def test_workflow_from_config(self):
        """Test creating workflow from WorkflowConfig."""
        config = WorkflowConfig(
            name="config_workflow",
            description="From config",
            variables={"KEY": "val"},
            stages=[
                WorkflowStage(
                    name="stage1",
                    pipelines=[PipelineRef(path="test.yml")],
                )
            ],
            fail_fast=False,
        )

        workflow = Workflow.from_config(config)

        assert workflow.name == "config_workflow"
        assert workflow.description == "From config"
        assert workflow.fail_fast is False
        assert len(workflow._stages) == 1

    def test_workflow_from_config_with_base_path(self, tmp_path):
        """Test that base_path is set from config."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(
                    name="stage1",
                    pipelines=[PipelineRef(path="pipeline.yml")],
                )
            ],
        )

        workflow = Workflow.from_config(config, base_path=tmp_path)

        assert workflow._base_path == tmp_path

    def test_workflow_from_yaml(self, tmp_path):
        """Test loading workflow from YAML file."""
        yaml_content = """
name: yaml_workflow
description: Loaded from YAML

variables:
  ENV: test

stages:
  - name: first
    pipelines:
      - path: pipeline1.yml
"""
        yaml_file = tmp_path / "workflow.yml"
        yaml_file.write_text(yaml_content)

        workflow = Workflow.from_yaml(yaml_file)

        assert workflow.name == "yaml_workflow"
        assert workflow.description == "Loaded from YAML"
        assert workflow.variables == {"ENV": "test"}
        assert len(workflow._stages) == 1
        assert workflow._stages[0].name == "first"

    def test_workflow_from_yaml_with_variable_overrides(self, tmp_path):
        """Test variable override when loading from YAML."""
        yaml_content = """
name: test
variables:
  VAR1: original
  VAR2: keep
stages:
  - name: stage
    pipelines:
      - path: test.yml
"""
        yaml_file = tmp_path / "workflow.yml"
        yaml_file.write_text(yaml_content)

        workflow = Workflow.from_yaml(yaml_file, variables={"VAR1": "overridden"})

        # Override should take precedence
        assert workflow.variables["VAR1"] == "overridden"
        assert workflow.variables["VAR2"] == "keep"

    def test_workflow_from_yaml_file_not_found(self, tmp_path):
        """Test that missing YAML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            Workflow.from_yaml(tmp_path / "nonexistent.yml")

        assert "not found" in str(exc_info.value)


class TestWorkflowBuilderMethods:
    """Tests for workflow builder methods."""

    def test_add_stage_with_string_paths(self):
        """Test adding a stage with string pipeline paths."""
        workflow = Workflow(name="test")
        workflow.add_stage(
            name="bronze",
            pipelines=["pipeline1.yml", "pipeline2.yml"],
            parallel=True,
        )

        assert len(workflow._stages) == 1
        stage = workflow._stages[0]
        assert stage.name == "bronze"
        assert len(stage.pipelines) == 2
        assert stage.parallel is True
        assert stage.pipelines[0].path == "pipeline1.yml"

    def test_add_stage_with_pipeline_refs(self):
        """Test adding a stage with PipelineRef objects."""
        workflow = Workflow(name="test")
        workflow.add_stage(
            name="stage",
            pipelines=[
                PipelineRef(path="p1.yml", name="custom_name"),
                PipelineRef(path="p2.yml", variables={"VAR": "val"}),
            ],
        )

        stage = workflow._stages[0]
        assert stage.pipelines[0].name == "custom_name"
        assert stage.pipelines[1].variables == {"VAR": "val"}

    def test_add_stage_returns_self_for_chaining(self):
        """Test that add_stage returns self for method chaining."""
        workflow = Workflow(name="test")
        result = workflow.add_stage("stage1", ["p1.yml"])

        assert result is workflow

    def test_add_stage_chaining(self):
        """Test chaining multiple add_stage calls."""
        workflow = (
            Workflow(name="test")
            .add_stage("bronze", ["p1.yml"])
            .add_stage("silver", ["p2.yml"], depends_on=["bronze"])
            .add_stage("gold", ["p3.yml"], depends_on=["silver"])
        )

        assert len(workflow._stages) == 3
        assert workflow._stages[2].depends_on == ["silver"]

    def test_with_variables_updates_variables(self):
        """Test that with_variables updates the variables dict."""
        workflow = Workflow(name="test", variables={"KEY1": "val1"})
        workflow.with_variables({"KEY2": "val2"})

        assert workflow.variables == {"KEY1": "val1", "KEY2": "val2"}

    def test_with_variables_returns_self(self):
        """Test that with_variables returns self for chaining."""
        workflow = Workflow(name="test")
        result = workflow.with_variables({"KEY": "val"})

        assert result is workflow


class TestWorkflowInfo:
    """Tests for workflow inspection methods."""

    def test_info_returns_workflow_details(self):
        """Test the info method returns correct structure."""
        workflow = Workflow(name="test_workflow", description="Test description")
        workflow.add_stage("stage1", ["p1.yml", "p2.yml"], parallel=True)
        workflow.add_stage("stage2", ["p3.yml"], depends_on=["stage1"])

        info = workflow.info()

        assert info["name"] == "test_workflow"
        assert info["description"] == "Test description"
        assert len(info["stages"]) == 2
        assert info["stages"][0]["name"] == "stage1"
        assert info["stages"][0]["parallel"] is True
        assert info["stages"][1]["depends_on"] == ["stage1"]

    def test_workflow_repr(self):
        """Test workflow string representation."""
        workflow = Workflow(name="my_workflow")
        workflow.add_stage("s1", ["p1.yml", "p2.yml"])
        workflow.add_stage("s2", ["p3.yml"])

        result = repr(workflow)

        assert "my_workflow" in result
        assert "stages=2" in result
        assert "pipelines=3" in result


class TestWorkflowExecution:
    """Tests for workflow run method."""

    def test_run_with_dry_run(self, tmp_path):
        """Test running workflow with dry_run flag."""
        # Create a minimal pipeline YAML
        pipeline_content = """
name: test_pipeline
engine: duckdb
source:
  type: file
  path: /dev/null
  format: csv
sink:
  type: file
  path: /tmp/output.parquet
  format: parquet
"""
        pipeline_file = tmp_path / "pipeline.yml"
        pipeline_file.write_text(pipeline_content)

        workflow = Workflow(name="test", variables={})
        workflow._base_path = tmp_path
        workflow.add_stage("stage1", [PipelineRef(path="pipeline.yml")])

        # Mock the Pipeline.from_yaml to avoid file I/O
        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = True
            mock_result.failed = False
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            workflow.run(dry_run=True)

            # Verify dry_run was passed
            mock_pipeline.from_yaml.return_value.run.assert_called_with(dry_run=True)

    def test_run_with_runtime_variables(self, tmp_path):
        """Test that runtime variables are merged."""
        workflow = Workflow(name="test", variables={"VAR1": "original"})
        workflow._base_path = tmp_path
        workflow.add_stage("stage1", [PipelineRef(path="pipeline.yml")])

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = True
            mock_result.failed = False
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            workflow.run(variables={"VAR2": "new"})

            # Both variables should be present
            assert workflow.variables["VAR1"] == "original"
            assert workflow.variables["VAR2"] == "new"

    def test_run_returns_workflow_result(self, tmp_path):
        """Test that run returns a WorkflowResult with correct structure."""
        workflow = Workflow(name="result_test")
        workflow._base_path = tmp_path
        workflow.add_stage("stage1", [PipelineRef(path="p1.yml")])

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = True
            mock_result.failed = False
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            result = workflow.run()

            assert result.workflow_name == "result_test"
            assert result.status == WorkflowStatus.SUCCESS
            assert result.total_pipelines == 1
            assert result.pipelines_succeeded == 1
            assert result.pipelines_failed == 0
            assert len(result.stage_results) == 1

    def test_run_fail_fast_stops_on_failure(self, tmp_path):
        """Test that fail_fast stops workflow on first failure."""
        workflow = Workflow(name="test", fail_fast=True)
        workflow._base_path = tmp_path
        workflow.add_stage("stage1", [PipelineRef(path="p1.yml")])
        workflow.add_stage("stage2", [PipelineRef(path="p2.yml")], depends_on=["stage1"])

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            # First pipeline fails
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = False
            mock_result.failed = True
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            result = workflow.run()

            # Should only have run stage1
            assert result.pipelines_failed == 1
            assert len(result.stage_results) == 1
            assert result.status in [WorkflowStatus.FAILED, WorkflowStatus.PARTIAL]


class TestWorkflowConfigValidation:
    """Tests for WorkflowConfig validation."""

    def test_valid_dependencies(self):
        """Test that valid dependencies pass validation."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(name="a", pipelines=[PipelineRef(path="p.yml")]),
                WorkflowStage(
                    name="b",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a"],
                ),
            ],
        )

        assert len(config.stages) == 2

    def test_invalid_dependency_raises_error(self):
        """Test that unknown dependency raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            WorkflowConfig(
                name="test",
                stages=[
                    WorkflowStage(
                        name="a",
                        pipelines=[PipelineRef(path="p.yml")],
                        depends_on=["nonexistent"],
                    ),
                ],
            )

        assert "unknown stage 'nonexistent'" in str(exc_info.value)

    def test_circular_dependency_detected(self):
        """Test that circular dependencies are detected."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(
                    name="a",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["b"],
                ),
                WorkflowStage(
                    name="b",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a"],
                ),
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            config.get_execution_order()

        assert "Circular dependency" in str(exc_info.value)


class TestExecutionOrder:
    """Tests for workflow execution order (topological sort)."""

    def test_simple_linear_order(self):
        """Test simple A -> B -> C order."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(name="a", pipelines=[PipelineRef(path="p.yml")]),
                WorkflowStage(
                    name="b",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a"],
                ),
                WorkflowStage(
                    name="c",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["b"],
                ),
            ],
        )

        order = config.get_execution_order()

        assert order == [["a"], ["b"], ["c"]]

    def test_parallel_stages_same_level(self):
        """Test that stages with no deps between them can run in same group."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(name="a", pipelines=[PipelineRef(path="p.yml")]),
                WorkflowStage(name="b", pipelines=[PipelineRef(path="p.yml")]),
                WorkflowStage(
                    name="c",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a", "b"],
                ),
            ],
        )

        order = config.get_execution_order()

        # a and b should be in the first group (in any order)
        assert set(order[0]) == {"a", "b"}
        assert order[1] == ["c"]

    def test_diamond_dependency(self):
        """Test diamond dependency pattern A -> B,C -> D."""
        config = WorkflowConfig(
            name="test",
            stages=[
                WorkflowStage(name="a", pipelines=[PipelineRef(path="p.yml")]),
                WorkflowStage(
                    name="b",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a"],
                ),
                WorkflowStage(
                    name="c",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["a"],
                ),
                WorkflowStage(
                    name="d",
                    pipelines=[PipelineRef(path="p.yml")],
                    depends_on=["b", "c"],
                ),
            ],
        )

        order = config.get_execution_order()

        assert order[0] == ["a"]
        assert set(order[1]) == {"b", "c"}
        assert order[2] == ["d"]


class TestPipelineRef:
    """Tests for PipelineRef model."""

    def test_resolved_name_uses_custom_name(self):
        """Test that custom name is used when provided."""
        ref = PipelineRef(path="path/to/pipeline.yml", name="custom")

        assert ref.resolved_name == "custom"

    def test_resolved_name_extracts_from_path(self):
        """Test that name is extracted from path when not provided."""
        ref = PipelineRef(path="path/to/my_pipeline.yml")

        assert ref.resolved_name == "my_pipeline"

    def test_resolved_name_handles_simple_path(self):
        """Test resolved_name with simple filename."""
        ref = PipelineRef(path="pipeline.yml")

        assert ref.resolved_name == "pipeline"


class TestContinueOnFailure:
    """Tests for continue_on_failure behavior."""

    def test_sequential_continues_on_failure(self, tmp_path):
        """Test that sequential execution continues when continue_on_failure=True."""
        workflow = Workflow(name="test", fail_fast=True)
        workflow._base_path = tmp_path

        # Add a stage with continue_on_failure
        stage = WorkflowStage(
            name="stage1",
            pipelines=[
                PipelineRef(path="p1.yml"),
                PipelineRef(path="p2.yml"),
            ],
            parallel=False,
            continue_on_failure=True,
        )
        workflow._stages.append(stage)

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            # First fails, second succeeds
            mock_result_fail = MagicMock(spec=PipelineResult)
            mock_result_fail.succeeded = False
            mock_result_fail.failed = True

            mock_result_success = MagicMock(spec=PipelineResult)
            mock_result_success.succeeded = True
            mock_result_success.failed = False

            mock_pipeline.from_yaml.return_value.run.side_effect = [
                mock_result_fail,
                mock_result_success,
            ]

            workflow.run()

            # Both pipelines should have run
            assert mock_pipeline.from_yaml.return_value.run.call_count == 2


class TestRunWorkflowFunction:
    """Tests for the run_workflow convenience function."""

    def test_run_workflow_loads_and_executes(self, tmp_path):
        """Test that run_workflow correctly loads and runs a workflow."""
        yaml_content = """
name: convenience_test
stages:
  - name: stage
    pipelines:
      - path: pipeline.yml
"""
        yaml_file = tmp_path / "workflow.yml"
        yaml_file.write_text(yaml_content)

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = True
            mock_result.failed = False
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            result = run_workflow(yaml_file)

            assert result.workflow_name == "convenience_test"

    def test_run_workflow_passes_parameters(self, tmp_path):
        """Test that run_workflow passes all parameters correctly."""
        yaml_content = """
name: param_test
stages:
  - name: stage
    pipelines:
      - path: pipeline.yml
"""
        yaml_file = tmp_path / "workflow.yml"
        yaml_file.write_text(yaml_content)

        with patch("quicketl.workflow.workflow.Pipeline") as mock_pipeline:
            mock_result = MagicMock(spec=PipelineResult)
            mock_result.succeeded = True
            mock_result.failed = False
            mock_pipeline.from_yaml.return_value.run.return_value = mock_result

            run_workflow(
                yaml_file,
                variables={"VAR": "val"},
                dry_run=True,
                max_workers=4,
            )

            # Verify dry_run was passed
            mock_pipeline.from_yaml.return_value.run.assert_called_with(dry_run=True)
