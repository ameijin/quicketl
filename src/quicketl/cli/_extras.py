"""Checks for commands that need an optional extra.

From 2.0 a plain `pip install quicketl` installs only the core: the CLI,
config validation and project setup. Running pipelines needs the
`pipelines` extra, which brings in Ibis and the rest of the data stack.
"""

from __future__ import annotations

import importlib

import typer
from rich.console import Console
from rich.markup import escape

PIPELINES_INSTALL_HINT = (
    "Pipelines need the pipelines extra. Install it with: pip install 'quicketl[pipelines]'"
)


def require_pipelines() -> None:
    """Exit with an install hint when the pipeline data stack is missing.

    Call this at the start of any command that runs pipelines, before
    importing pipeline modules.

    Raises:
        typer.Exit: With code 1 if Ibis cannot be imported.
    """
    try:
        importlib.import_module("ibis")
    except ImportError:
        # Escape the hint so Rich does not read [pipelines] as a style tag,
        # and keep it on one line so the command can be copied.
        Console(stderr=True).print(
            f"[red]Error:[/red] {escape(PIPELINES_INSTALL_HINT)}", soft_wrap=True
        )
        raise typer.Exit(1) from None
