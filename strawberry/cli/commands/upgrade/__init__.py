import glob

import rich
import typer
from libcst.codemod import CodemodContext

from strawberry.cli.app import app
from strawberry.codemods.annotated_unions import ConvertUnionToAnnotatedUnion

from ._run_codemod import run_codemod

codemods = {
    "annotated-union": ConvertUnionToAnnotatedUnion,
}


# TODO: add support for running all of them
# TODO: add support for passing a list of files
@app.command(help="Upgrades a Strawberry project to the latest version")
def upgrade(
    codemod: str = typer.Argument(
        ...,
        autocompletion=lambda: list(codemods.keys()),
        help="Name of the upgrade to run",
    ),
) -> None:
    if codemod not in codemods:
        rich.print(f'[red]Upgrade named "{codemod}" does not exist')

        raise typer.Exit(2)

    transformer = ConvertUnionToAnnotatedUnion(CodemodContext())

    files = list(set(glob.glob("**/*.py", recursive=True)))

    results = list(run_codemod(transformer, files))
    changed = [result for result in results if result.changed]

    rich.print()
    rich.print("[green]Upgrade completed successfully, here's a summary:")
    rich.print(f"  - {len(changed)} files changed")
    rich.print(f"  - {len(results) - len(changed)} files skipped")

    if changed:
        raise typer.Exit(1)
