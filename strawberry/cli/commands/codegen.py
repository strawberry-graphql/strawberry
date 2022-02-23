import click

from strawberry.cli.utils import load_schema
from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.python import PythonPlugin


@click.command(short_help="Generate code from a query")
@click.argument("schema", type=str)
@click.argument("query", type=str)
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
def codegen(schema: str, query: str, app_dir: str):
    schema_symbol = load_schema(schema, app_dir)

    code_generator = QueryCodegen(schema_symbol, plugins=[PythonPlugin()])

    with open(query) as f:
        code = code_generator.codegen(f.read())

    print(code)
