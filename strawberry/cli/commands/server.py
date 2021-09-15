import os
import sys

import click

from strawberry import Schema
from strawberry.cli.constants import DEBUG_SERVER_SCHEMA_ENV_VAR_KEY
from strawberry.utils.importer import import_module_symbol


@click.command("server", short_help="Starts debug server")
@click.argument("schema", type=str)
@click.option("-h", "--host", default="0.0.0.0", type=str)
@click.option("-p", "--port", default=8000, type=int)
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
def server(schema, host, port, app_dir):
    sys.path.insert(0, app_dir)

    try:
        import starlette  # noqa: F401
        import uvicorn
    except ImportError:
        message = (
            "The debug server requires additional packages, install them by running:\n"
            "pip install strawberry-graphql[debug-server]"
        )
        raise click.ClickException(message)

    try:
        schema_symbol = import_module_symbol(schema, default_symbol_name="schema")
    except (ImportError, AttributeError) as exc:
        message = str(exc)
        raise click.BadArgumentUsage(message)

    if not isinstance(schema_symbol, Schema):
        message = "The `schema` must be an instance of strawberry.Schema"
        raise click.BadArgumentUsage(message)

    os.environ[DEBUG_SERVER_SCHEMA_ENV_VAR_KEY] = schema
    app = "strawberry.cli.debug_server:app"

    print(f"Running strawberry on http://{host}:{port}/graphql 🍓")
    uvicorn.run(
        app, host=host, port=port, log_level="error", reload=True, reload_dirs=[app_dir]
    )
