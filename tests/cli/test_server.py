from typer import Typer
from typer.testing import CliRunner


def test_command_fails_with_deprecation_message(cli_app: Typer, cli_runner: CliRunner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["server", schema])

    assert result.exit_code == 1
    assert (
        result.stdout
        == "The `strawberry server` command is deprecated, use `strawberry dev` instead.\n"
    )
