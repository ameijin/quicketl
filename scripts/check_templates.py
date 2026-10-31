"""Render each platform template and check the Terraform and dbt it generates.

For each spec below, this script:

1. copies copier.yml and templates/ into a temporary tagged git repo;
2. runs `quicketl platform scaffold` against it;
3. runs `terraform fmt -check`, `terraform init -backend=false` and
   `terraform validate` in the generated terraform/ folder;
4. checks that every `snowflake_<type>.<name>[...].<attribute>` reference
   names an attribute the provider schema has. `terraform validate` does not
   check references through for_each keys, so this step covers that gap;
5. runs `dbt parse` and `dbt ls` in the generated dbt/ folder, and checks that
   every generated model lands in a domain schema (never PUBLIC, which the
   Terraform grants nothing on);
6. installs Airflow 3.3.1 from the generated airflow/requirements.txt (the file
   MWAA installs, with its constraints) into a scratch virtual environment,
   then loads the generated DAGs with Airflow's DagBag and fails on any import
   error or missing DAG.

It needs `git`, `terraform`, `uv` and network access to the Terraform
registry and PyPI. It never connects to Snowflake: dbt and Airflow get
placeholder settings and nothing opens a connection.

Usage:
    uv run python scripts/check_templates.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    REPO_ROOT / "examples" / "06-platform-spec" / "platform.yml",
    REPO_ROOT / "tests" / "fixtures" / "platform" / "minimal.yml",
]
PROVIDER = "registry.terraform.io/snowflakedb/snowflake"
TAG = "v0.0.1"
REFERENCE = re.compile(r"\b(snowflake_[a-z0-9_]+)\.([a-z0-9_]+)(?:\[[^\]]*\])?\.([a-z0-9_]+)")
DBT = ["uvx", "--from", "dbt-core==1.12.6", "--with", "dbt-snowflake==1.12.4", "dbt"]
DBT_ENV = {
    "SNOWFLAKE_ACCOUNT": "placeholder",
    "SNOWFLAKE_USER": "placeholder",
    "SNOWFLAKE_PRIVATE_KEY": "placeholder",
    "DBT_SNOWFLAKE_ROLE": "placeholder",
    "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
}


def run(cmd: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd.name})", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def make_template_repo(work: Path) -> Path:
    repo = work / "template-repo"
    repo.mkdir()
    shutil.copy(REPO_ROOT / "copier.yml", repo / "copier.yml")
    shutil.copytree(REPO_ROOT / "templates", repo / "templates")
    git = ["git", "-c", "user.email=check@example.com", "-c", "user.name=check"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "templates"], ["tag", TAG]):
        subprocess.run([*git, *args], cwd=repo, check=True, capture_output=True)
    return repo


def check_references(tf_dir: Path) -> list[str]:
    """Return references to attributes the provider schema does not have."""
    schema_json = subprocess.run(
        ["terraform", "providers", "schema", "-json"],
        cwd=tf_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    resources = json.loads(schema_json)["provider_schemas"][PROVIDER]["resource_schemas"]
    problems = []
    for tf_file in sorted(tf_dir.glob("*.tf")):
        for resource_type, _name, attribute in REFERENCE.findall(tf_file.read_text()):
            attributes = resources.get(resource_type, {}).get("block", {}).get("attributes", {})
            if attribute not in attributes:
                problems.append(f"{tf_file.name}: {resource_type} has no attribute {attribute!r}")
    return problems


def check_dbt(dbt_dir: Path) -> list[str]:
    """Parse the dbt project and return models that would land outside a domain schema."""
    env = {**os.environ, **DBT_ENV}
    common = ["--profiles-dir", ".", "--no-version-check"]
    print(f"$ dbt parse  (in {dbt_dir.name})", flush=True)
    subprocess.run([*DBT, "parse", *common], cwd=dbt_dir, env=env, check=True)
    listed = subprocess.run(
        [
            *DBT,
            "ls",
            *common,
            "--resource-types",
            "model",
            "--output",
            "json",
            "--output-keys",
            "unique_id",
            "schema",
            "--quiet",
        ],
        cwd=dbt_dir,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    problems = []
    for line in filter(None, listed.splitlines()):
        node = json.loads(line)
        if node["schema"].upper() == "PUBLIC":
            problems.append(f"dbt: {node['unique_id']} would build in PUBLIC, not a domain schema")
    return problems


AIRFLOW_VERSION = "3.3.1"
LOAD_DAGS = """
import sys
from airflow.dag_processing.dagbag import DagBag

bag = DagBag(dag_folder=sys.argv[1], safe_mode=False)
for path, error in bag.import_errors.items():
    print(f"IMPORT ERROR in {path}:\\n{error}")
print("DAGS:", ",".join(sorted(bag.dags)))
"""


def make_airflow_venv(work: Path, requirements: Path) -> Path:
    """Create a virtual environment with Airflow and the template's requirements."""
    venv = work / "airflow-venv"
    run(["uv", "venv", "-q", str(venv), "--python", "3.12"], cwd=work)
    python = venv / "bin" / "python"
    run(
        [
            "uv",
            "pip",
            "install",
            "-q",
            "--python",
            str(python),
            f"apache-airflow=={AIRFLOW_VERSION}",
            "-r",
            str(requirements),
        ],
        cwd=work,
    )
    return python


def check_airflow(dags_dir: Path, python: Path, work: Path) -> list[str]:
    """Load the generated DAGs with DagBag and return import problems."""
    home = work / "airflow-home"
    home.mkdir(exist_ok=True)
    env = {**os.environ, "AIRFLOW_HOME": str(home), "AIRFLOW__CORE__LOAD_EXAMPLES": "False"}
    print(f"$ DagBag({dags_dir.name})", flush=True)
    output = subprocess.run(
        [str(python), "-I", "-c", LOAD_DAGS, str(dags_dir)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    problems = [line for line in output.splitlines() if line.startswith("IMPORT ERROR")]
    dag_ids = next(line for line in output.splitlines() if line.startswith("DAGS:"))[5:].strip()
    if not dag_ids:
        problems.append(f"airflow: no DAG loaded from {dags_dir}")
    else:
        print(f"  loaded: {dag_ids}")
    if problems:
        print(output)
    return problems


def scaffold_spec(spec: Path, repo: Path, work: Path) -> Path:
    project = work / spec.stem
    project.mkdir()
    shutil.copy(spec, project / "platform.yml")
    quicketl = shutil.which("quicketl") or "quicketl"
    run([quicketl, "platform", "scaffold", "-t", str(repo), "-r", TAG], cwd=project)
    return project


def check_project(project: Path, airflow_python: Path, work: Path) -> list[str]:
    tf_dir = project / "terraform"
    run(["terraform", "fmt", "-check", "-diff"], cwd=tf_dir)
    run(["terraform", "init", "-backend=false", "-input=false", "-no-color"], cwd=tf_dir)
    run(["terraform", "validate", "-no-color"], cwd=tf_dir)
    return (
        check_references(tf_dir)
        + check_dbt(project / "dbt")
        + check_airflow(project / "airflow" / "dags", airflow_python, work)
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        repo = make_template_repo(work)
        projects = [scaffold_spec(spec, repo, work) for spec in SPECS]
        airflow_python = make_airflow_venv(work, projects[0] / "airflow" / "requirements.txt")
        problems = []
        for project in projects:
            problems += check_project(project, airflow_python, work)
    for problem in problems:
        print(f"ERROR: {problem}")
    print("Templates OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
