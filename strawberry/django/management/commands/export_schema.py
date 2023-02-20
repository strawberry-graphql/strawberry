import pathlib
from django.core.management.base import BaseCommand, CommandError
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


class Command(BaseCommand):

    help = "Export the graphql schema"  # noqa:A003

    def add_arguments(self, parser):
        parser.add_argument("schema", nargs=1, type=str, help="The schema location")
        parser.add_argument(
            "--path", nargs="?", type=str, help="Optional path to export"
        )

    def handle(self, *args, **options):
        try:
            schema_symbol = import_module_symbol(
                options["schema"][0], default_symbol_name="schema"
            )
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e))

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path:
            pathlib.Path(path).write_text(schema_output)
        else:
            self.stdout.write(schema_output)
