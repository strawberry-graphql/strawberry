import sys

import typer
from rich.console import Console

from strawberry.cli.app import app
from strawberry.cli.utils import load_schema
from strawberry.utils.locate_definition import (
    locate_definition as locate_definition_util,
)

err_console = Console(stderr=True)


@app.command(help="Locate a definition in the schema (output: path:line:column)")
def locate_definition(
    schema: str,
    symbol: str,
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
) -> None:
    schema_symbol = load_schema(schema, app_dir)

    if location := locate_definition_util(schema_symbol, symbol):
        typer.echo(location)
    else:
        err_console.print(f"Definition not found: {symbol}")
        sys.exit(1)
