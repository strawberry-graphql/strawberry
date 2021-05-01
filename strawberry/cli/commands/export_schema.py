import importlib

import click

from strawberry.printer import print_schema


@click.command(short_help="Exports the schema")
@click.argument("selector", type=str)
def export_schema(selector: str):
    module_name, symbol_name = selector.rsplit(":", 1)
    schema_module = importlib.import_module(module_name)
    schema_symbol = getattr(schema_module, symbol_name)
    print(print_schema(schema_symbol))
