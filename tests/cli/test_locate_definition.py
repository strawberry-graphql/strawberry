from typer import Typer
from typer.testing import CliRunner


def test_find_model_name(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User"])

    assert result.exit_code == 0
    assert result.stdout.strip().endswith(
        "tests/fixtures/sample_package/sample_module.py:10:7"
    )


def test_find_model_field(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User.name"])

    assert result.exit_code == 0
    assert result.stdout.strip().endswith(
        "tests/fixtures/sample_package/sample_module.py:11:5"
    )


def test_find_missing_model(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "Missing"])

    assert result.exit_code == 1
    assert result.stdout.strip() == "Definition not found: Missing"


def test_find_missing_model_field(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app, ["locate-definition", selector, "Missing.field"]
    )

    assert result.exit_code == 1
    assert result.stdout.strip() == "Definition not found: Missing.field"


def test_find_missing_schema(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:missing"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User"])

    assert result.exit_code == 2
