from __future__ import annotations

from pathlib import Path  # noqa: TCH003

import typer

from strawberry.cli.app import app
from strawberry.schema_codegen import codegen


@app.command(help="Generate code from a query")
def schema_codegen(
    schema: Path = typer.Argument(exists=True),
    output_dir: Path
    | None = typer.Option(
        None,
        "-o",
        "--output-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    output = codegen(schema.read_text())

    if output_dir is None:
        typer.echo(output)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "schema.py"
    output_file.write_text(output)
