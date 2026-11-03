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


def render_project(cli_runner: CliRunner, template_repo: Path, temp_dir: Path, spec: Path) -> Path:
    """Scaffold `spec` from the test template repo and return the project folder."""
    project = temp_dir / spec.stem
    project.mkdir()
    shutil.copy(spec, project / "platform.yml")
    result = scaffold(
        cli_runner, str(project / "platform.yml"), "-t", str(template_repo), "-r", TAG
    )
    assert result.exit_code == 0, result.output
    return project


class TestSnowflakeTerraform:
    """What the snowflake-airflow template writes into terraform/.

    scripts/check_templates.py (the CI `templates` job) runs terraform validate
    on the same output. These tests check which files and values appear.
    """

    def render(self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path, spec: Path):
        return render_project(cli_runner, template_repo, temp_dir, spec) / "terraform"

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

    def test_modules_are_pinned_to_the_template_tag(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        tf = self.render(cli_runner, template_repo, temp_dir, FULL_SPEC)

        sources = [
            line.split('"')[1]
            for path in sorted(tf.glob("*.tf"))
            for line in path.read_text().splitlines()
            if line.strip().startswith("source") and "snowflakedb/snowflake" not in line
        ]
        base = "git::https://github.com/ameijin/quicketl.git//terraform/modules/"
        assert sorted(sources) == sorted(
            f"{base}{name}?ref={TAG}"
            for name in (
                "snowflake-platform",
                "snowflake-network-policy",
                "snowflake-s3-integration",
                "snowflake-okta-sso",
            )
        )
        for source in sources:
            module = source.removeprefix(base).split("?")[0]
            assert (REPO_ROOT / "terraform" / "modules" / module / "main.tf").exists()
        answers = yaml.safe_load((tf.parent / ".copier-answers.yml").read_text())
        assert answers["template_ref"] == TAG

    def test_role_domains_default_to_every_domain(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        tf = self.render(cli_runner, template_repo, temp_dir, FULL_SPEC)

        locals_tf = (tf / "locals.tf").read_text()
        loader = locals_tf.split("LOADER = {")[1].split("TRANSFORMER")[0]
        analyst = locals_tf.split("ANALYST = {")[1]
        assert 'domains = ["SALES", "FINANCE"]' in loader
        assert 'domains = ["SALES"]' in analyst


class TestSnowflakeDbt:
    """What the snowflake-airflow template writes into dbt/.

    scripts/check_templates.py runs dbt parse and dbt ls on the same output.
    """

    def test_full_spec_generates_sources_and_example_model(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        dbt = render_project(cli_runner, template_repo, temp_dir, FULL_SPEC) / "dbt"

        project = yaml.safe_load((dbt / "dbt_project.yml").read_text())
        assert project["name"] == "acme_data"
        assert project["vars"]["platform_prefix"] == "ACME_DATA"
        assert project["vars"]["platform_landing_layer"] == "RAW"
        assert project["vars"]["platform_layers"] == ["STAGING", "MARTS"]
        assert project["vars"]["platform_domains"] == ["SALES", "FINANCE"]

        sources = yaml.safe_load((dbt / "models" / "_sources.yml").read_text())["sources"]
        assert [(s["name"], s["schema"]) for s in sources] == [
            ("sales", "SALES"),
            ("finance", "FINANCE"),
        ]
        assert "{{ target.name | upper }}" in sources[0]["database"]

        model = dbt / "models" / "staging" / "sales" / "stg_sales__orders.sql"
        assert "{{ source('sales', 'orders') }}" in model.read_text()

    def test_profiles_default_to_the_transformer_role(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        dbt = render_project(cli_runner, template_repo, temp_dir, FULL_SPEC) / "dbt"

        profile = yaml.safe_load((dbt / "profiles.yml").read_text())["acme_data"]
        assert profile["target"] == "dev"
        prod = profile["outputs"]["prod"]
        assert prod["role"] == "{{ env_var('DBT_SNOWFLAKE_ROLE', 'ACME_DATA_PROD_TRANSFORMER') }}"
        assert prod["warehouse"] == "ACME_DATA_PROD_WH"
        assert prod["database"] == "ACME_DATA_PROD_STAGING"
        assert prod["private_key"] == "{{ env_var('SNOWFLAKE_PRIVATE_KEY') }}"

    def test_minimal_spec_requires_a_role_and_has_no_models(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        dbt = render_project(cli_runner, template_repo, temp_dir, MINIMAL_SPEC) / "dbt"

        profile = yaml.safe_load((dbt / "profiles.yml").read_text())["minimal"]
        assert profile["outputs"]["dev"]["role"] == "{{ env_var('DBT_SNOWFLAKE_ROLE') }}"
        assert not (dbt / "models" / "_sources.yml").exists()
        assert not list((dbt / "models").rglob("*.sql"))
        assert not list(dbt.rglob("*.jinja"))

    def test_dbt_build_output_is_ignored_by_git(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        project = render_project(cli_runner, template_repo, temp_dir, MINIMAL_SPEC)

        gitignore = (project / ".gitignore").read_text()
        assert "dbt/target/" in gitignore
        assert "dbt/dbt_packages/" in gitignore


class TestSnowflakeAirflow:
    """What the snowflake-airflow template writes into airflow/.

    scripts/check_templates.py loads the same DAGs with Airflow 3.3.1's DagBag.
    """

    def test_full_spec_dag_loads_every_source_then_runs_dbt(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        airflow = render_project(cli_runner, template_repo, temp_dir, FULL_SPEC) / "airflow"

        dag = (airflow / "dags" / "acme_data_platform.py").read_text()
        compile(dag, "acme_data_platform.py", "exec")
        assert 'dag_id="acme_data_platform"' in dag
        assert 'schedule="@daily"' in dag
        assert '"location": "s3://example-landing/finance/invoices/"' in dag
        assert (
            "load_source.partial(environment=ENVIRONMENT).expand(source=SOURCES) >> dbt_build"
            in dag
        )
        assert 'STORAGE_INTEGRATION = f"{PREFIX}_S3_LANDING"' in dag
        assert "{{ var.value.get('platform_environment', 'dev') }}" in dag

    def test_minimal_spec_dag_only_runs_dbt(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        airflow = render_project(cli_runner, template_repo, temp_dir, MINIMAL_SPEC) / "airflow"

        dag = (airflow / "dags" / "minimal_platform.py").read_text()
        compile(dag, "minimal_platform.py", "exec")
        assert "SnowflakeHook" not in dag
        assert "load_source" not in dag
        assert "dbt_build = BashOperator(" in dag

    def test_requirements_follow_the_airflow_constraints(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        airflow = render_project(cli_runner, template_repo, temp_dir, MINIMAL_SPEC) / "airflow"

        lines = (airflow / "requirements.txt").read_text().splitlines()
        assert lines[0] == (
            '--constraint "https://raw.githubusercontent.com/apache/airflow/'
            'constraints-3.3.1/constraints-3.12.txt"'
        )
        assert "apache-airflow-providers-snowflake==6.16.0" in lines
        assert "apache-airflow-providers-standard==1.17.0" in lines

    def test_startup_script_installs_dbt_on_workers_only(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        airflow = render_project(cli_runner, template_repo, temp_dir, MINIMAL_SPEC) / "airflow"

        script = (airflow / "startup.sh").read_text()
        assert '"${MWAA_AIRFLOW_COMPONENT}" != "worker"' in script
        assert '"dbt-core==1.12.6" "dbt-snowflake==1.12.4"' in script
        dag = (airflow / "dags" / "minimal_platform.py").read_text()
        assert "/usr/local/airflow/python3-virtualenv/dbt-env/bin/dbt" in dag


class TestSnowflakeCICD:
    """The GitHub Actions workflows the snowflake-airflow template writes.

    scripts/check_templates.py runs actionlint on the same output.
    """

    def workflows(self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path, spec: Path):
        project = render_project(cli_runner, template_repo, temp_dir, spec)
        folder = project / ".github" / "workflows"
        return project, {path.name: yaml.safe_load(path.read_text()) for path in folder.iterdir()}

    def test_generates_ci_and_deploy_workflows(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        project, workflows = self.workflows(cli_runner, template_repo, temp_dir, MINIMAL_SPEC)

        assert set(workflows) == {"ci.yml", "deploy.yml"}
        assert (project / ".github" / "dependabot.yml").exists()
        assert set(workflows["ci.yml"]["jobs"]) == {"terraform", "terraform-plan", "dbt", "airflow"}
        assert set(workflows["deploy.yml"]["jobs"]) == {"plan", "apply", "mwaa"}
        # GitHub expressions survive rendering untouched.
        plan_env = workflows["deploy.yml"]["jobs"]["plan"]["env"]
        assert plan_env["SNOWFLAKE_PRIVATE_KEY"] == "${{ secrets.SNOWFLAKE_PRIVATE_KEY }}"
        assert plan_env["SNOWFLAKE_AUTHENTICATOR"] == "SNOWFLAKE_JWT"

    def test_terraform_uses_s3_state_keyed_by_platform(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        project, workflows = self.workflows(cli_runner, template_repo, temp_dir, FULL_SPEC)

        assert 'backend "s3" {}' in (project / "terraform" / "backend.tf").read_text()
        inits = [
            step["run"]
            for workflow in workflows.values()
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if step.get("name") == "terraform init"
        ]
        assert len(inits) == 3  # CI plan, deploy plan, deploy apply
        for init in inits:
            assert '-backend-config="key=acme_data/terraform.tfstate"' in init
            assert '-backend-config="use_lockfile=true"' in init

    def test_deploy_runs_environments_in_spec_order(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        _, workflows = self.workflows(cli_runner, template_repo, temp_dir, FULL_SPEC)

        mwaa = workflows["deploy.yml"]["jobs"]["mwaa"]
        assert mwaa["strategy"]["matrix"]["environment"] == ["dev", "prod"]
        assert mwaa["strategy"]["max-parallel"] == 1
        assert workflows["deploy.yml"]["jobs"]["apply"]["environment"] == "terraform"

    def test_terraform_variables_follow_the_spec(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        _, full = self.workflows(cli_runner, template_repo, temp_dir, FULL_SPEC)
        _, minimal = self.workflows(cli_runner, template_repo, temp_dir, MINIMAL_SPEC)

        full_env = full["deploy.yml"]["jobs"]["plan"]["env"]
        assert full_env["TF_VAR_storage_aws_role_arn"] == "${{ vars.STORAGE_AWS_ROLE_ARN }}"
        assert full_env["TF_VAR_okta_x509_cert"] == "${{ secrets.OKTA_X509_CERT }}"
        assert full["ci.yml"]["jobs"]["terraform-plan"]["env"] == full_env
        for workflow in minimal.values():
            for job in workflow["jobs"].values():
                assert not [key for key in job.get("env", {}) if key.startswith("TF_VAR_")]

    def test_actions_are_pinned_to_commit_shas(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        _, workflows = self.workflows(cli_runner, template_repo, temp_dir, FULL_SPEC)

        uses = [
            step["uses"]
            for workflow in workflows.values()
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]
        assert uses
        for ref in uses:
            sha = ref.split("@")[1]
            assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha), ref

    def test_ci_checks_dbt_with_the_versions_mwaa_installs(
        self, cli_runner: CliRunner, template_repo: Path, temp_dir: Path
    ):
        project, workflows = self.workflows(cli_runner, template_repo, temp_dir, MINIMAL_SPEC)

        runs = [step.get("run", "") for step in workflows["ci.yml"]["jobs"]["dbt"]["steps"]]
        assert 'pip install "dbt-core==1.12.6" "dbt-snowflake==1.12.4"' in runs
        startup = (project / "airflow" / "startup.sh").read_text()
        assert '"dbt-core==1.12.6" "dbt-snowflake==1.12.4"' in startup
