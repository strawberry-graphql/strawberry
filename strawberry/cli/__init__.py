import click

from .commands.schema_importer.import_schema import import_schema as cmd_import_schema
from .commands.server import server as cmd_server


@click.group()
def run():  # pragma: no cover
    pass


run.add_command(cmd_server)
run.add_command(cmd_import_schema)
