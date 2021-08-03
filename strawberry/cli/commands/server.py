import importlib
import sys

import click

from strawberry import Schema
from strawberry.asgi import GraphQL
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
        import hupper
        import uvicorn
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
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

    reloader = hupper.start_reloader("strawberry.cli.run", verbose=False)
    schema_module = importlib.import_module(schema_symbol.__module__)
    reloader.watch_files([schema_module.__file__])

    app = Starlette(debug=True)
    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
    )

    graphql_app = GraphQL(schema_symbol, debug=True)

    paths = ["/", "/graphql"]
    for path in paths:
        app.add_route(path, graphql_app)
        app.add_websocket_route(path, graphql_app)

    print(f"Running strawberry on http://{host}:{port}/graphql 🍓")
    uvicorn.run(app, loop="none", host=host, port=port, log_level="error")
