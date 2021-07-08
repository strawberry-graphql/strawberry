import click

from .commands.export_schema import export_schema as cmd_export_schema
from .commands.server import server as cmd_server


@click.group()
def run():  # pragma: no cover
    pass


run.add_command(cmd_server)
run.add_command(cmd_export_schema)
