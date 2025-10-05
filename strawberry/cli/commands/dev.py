import os
import sys
from enum import Enum
from typing import Annotated

import rich
import typer

from strawberry.cli.app import app
from strawberry.cli.constants import DEV_SERVER_SCHEMA_ENV_VAR_KEY
from strawberry.cli.utils import load_schema


class LogLevel(str, Enum):
    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"
    trace = "trace"


@app.command(help="Starts the dev server")
def dev(
    schema: str,
    host: Annotated[
        str, typer.Option("-h", "--host", help="Host to bind the server to.")
    ] = "0.0.0.0",  # noqa: S104
    port: Annotated[
        int, typer.Option("-p", "--port", help="Port to bind the server to.")
    ] = 8000,
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "--log-level", help="Passed to uvicorn to determine the server log level."
        ),
    ] = LogLevel.error,
    app_dir: Annotated[
        str,
        typer.Option(
            "--app-dir",
            help="Look for the schema module in the specified directory, by adding this to the PYTHONPATH. Defaults to the current working directory.",
        ),
    ] = ".",
) -> None:
    try:
        import starlette  # noqa: F401
        import uvicorn
    except ImportError:
        rich.print(
            "[red]Error: The dev server requires additional packages, install them by running:\n"
            r"pip install 'strawberry-graphql\[cli]'"
        )
        raise typer.Exit(1) from None

    sys.path.insert(0, app_dir)
    load_schema(schema, app_dir=app_dir)

    os.environ[DEV_SERVER_SCHEMA_ENV_VAR_KEY] = schema
    asgi_app = "strawberry.cli.dev_server:app"

    end = " 🍓\n" if sys.platform != "win32" else "\n"
    rich.print(f"Running strawberry on http://{host}:{port}/graphql", end=end)

    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        log_level=log_level,
        reload=True,
        reload_dirs=[app_dir],
    )
