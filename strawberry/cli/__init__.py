try:
    from .app import app
    from .commands.codegen import codegen as codegen  # noqa: PLC0414
    from .commands.export_schema import export_schema as export_schema  # noqa: PLC0414
    from .commands.locate_definition import (
        locate_definition as locate_definition,  # noqa: PLC0414
    )
    from .commands.schema_codegen import (
        schema_codegen as schema_codegen,  # noqa: PLC0414
    )
    from .commands.server import server as server  # noqa: PLC0414
    from .commands.upgrade import upgrade as upgrade  # noqa: PLC0414

    def run() -> None:
        app()

except ModuleNotFoundError as exc:
    from strawberry.exceptions import MissingOptionalDependenciesError

    raise MissingOptionalDependenciesError(extras=["cli"]) from exc
