import sys

import typer
from rich.console import Console

from strawberry.cli.app import app
from strawberry.cli.utils import load_schema
from strawberry.exceptions.utils.source_finder import SourceFinder

err_console = Console(stderr=True)


@app.command(help="Locate a definition in the schema")
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

    finder = SourceFinder()

    if "." in symbol:
        model, field = symbol.split(".")
    else:
        model, field = symbol, None

    schema_type = schema_symbol.get_type_by_name(model)

    if not schema_type:
        err_console.print(f"Definition not found: {symbol}")
        sys.exit(1)

    location = (
        finder.find_class_attribute_from_object(schema_type.origin, field)
        if field
        else finder.find_class_from_object(schema_type.origin)
    )

    if not location:
        err_console.print(f"Definition not found: {symbol}")
        sys.exit(1)

    typer.echo(f"{location.path}:{location.error_line}:{location.error_column + 1}")
