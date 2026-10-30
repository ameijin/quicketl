"""Tests for running pipelines from a folder other than the project folder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quicketl.cli.main import app

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

PIPELINE = (
    "name: p\n"
    "source:\n  type: file\n  path: data/in.csv\n  format: csv\n"
    "sink:\n  type: file\n  path: out/result.parquet\n"
)


def _make_project(root: Path, *, project_file: bool) -> Path:
    """Create pipelines/p.yml reading data/in.csv, relative to `root`."""
    (root / "pipelines").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "out").mkdir()  # the file sink does not create missing folders
    (root / "data" / "in.csv").write_text("id,amount\n1,10\n2,20\n")
    if project_file:
        (root / "quicketl.yml").write_text('version: "1.0"\n')
    pipeline = root / "pipelines" / "p.yml"
    pipeline.write_text(PIPELINE)
    return pipeline


class TestRunFromAnotherFolder:
    """`quicketl run` works from any folder when the project root is known."""

    def test_project_file_marks_the_root(self, cli_runner: CliRunner, temp_dir: Path):
        """Paths resolve against the folder holding quicketl.yml."""
        pipeline = _make_project(temp_dir, project_file=True)

        result = cli_runner.invoke(app, ["run", str(pipeline)])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "out" / "result.parquet").exists()

    def test_base_dir_option(self, cli_runner: CliRunner, temp_dir: Path):
        """--base-dir sets the root when there is no quicketl.yml."""
        pipeline = _make_project(temp_dir, project_file=False)

        result = cli_runner.invoke(app, ["run", str(pipeline), "--base-dir", str(temp_dir)])

        assert result.exit_code == 0, result.output
        assert (temp_dir / "out" / "result.parquet").exists()


class TestWorkflowFromAnotherFolder:
    """`quicketl workflow run` passes --base-dir to every pipeline."""

    def test_base_dir_option(self, cli_runner: CliRunner, temp_dir: Path):
        """Pipelines in the workflow resolve their paths against --base-dir."""
        _make_project(temp_dir, project_file=False)
        workflow = temp_dir / "workflow.yml"
        workflow.write_text(
            "name: wf\nstages:\n  - name: s1\n    pipelines:\n      - path: pipelines/p.yml\n"
        )

        result = cli_runner.invoke(
            app, ["workflow", "run", str(workflow), "--base-dir", str(temp_dir)]
        )

        assert result.exit_code == 0, result.output
        assert (temp_dir / "out" / "result.parquet").exists()
