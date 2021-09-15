import sys

import click

from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


@click.command(short_help="Exports the schema")
@click.argument("schema", type=str)
@click.option(
    "--app-dir",
    default=".",
    type=str,
    show_default=True,
    help=(
        "Look for the module in the specified directory, by adding this to the "
        "PYTHONPATH. Defaults to the current working directory. "
        "Works the same as `--app-dir` in uvicorn."
    ),
)
def export_schema(schema: str, app_dir):
    sys.path.insert(0, app_dir)

    try:
        schema_symbol = import_module_symbol(schema, default_symbol_name="schema")
    except (ImportError, AttributeError) as exc:
        message = str(exc)
        raise click.BadArgumentUsage(message)
    if not isinstance(schema_symbol, Schema):
        message = "The `schema` must be an instance of strawberry.Schema"
        raise click.BadArgumentUsage(message)
    print(print_schema(schema_symbol))
