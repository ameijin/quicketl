"""Tests for the CLI on a slim install, without the [pipelines] extra.

Each test runs the CLI in a subprocess that blocks the pipeline data stack
(Ibis, pyarrow, pandas, polars, DuckDB, fsspec), which is what a plain
`pip install quicketl` looks like from 2.0.
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

INSTALL_HINT = "pip install 'quicketl[pipelines]'"

SLIM_CLI = """
import sys

class _BlockPipelineStack:
    BLOCKED = {"ibis", "pyarrow", "pandas", "polars", "duckdb", "fsspec"}

    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in self.BLOCKED:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None

sys.meta_path.insert(0, _BlockPipelineStack())

from quicketl.cli.main import app

sys.argv = ["quicketl", *sys.argv[1:]]
app()
"""

PIPELINE = (
    "name: p\n"
    "source:\n  type: file\n  path: data/in.csv\n  format: csv\n"
    "sink:\n  type: file\n  path: out/result.parquet\n"
)


def run_slim(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run `quicketl ARGS` with the pipeline data stack unavailable."""
    return subprocess.run(
        [sys.executable, "-c", SLIM_CLI, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


@pytest.fixture
def pipeline_file(temp_dir: Path) -> Path:
    path = temp_dir / "pipeline.yml"
    path.write_text(PIPELINE)
    return path


class TestCoreCommandsWorkWithoutPipelines:
    """Commands that only read config or write files work on a slim install."""

    def test_help(self, temp_dir: Path):
        result = run_slim("--help", cwd=temp_dir)

        assert result.returncode == 0, result.stderr
        assert "run" in result.stdout
        assert "validate" in result.stdout

    def test_version(self, temp_dir: Path):
        result = run_slim("--version", cwd=temp_dir)

        assert result.returncode == 0, result.stderr

    def test_info_without_flags(self, temp_dir: Path):
        result = run_slim("info", cwd=temp_dir)

        assert result.returncode == 0, result.stderr

    def test_validate(self, temp_dir: Path, pipeline_file: Path):
        result = run_slim("validate", str(pipeline_file), cwd=temp_dir)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Configuration is valid" in result.stdout

    def test_schema(self, temp_dir: Path):
        result = run_slim("schema", cwd=temp_dir)

        assert result.returncode == 0, result.stderr

    def test_platform_validate(self, temp_dir: Path):
        spec = temp_dir / "platform.yml"
        spec.write_text("name: acme\nwarehouse:\n  type: snowflake\ndomains:\n  - name: sales\n")

        result = run_slim("platform", "validate", str(spec), cwd=temp_dir)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Platform spec is valid" in result.stdout

    def test_platform_init(self, temp_dir: Path):
        result = run_slim("platform", "init", str(temp_dir / "proj"), cwd=temp_dir)

        assert result.returncode == 0, result.stdout + result.stderr
        assert (temp_dir / "proj" / "platform.yml").exists()

    def test_init(self, temp_dir: Path):
        result = run_slim("init", "proj", "-o", str(temp_dir), cwd=temp_dir)

        assert result.returncode == 0, result.stdout + result.stderr
        assert (temp_dir / "proj" / "quicketl.yml").exists()


class TestPipelineCommandsShowInstallHint:
    """Commands that need the data stack exit 1 with a one-line install hint."""

    def test_run(self, temp_dir: Path, pipeline_file: Path):
        result = run_slim("run", str(pipeline_file), cwd=temp_dir)

        assert result.returncode == 1
        assert INSTALL_HINT in result.stdout + result.stderr
        assert "Traceback" not in result.stderr

    def test_workflow_run(self, temp_dir: Path, pipeline_file: Path):
        workflow = temp_dir / "workflow.yml"
        workflow.write_text(
            "name: wf\nstages:\n  - name: s1\n    pipelines:\n      - path: pipeline.yml\n"
        )

        result = run_slim("workflow", "run", str(workflow), cwd=temp_dir)

        assert result.returncode == 1
        assert INSTALL_HINT in result.stdout + result.stderr
        assert "Traceback" not in result.stderr

    def test_info_backends(self, temp_dir: Path):
        result = run_slim("info", "--backends", cwd=temp_dir)

        assert result.returncode == 1
        assert INSTALL_HINT in result.stdout + result.stderr
        assert "Traceback" not in result.stderr


class TestLazyTopLevelExports:
    """`import quicketl` stays light; pipeline classes load on first use."""

    def test_import_does_not_load_ibis(self):
        code = "import sys, quicketl; print('ibis' in sys.modules)"

        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )

        assert result.stdout.strip() == "False"

    def test_pipeline_export_still_works(self):
        import quicketl
        from quicketl.pipeline.pipeline import Pipeline

        assert quicketl.Pipeline is Pipeline

    def test_pipeline_import_without_extra_shows_hint(self):
        """`from quicketl import Pipeline` on a core install names the extra to install."""
        code = SLIM_CLI.split("from quicketl.cli.main import app")[0] + (
            "try:\n    from quicketl import Pipeline\nexcept ImportError as e:\n    print(e)\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )

        assert INSTALL_HINT in result.stdout

    def test_unknown_attribute_raises(self):
        import quicketl

        with pytest.raises(AttributeError):
            _ = quicketl.NotAThing
