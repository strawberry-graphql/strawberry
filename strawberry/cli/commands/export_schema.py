from pathlib import Path

import typer

from strawberry.cli.app import app
from strawberry.cli.utils import load_schema
from strawberry.printer import print_schema


@app.command(help="Exports the schema")
def export_schema(
    schema: str,
    app_dir: str = typer.Option(
        ".",
        "--app-dir",
        show_default=True,
        help=(
            "Look for the module in the specified directory, by adding this to the "
            "PYTHONPATH. Defaults to the current working directory. "
            "Works the same as `--app-dir` in uvicorn."
        ),
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save the exported schema. If not provided, prints to console.",
    ),
    federation_version: float = typer.Option(
        None,
        "--federation-version",
        "-e",
        help=(
            "Override the output federation schema version. please use with care!"
            "schema may break if it have directives that are not supported by the defined federation version."
            "(for directive version compatibility please see: https://www.apollographql.com/docs/graphos/reference/federation/directives)"
        ),
        min=1,
    ),
) -> None:
    if federation_version:
        app.__setattr__("federation_version_override", federation_version)
    schema_symbol = load_schema(schema, app_dir)

    schema_text = print_schema(schema_symbol)

    if output:
        Path(output).write_text(schema_text)
        typer.echo(f"Schema exported to {output}")
    else:
        print(schema_text)  # noqa: T201
