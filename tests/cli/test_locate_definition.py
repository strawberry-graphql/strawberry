from typer import Typer
from typer.testing import CliRunner


def test_find_model_name(mocker, cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User"])

    assert result.exit_code == 0
    assert result.stdout.strip().endswith(
        "tests/fixtures/sample_package/sample_module.py:10:7"
    )


def test_find_model_field(mocker, cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User.name"])

    assert result.exit_code == 0
    assert result.stdout.strip().endswith(
        "tests/fixtures/sample_package/sample_module.py:11:5"
    )
