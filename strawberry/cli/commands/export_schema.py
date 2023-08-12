import typer

from strawberry.cli.app import app
from strawberry.cli.utils import load_schema
from strawberry.printer import print_schema


@app.command(help="Exports the schema")
def export_schema(
    schema: str,
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
    output: str = typer.Option(
        None,
        "--output",
        help="File to save the exported schema. If not provided, prints to console.",
    ),
) -> None:
    schema_symbol = load_schema(schema, app_dir)

    schema_text = print_schema(schema_symbol)  # noqa: T201

    if output:
        with open(output, "w") as file:
            file.write(schema_text)
        typer.echo(f"Schema exported to {output}")
    else:
        print(schema_text)