"""Core modules import only the standard library and declared core dependencies.

A plain `pip install quicketl` installs only `[project].dependencies`. If a
core module imports a package that is merely pulled in by one of them today
(for example click, which typer 0.12 to 0.20 depended on and 0.27 does not),
the CLI breaks as soon as that dependency changes.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_PACKAGES = ["cli", "platform"]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def core_distributions() -> set[str]:
    """Distribution names listed in [project].dependencies."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]
    return {
        _normalize(re.match(r"[A-Za-z0-9._-]+", dep).group()) for dep in project["dependencies"]
    }


def module_level_imports(path: Path) -> set[str]:
    """Top-level package names imported unconditionally at module level.

    Imports inside functions, `if TYPE_CHECKING:` blocks and `try:` blocks
    are skipped: those are lazy, type-only or optional.
    """
    names = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


CORE_FILES = sorted(
    path
    for package in CORE_PACKAGES
    for path in (REPO_ROOT / "src" / "quicketl" / package).glob("*.py")
)


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_core_module_imports_only_declared_dependencies(path: Path):
    declared = core_distributions()
    providers = packages_distributions()
    undeclared = []
    for name in sorted(module_level_imports(path)):
        if name == "quicketl" or name == "__future__" or name in sys.stdlib_module_names:
            continue
        dists = {_normalize(d) for d in providers.get(name, [])}
        if not dists & declared:
            undeclared.append(name)

    assert not undeclared, (
        f"{path.name} imports {undeclared} at module level, but no core dependency in "
        "pyproject.toml provides them"
    )
