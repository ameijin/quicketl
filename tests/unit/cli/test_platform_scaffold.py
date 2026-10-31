"""Tests for 'quicketl platform scaffold' and 'quicketl platform update'.

These render the real templates: each test copies the repo's copier.yml and
templates/ into a temporary git repo, tags it, and points --template at it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

from quicketl.cli.main import app

if TYPE_CHECKING:
    from typer.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[3]
TAG = "v0.0.1"

SPEC = """
name: acme_data
warehouse:
  type: snowflake
domains:
  - name: sales
    description: Orders and customers
roles:
  - name: analyst
    access: {marts: read}
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def template_repo(temp_dir: Path) -> Path:
    """A git repo holding this checkout's copier.yml and templates/, tagged TAG."""
    repo = temp_dir / "template-repo"
    repo.mkdir()
    shutil.copy(REPO_ROOT / "copier.yml", repo / "copier.yml")
    shutil.copytree(REPO_ROOT / "templates", repo / "templates")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "templates")
    git(repo, "tag", TAG)
    return repo


@pytest.fixture
def project(temp_dir: Path) -> Path:
    folder = temp_dir / "acme"
    folder.mkdir()
    (folder / "platform.yml").write_text(SPEC)
    return folder


def scaffold(cli_runner: CliRunner, *args: str):
    return cli_runner.invoke(app, ["platform", "scaffold", *args])


class TestScaffold:
    def test_generates_project_next_to_spec(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        result = scaffold(
            cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG
        )

        assert result.exit_code == 0, result.output
        readme = (project / "README.md").read_text()
        assert "# acme_data" in readme
        assert "`sales`: Orders and customers" in readme
        assert "`analyst`: read marts" in readme
        answers = yaml.safe_load((project / ".copier-answers.yml").read_text())
        assert answers["_commit"] == TAG
        assert answers["spec"]["name"] == "acme_data"
        assert (project / "platform.yml").read_text() == SPEC

    def test_dest_elsewhere_gets_a_copy_of_the_spec(
        self, cli_runner: CliRunner, template_repo: Path, project: Path, temp_dir: Path
    ):
        dest = temp_dir / "generated"

        result = scaffold(
            cli_runner,
            str(project / "platform.yml"),
            "-d",
            str(dest),
            "-t",
            str(template_repo),
            "-r",
            TAG,
        )

        assert result.exit_code == 0, result.output
        assert (dest / "README.md").exists()
        assert (dest / "platform.yml").read_text() == SPEC

    def test_second_scaffold_points_to_update(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        args = (str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG)
        scaffold(cli_runner, *args)

        result = scaffold(cli_runner, *args)

        assert result.exit_code == 1
        assert "platform update" in result.output

    def test_warehouse_without_template_is_rejected(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        spec = project / "platform.yml"
        spec.write_text(SPEC.replace("snowflake", "databricks"))

        result = scaffold(cli_runner, str(spec), "-t", str(template_repo), "-r", TAG)

        assert result.exit_code == 1
        assert "No template yet for databricks-airflow" in result.output
        assert not (project / "README.md").exists()

    def test_invalid_spec_is_rejected(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        spec = project / "platform.yml"
        spec.write_text(SPEC.replace("marts: read", "gold: read"))

        result = scaffold(cli_runner, str(spec), "-t", str(template_repo), "-r", TAG)

        assert result.exit_code == 1
        assert "unknown layer 'gold'" in result.output
        assert not (project / "README.md").exists()

    def test_unknown_ref_fails_cleanly(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        result = scaffold(
            cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", "v9.9.9"
        )

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert not (project / "README.md").exists()


class TestUpdate:
    @pytest.fixture
    def generated(self, cli_runner: CliRunner, template_repo: Path, project: Path) -> Path:
        result = scaffold(
            cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG
        )
        assert result.exit_code == 0, result.output
        git(project, "init", "-q")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "scaffold")
        return project

    def test_applies_spec_changes(self, cli_runner: CliRunner, generated: Path):
        spec = generated / "platform.yml"
        spec.write_text(
            SPEC.replace(
                "    description: Orders and customers\n",
                "    description: Orders and customers\n  - name: finance\n",
            )
        )
        git(generated, "commit", "-qam", "add finance")

        result = cli_runner.invoke(app, ["platform", "update", str(generated), "-r", TAG])

        assert result.exit_code == 0, result.output
        assert "`finance`" in (generated / "README.md").read_text()

    def test_applies_template_changes_from_a_newer_tag(
        self, cli_runner: CliRunner, generated: Path, template_repo: Path
    ):
        readme = template_repo / "templates" / "snowflake-airflow" / "README.md.jinja"
        readme.write_text(readme.read_text() + "\nNew template section.\n")
        git(template_repo, "commit", "-qam", "template change")
        git(template_repo, "tag", "v0.0.2")

        result = cli_runner.invoke(app, ["platform", "update", str(generated), "-r", "v0.0.2"])

        assert result.exit_code == 0, result.output
        assert "New template section." in (generated / "README.md").read_text()
        answers = yaml.safe_load((generated / ".copier-answers.yml").read_text())
        assert answers["_commit"] == "v0.0.2"

    def test_dirty_project_is_refused(self, cli_runner: CliRunner, generated: Path):
        (generated / "notes.txt").write_text("uncommitted\n")

        result = cli_runner.invoke(app, ["platform", "update", str(generated), "-r", TAG])

        assert result.exit_code == 1
        assert "dirty" in result.output

    def test_project_not_in_git_is_refused(
        self, cli_runner: CliRunner, template_repo: Path, project: Path
    ):
        scaffold(cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG)

        result = cli_runner.invoke(app, ["platform", "update", str(project), "-r", TAG])

        assert result.exit_code == 1
        assert "git-tracked" in result.output

    def test_folder_not_generated_by_scaffold(self, cli_runner: CliRunner, project: Path):
        result = cli_runner.invoke(app, ["platform", "update", str(project), "-r", TAG])

        assert result.exit_code == 1
        assert "not generated" in result.output


FULL_SPEC = REPO_ROOT / "examples" / "06-platform-spec" / "platform.yml"
MINIMAL_SPEC = REPO_ROOT / "tests" / "fixtures" / "platform" / "minimal.yml"


class TestSnowflakeTerraform:
    """What the snowflake-airflow template writes into terraform/.

    scripts/check_templates.py (the CI `templates` job) runs terraform validate
    on the same output. These tests check which files and values appear.
    """

    def render(self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path, spec: Path):
        project = temp_dir / spec.stem
        project.mkdir()
        shutil.copy(spec, project / "platform.yml")
        result = scaffold(
            cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG
        )
        assert result.exit_code == 0, result.output
        return project / "terraform"

    def test_full_spec_generates_optional_files(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        tf = self.render(cli_runner, template_repo, temp_dir, FULL_SPEC)

        names = {p.name for p in tf.iterdir()}
        assert {"network.tf", "storage.tf", "sso.tf"} <= names
        locals_tf = (tf / "locals.tf").read_text()
        assert 'prefix = "ACME_DATA"' in locals_tf
        assert 'environments = ["DEV", "PROD"]' in locals_tf
        assert "ANALYST = {" in locals_tf
        assert '"203.0.113.0/24", "198.51.100.7"' in (tf / "network.tf").read_text()
        assert "s3://example-landing/finance/invoices/" in (tf / "storage.tf").read_text()
        providers = (tf / "providers.tf").read_text()
        assert "snowflake_network_rule_resource" in providers
        assert "snowflake_storage_integration_aws_resource" in providers

    def test_minimal_spec_skips_optional_files(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        tf = self.render(cli_runner, template_repo, temp_dir, MINIMAL_SPEC)

        gitignore = (tf.parent / ".gitignore").read_text()
        assert "*.tfvars" in gitignore
        assert "*.tfstate" in gitignore
        names = {p.name for p in tf.iterdir()}
        assert not {"network.tf", "storage.tf", "sso.tf"} & names
        assert not any(name.endswith(".jinja") for name in names)
        assert "preview_features_enabled" not in (tf / "providers.tf").read_text()
        variables = (tf / "variables.tf").read_text()
        assert "storage_aws_role_arn" not in variables
        assert "okta" not in variables

    def test_role_domains_default_to_every_domain(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        tf = self.render(cli_runner, template_repo, temp_dir, FULL_SPEC)

        locals_tf = (tf / "locals.tf").read_text()
        loader = locals_tf.split("LOADER = {")[1].split("TRANSFORMER")[0]
        analyst = locals_tf.split("ANALYST = {")[1]
        assert 'domains = ["SALES", "FINANCE"]' in loader
        assert 'domains = ["SALES"]' in analyst
