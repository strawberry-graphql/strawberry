from enum import Enum

import typer

from strawberry.cli.app import app


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
) -> None:
    typer.echo(
        "The `strawberry server` command is deprecated, use `strawberry dev` instead."
    )
    raise typer.Exit(1)
