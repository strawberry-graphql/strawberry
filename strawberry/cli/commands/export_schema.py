import importlib

import click

from strawberry.printer import print_schema


@click.command("export_schema", short_help="Exports the schema")
@click.argument("module", type=str)
def export_schema(module: str):
    schema_module = importlib.import_module(module)
    schema = getattr(schema_module, "schema")
    print(print_schema(schema))
