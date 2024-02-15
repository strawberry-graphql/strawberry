from __future__ import annotations

import glob
import pathlib  # noqa: TCH003
import sys
from enum import Enum
from typing import List
from typing_extensions import assert_never

import rich
import typer
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand

from strawberry.cli.app import app
from strawberry.codemods.annotated_unions import ConvertUnionToAnnotatedUnion
from strawberry.codemods.resolver_type import ConvertFieldWithResolverTypeAnnotations

from ._run_codemod import run_codemod


class Codemod(Enum):
    ANNOTATED_UNION = "annotated-union"
    RESOLVER_TYPE = "resolver-type"


# TODO: add support for running all of them
@app.command(help="Upgrades a Strawberry project to the latest version")
def upgrade(
    codemod: Codemod = typer.Argument(
        ...,
        help="Name of the upgrade to run",
    ),
    paths: List[pathlib.Path] = typer.Argument(..., file_okay=True, dir_okay=True),
    python_target: str = typer.Option(
        ".".join(str(x) for x in sys.version_info[:2]),
        "--python-target",
        help="Python version to target",
    ),
    use_typing_extensions: bool = typer.Option(
        False,
        "--use-typing-extensions",
        help="Use typing_extensions instead of typing for newer features",
    ),
) -> None:
    python_target_version = tuple(int(x) for x in python_target.split("."))

    if codemod == Codemod.ANNOTATED_UNION:
        transformer: VisitorBasedCodemodCommand = ConvertUnionToAnnotatedUnion(
            CodemodContext(),
            use_pipe_syntax=python_target_version >= (3, 10),
            use_typing_extensions=use_typing_extensions,
        )
    elif codemod == Codemod.RESOLVER_TYPE:
        transformer = ConvertFieldWithResolverTypeAnnotations(CodemodContext())
    else:
        return assert_never(codemod)

    files: list[str] = []

    for path in paths:
        if path.is_dir():
            glob_path = str(path / "**/*.py")
            files.extend(glob.glob(glob_path, recursive=True))  # noqa: PTH207
        else:
            files.append(str(path))

    files = list(set(files))

    results = list(run_codemod(transformer, files))
    changed = [result for result in results if result.changed]

    rich.print()
    rich.print("[green]Upgrade completed successfully, here's a summary:")
    rich.print(f"  - {len(changed)} files changed")
    rich.print(f"  - {len(results) - len(changed)} files skipped")

    if changed:
        raise typer.Exit(1)
