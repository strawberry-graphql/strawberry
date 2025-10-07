from pathlib import Path

from inline_snapshot import snapshot
from typer import Typer
from typer.testing import CliRunner

from tests.typecheckers.utils.marks import skip_on_windows

pytestmark = skip_on_windows


def _simplify_path(path: str) -> str:
    path = Path(path)

    root = Path(__file__).parents[1]

    return str(path.relative_to(root))


def test_find_model_name(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User"])

    assert result.exit_code == 0
    assert _simplify_path(result.stdout.strip()) == snapshot(
        "fixtures/sample_package/sample_module.py:38:7"
    )


def test_find_model_field(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User.name"])

    assert result.exit_code == 0
    assert _simplify_path(result.stdout.strip()) == snapshot(
        "fixtures/sample_package/sample_module.py:39:5"
    )


def test_find_missing_model(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "Missing"])

    assert result.exit_code == 1
    assert result.stderr.strip() == snapshot("Definition not found: Missing")


def test_find_missing_model_field(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app, ["locate-definition", selector, "Missing.field"]
    )

    assert result.exit_code == 1
    assert result.stderr.strip() == snapshot("Definition not found: Missing.field")


def test_find_missing_schema(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:missing"
    result = cli_runner.invoke(cli_app, ["locate-definition", selector, "User"])

    assert result.exit_code == 2
