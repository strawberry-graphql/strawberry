import re
import sys
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture, MockFixture
from starlette.testclient import TestClient
from typer import Typer
from typer.testing import CliRunner

# UTF-8 chars are not supported by default console on Windows
BOOT_MSG_END = " 🍓\n" if sys.platform != "win32" else "\n"
BOOT_MSG = f"Running strawberry on http://0.0.0.0:8000/graphql{BOOT_MSG_END}"

cli_runner = CliRunner()


@pytest.fixture
def uvicorn_run_mock(mocker: MockFixture) -> MagicMock:
    # uvicorn is only conditionally imported by the cli command,
    # so we need to import it here to be able to mock it
    import uvicorn

    return mocker.patch.object(uvicorn, "run")


def test_without_options(cli_app: Typer, uvicorn_run_mock: MagicMock):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    assert result.exit_code == 0, result.stdout
    assert uvicorn_run_mock.call_count == 1
    assert re.match(BOOT_MSG, result.stdout)


def test_app_dir_option(cli_app: Typer, uvicorn_run_mock: MagicMock):
    result = cli_runner.invoke(
        cli_app,
        ["dev", "--app-dir=./tests/fixtures/sample_package", "sample_module"],
    )

    assert result.exit_code == 0, result.stdout
    assert uvicorn_run_mock.call_count == 1
    assert re.match(BOOT_MSG, result.stdout)


def test_default_schema_symbol_name(cli_app: Typer, uvicorn_run_mock: MagicMock):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    assert result.exit_code == 0, result.stdout
    assert uvicorn_run_mock.call_count == 1


def test_invalid_app_dir(cli_app: Typer):
    result = cli_runner.invoke(cli_app, ["dev", "--app-dir=./non/existing/path", "app"])

    expected_error = "Error: No module named 'app'"

    assert result.exit_code == 2
    assert expected_error in result.stdout


def test_invalid_module(cli_app: Typer):
    schema = "not.existing.module"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    expected_error = "Error: No module named 'not'"

    assert result.exit_code == 2
    assert expected_error in result.stdout


def test_invalid_symbol(cli_app: Typer):
    schema = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    expected_error = (
        "Error: module 'tests.fixtures.sample_package.sample_module' "
        "has no attribute 'not'"
    )

    assert result.exit_code == 2
    assert expected_error in result.stdout.replace("\n", "")


def test_invalid_schema_instance(cli_app: Typer):
    schema = "tests.fixtures.sample_package.sample_module:not_a_schema"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    expected_error = "Error: The `schema` must be an instance of strawberry.Schema"

    assert result.exit_code == 2
    assert expected_error in result.stdout


@pytest.mark.parametrize("dependency", ["uvicorn", "starlette"])
def test_missing_dev_server_dependencies(
    cli_app: Typer, mocker: MockerFixture, dependency: str
):
    mocker.patch.dict(sys.modules, {dependency: None})

    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["dev", schema])

    assert result.exit_code == 1
    assert result.stdout == (
        "Error: "
        "The dev server requires additional packages, install them by running:\n"
        "pip install 'strawberry-graphql[cli]'\n"
    )


@pytest.mark.parametrize("path", ["/", "/graphql"])
def test_dev_server_routes(dev_server_client: TestClient, path: str):
    response = dev_server_client.get(path)
    assert response.status_code == 200
