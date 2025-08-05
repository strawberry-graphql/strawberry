try:
    from .app import app
    from .commands.codegen import codegen as codegen
    from .commands.export_schema import export_schema as export_schema
    from .commands.locate_definition import (
        locate_definition as locate_definition,
    )
    from .commands.schema_codegen import (
        schema_codegen as schema_codegen,
    )
    from .commands.server import server as server
    from .commands.upgrade import upgrade as upgrade

    def run() -> None:
        app()

except ModuleNotFoundError as exc:
    from strawberry.exceptions import MissingOptionalDependenciesError

    raise MissingOptionalDependenciesError(extras=["cli"]) from exc
