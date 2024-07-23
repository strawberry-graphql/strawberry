try:
    import typer

    from .commands.codegen import codegen_app
    from .commands.export_schema import export_schema_app
    from .commands.schema_codegen import schema_codegen_app
    from .commands.server import server_app
    from .commands.upgrade import upgrade_app


except ModuleNotFoundError as exc:
    from strawberry.exceptions import MissingOptionalDependenciesError

    raise MissingOptionalDependenciesError(extras=["cli"]) from exc


app = typer.Typer(no_args_is_help=True)
app.add_typer(codegen_app)
app.add_typer(export_schema_app)
app.add_typer(schema_codegen_app)
app.add_typer(server_app)
app.add_typer(upgrade_app)


def run() -> None:
    app()
