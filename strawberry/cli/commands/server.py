import os
import sys

import click

from strawberry.cli.constants import DEBUG_SERVER_SCHEMA_ENV_VAR_KEY
from strawberry.cli.utils import load_schema


@click.command("server", short_help="Starts debug server")
@click.argument("schema", type=str)
@click.option("-h", "--host", default="0.0.0.0", type=str)
@click.option("-p", "--port", default=8000, type=int)
@click.option(
    "--log-level",
    default="error",
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    help="passed to uvicorn to determine the log level",
)
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
def server(schema, host, port, log_level, app_dir):
    sys.path.insert(0, app_dir)

    try:
        import starlette  # noqa: F401
        import uvicorn
    except ImportError:
        message = (
            "The debug server requires additional packages, install them by running:\n"
            "pip install 'strawberry-graphql[debug-server]'"
        )
        raise click.ClickException(message)

    load_schema(schema, app_dir=app_dir)

    os.environ[DEBUG_SERVER_SCHEMA_ENV_VAR_KEY] = schema
    app = "strawberry.cli.debug_server:app"

    # Windows doesn't support UTF-8 by default
    endl = " 🍓\n" if sys.platform != "win32" else "\n"
    print(f"Running strawberry on http://{host}:{port}/graphql", end=endl)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=True,
        reload_dirs=[app_dir],
    )
