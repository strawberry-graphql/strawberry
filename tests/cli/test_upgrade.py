from typer.testing import CliRunner

from strawberry.cli.app import app


def test_upgrade_returns_error_code_if_codemod_does_not_exist(cli_runner: CliRunner):
    result = cli_runner.invoke(
        app,
        ["upgrade", "a_random_codemod"],
    )

    assert result.exit_code == 2
    assert 'Upgrade named "a_random_codemod" does not exist' in result.stdout
