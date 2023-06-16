from .commands.codegen import codegen  # noqa
from .commands.export_schema import export_schema  # noqa
from .commands.server import server  # noqa


from .app import app


def run() -> None:
    app()
