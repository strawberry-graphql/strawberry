import sys

import click

from strawberry import Schema
from strawberry.utils.importer import import_module_symbol


def load_schema(schema: str, app_dir: str) -> Schema:
    sys.path.insert(0, app_dir)

    try:
        schema_symbol = import_module_symbol(schema, default_symbol_name="schema")
    except (ImportError, AttributeError) as exc:
        message = str(exc)

        raise click.BadArgumentUsage(message)

    if not isinstance(schema_symbol, Schema):
        message = "The `schema` must be an instance of strawberry.Schema"
        raise click.BadArgumentUsage(message)

    return schema_symbol
