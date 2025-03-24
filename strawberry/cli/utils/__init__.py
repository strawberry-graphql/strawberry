import sys

import rich
import typer

from strawberry import Schema
from strawberry.utils.importer import import_module_symbol


def load_schema(schema: str, app_dir: str) -> Schema:
    sys.path.insert(0, app_dir)

    try:
        schema_symbol = import_module_symbol(schema, default_symbol_name="schema")
    except (ImportError, AttributeError) as exc:
        message = str(exc)

        rich.print(f"[red]Error: {message}")
        raise typer.Exit(2)  # noqa: B904

    if callable(schema_symbol):
        try:
            schema_symbol = schema_symbol()
        except Exception as exc:  # noqa: BLE001
            message = f"Error invoking schema_symbol: {exc}"
            rich.print(f"[red]Error: {message}")
            raise typer.Exit(2)  # noqa: B904

    if not isinstance(schema_symbol, Schema):
        message = "The `schema` must be an instance of strawberry.Schema"
        rich.print(f"[red]Error: {message}")
        raise typer.Exit(2)

    return schema_symbol
