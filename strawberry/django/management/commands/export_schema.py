import sys

from django.core.management import BaseCommand, CommandParser, CommandError
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


def export_schema(schema: str, app_dir):
    sys.path.insert(0, app_dir)

    try:
        schema_symbol = import_module_symbol(schema, default_symbol_name="schema")
    except (ImportError, AttributeError) as exc:
        message = str(exc)
        raise CommandError(message)
    if not isinstance(schema_symbol, Schema):
        message = "The `schema` must be an instance of strawberry.Schema"
        raise CommandError(message)
    print(print_schema(schema_symbol))


class Command(BaseCommand):
    help = 'Exports the strawberry graphql schema'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("schema", type=str)
        parser.add_argument("--app-dir", action="store_true", default=".", help=(
            "Look for the module in the specified directory, by adding this to the "
            "PYTHONPATH. Defaults to the current working directory. "
            "Works the same as `--app-dir` in uvicorn."
        ))

    def handle(self, *args, **options):
        schema = options["schema"]
        app_dir = options["app_dir"]
        export_schema(schema, app_dir)
