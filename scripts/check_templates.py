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
   error or missing DAG;
7. lints the generated GitHub Actions workflows with actionlint.

It needs `git`, `terraform`, `uv`, `actionlint` and network access to the Terraform
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
MODULES_DIR = REPO_ROOT / "terraform" / "modules"
MODULE_SOURCE = re.compile(
    r'source\s*=\s*"git::https://github\.com/ameijin/quicketl\.git//terraform/modules/([a-z0-9-]+)\?ref=[^"]+"'
)
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


def check_references(tf_dir: Path, source_dir: Path | None = None) -> list[str]:
    """Return references to attributes the provider schema does not have.

    `tf_dir` is an initialized Terraform folder to read the schema from;
    `source_dir` (default: `tf_dir`) holds the .tf files to check.
    """
    schema_json = subprocess.run(
        ["terraform", "providers", "schema", "-json"],
        cwd=tf_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    resources = json.loads(schema_json)["provider_schemas"][PROVIDER]["resource_schemas"]
    problems = []
    for tf_file in sorted((source_dir or tf_dir).glob("*.tf")):
        for resource_type, _name, attribute in REFERENCE.findall(tf_file.read_text()):
            attributes = resources.get(resource_type, {}).get("block", {}).get("attributes", {})
            if attribute not in attributes:
                problems.append(f"{tf_file.name}: {resource_type} has no attribute {attribute!r}")
    return problems


def terraform_check(tf_dir: Path) -> None:
    run(["terraform", "init", "-backend=false", "-input=false", "-no-color"], cwd=tf_dir)
    run(["terraform", "validate", "-no-color"], cwd=tf_dir)


def check_modules() -> list[str]:
    """Format-check each module, validate its example, and check its references."""
    problems = []
    for module in sorted(p for p in MODULES_DIR.iterdir() if p.is_dir()):
        run(["terraform", "fmt", "-check", "-diff", "-recursive"], cwd=module)
        example = module / "examples" / "basic"
        if not example.is_dir():
            problems.append(f"{module.name}: no examples/basic")
            continue
        terraform_check(example)
        problems += [f"{module.name}/{p}" for p in check_references(example, module)]
        shutil.rmtree(example / ".terraform", ignore_errors=True)
        (example / ".terraform.lock.hcl").unlink(missing_ok=True)
    return problems


def use_local_modules(tf_dir: Path) -> int:
    """Point git module sources at this checkout; the release tag may not exist yet.

    Returns how many sources were rewritten.
    """
    count = 0
    for tf_file in tf_dir.glob("*.tf"):
        text, n = MODULE_SOURCE.subn(
            lambda m: f'source = "{MODULES_DIR / m.group(1)}"', tf_file.read_text()
        )
        tf_file.write_text(text)
        count += n
    return count


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


def check_workflows(project: Path) -> list[str]:
    """Lint the generated GitHub Actions workflows and return any problems."""
    workflows = sorted((project / ".github" / "workflows").glob("*.yml"))
    if not workflows:
        return [f"{project.name}: no GitHub Actions workflows generated"]
    print(f"$ actionlint  (in {project.name})", flush=True)
    result = subprocess.run(
        ["actionlint", "-no-color", *(str(w) for w in workflows)],
        cwd=project,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, result.stderr)
        return [f"{project.name}: actionlint found problems in .github/workflows"]
    return []


def scaffold_spec(spec: Path, repo: Path, work: Path) -> Path:
    project = work / spec.stem
    project.mkdir()
    shutil.copy(spec, project / "platform.yml")
    quicketl = shutil.which("quicketl") or "quicketl"
    run([quicketl, "platform", "scaffold", "-t", str(repo), "-r", TAG], cwd=project)
    return project


def check_project(project: Path, airflow_python: Path, work: Path) -> list[str]:
    tf_dir = project / "terraform"
    problems = []
    run(["terraform", "fmt", "-check", "-diff"], cwd=tf_dir)
    if use_local_modules(tf_dir) == 0:
        problems.append(f"{project.name}: terraform/ uses no quicketl modules")
    terraform_check(tf_dir)
    # `terraform providers schema` needs an initialized backend, and generated
    # projects declare an S3 one. Read the schema from a folder holding only
    # the project's versions.tf, so the provider constraints are the same.
    schema_dir = work / f"{project.name}-schema"
    schema_dir.mkdir()
    shutil.copy(tf_dir / "versions.tf", schema_dir / "versions.tf")
    run(["terraform", "init", "-input=false", "-no-color"], cwd=schema_dir)
    return (
        problems
        + check_references(schema_dir, tf_dir)
        + check_dbt(project / "dbt")
        + check_airflow(project / "airflow" / "dags", airflow_python, work)
        + check_workflows(project)
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        repo = make_template_repo(work)
        projects = [scaffold_spec(spec, repo, work) for spec in SPECS]
        airflow_python = make_airflow_venv(work, projects[0] / "airflow" / "requirements.txt")
        problems = check_modules()
        for project in projects:
            problems += check_project(project, airflow_python, work)
    for problem in problems:
        print(f"ERROR: {problem}")
    print("Templates OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
