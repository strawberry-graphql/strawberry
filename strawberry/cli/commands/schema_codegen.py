from pathlib import Path
from typing import Optional

import typer

from strawberry.cli.app import app
from strawberry.schema_codegen import codegen


@app.command(help="Generate code from a query")
def schema_codegen(
    schema: Path = typer.Argument(exists=True),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    generated_output = codegen(schema.read_text())

    if output is None:
        typer.echo(generated_output)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated_output)

    typer.echo(f"Code generated at `{output.name}`")
