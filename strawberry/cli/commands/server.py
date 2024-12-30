import os
import sys
from enum import Enum

import rich
import typer

from strawberry.cli.app import app
from strawberry.cli.constants import (
    DEBUG_SERVER_LOG_OPERATIONS,
    DEBUG_SERVER_SCHEMA_ENV_VAR_KEY,
)
from strawberry.cli.utils import load_schema


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"

    __slots__ = ()


@app.command(help="Starts debug server")
def server(
    schema: str,
    host: str = typer.Option("0.0.0.0", "-h", "--host", show_default=True),  # noqa: S104
    port: int = typer.Option(8000, "-p", "--port", show_default=True),
    log_level: LogLevel = typer.Option(
        "error",
        "--log-level",
        help="passed to uvicorn to determine the log level",
    ),
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
    log_operations: bool = typer.Option(
        True,
        "--log-operations",
        show_default=True,
        help="Log GraphQL operations",
    ),
) -> None:
    sys.path.insert(0, app_dir)

    try:
        import starlette  # noqa: F401
        import uvicorn
    except ImportError:
        rich.print(
            "[red]Error: The debug server requires additional packages, "
            "install them by running:\n"
            r"pip install 'strawberry-graphql\[debug-server]'"
        )
        raise typer.Exit(1)  # noqa: B904

    load_schema(schema, app_dir=app_dir)

    os.environ[DEBUG_SERVER_SCHEMA_ENV_VAR_KEY] = schema
    os.environ[DEBUG_SERVER_LOG_OPERATIONS] = str(log_operations)
    app = "strawberry.cli.debug_server:app"

    # Windows doesn't support UTF-8 by default
    endl = " 🍓\n" if sys.platform != "win32" else "\n"
    print(f"Running strawberry on http://{host}:{port}/graphql", end=endl)  # noqa: T201

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=True,
        reload_dirs=[app_dir],
    )
