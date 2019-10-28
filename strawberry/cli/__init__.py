import click

from .commands.server import server as cmd_server


@click.group()
def run():
    pass


run.add_command(cmd_server)
