try:
    from .app import app
    from .commands.codegen import codegen as codegen  # noqa
    from .commands.export_schema import export_schema as export_schema  # noqa
    from .commands.schema_codegen import schema_codegen as schema_codegen  # noqa
    from .commands.server import server as server  # noqa
    from .commands.upgrade import upgrade as upgrade  # noqa

    def run() -> None:
        app()

except ModuleNotFoundError as exc:
    from strawberry.exceptions import MissingOptionalDependenciesError

    raise MissingOptionalDependenciesError(extras=["cli"]) from exc
