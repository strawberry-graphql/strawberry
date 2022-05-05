import click

from strawberry.cli.utils import load_schema
from strawberry.printer import print_schema


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
def export_schema(schema: str, app_dir: str):
    schema_symbol = load_schema(schema, app_dir)

    print(print_schema(schema_symbol))
