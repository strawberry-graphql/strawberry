from __future__ import annotations

import re
import sys

import pytest
from pytest_mock import MockerFixture
from starlette.testclient import TestClient
from typer import Typer
from typer.testing import CliRunner

BOOT_MSG = "Running strawberry on http://0.0.0.0:8000/graphql"

if sys.platform != "win32":
    # UTF-8 chars are not supported by default console on Windows
    BOOT_MSG += " 🍓"

BOOT_MSG += "\n"


def test_cli_cmd_server(cli_app: Typer, cli_runner: CliRunner):
    import uvicorn

    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["server", schema])

    assert result.exit_code == 0
    assert uvicorn.run.call_count == 1
    assert re.match(BOOT_MSG, result.stdout)


def test_cli_cmd_server_app_dir_option(cli_app: Typer, cli_runner: CliRunner):
    import uvicorn

    result = cli_runner.invoke(
        cli_app,
        ["server", "--app-dir=./tests/fixtures/sample_package", "sample_module"],
    )

    assert result.exit_code == 0
    assert uvicorn.run.call_count == 1
    assert re.match(BOOT_MSG, result.stdout)


def test_default_schema_symbol_name(cli_app: Typer, cli_runner: CliRunner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["server", schema])

    assert result.exit_code == 0


def test_invalid_module(cli_app: Typer, cli_runner: CliRunner):
    schema = "not.existing.module"
    result = cli_runner.invoke(cli_app, ["server", schema])

    expected_error = "Error: No module named 'not'"

    assert result.exit_code == 2
    assert expected_error in result.stdout


def test_invalid_symbol(cli_app: Typer, cli_runner: CliRunner):
    schema = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    result = cli_runner.invoke(cli_app, ["server", schema])

    expected_error = (
        "Error: module 'tests.fixtures.sample_package.sample_module' "
        "has no attribute 'not'"
    )

    assert result.exit_code == 2
    assert expected_error in result.stdout.replace("\n", "")


def test_invalid_schema_instance(cli_app: Typer, cli_runner: CliRunner):
    schema = "tests.fixtures.sample_package.sample_module:not_a_schema"
    result = cli_runner.invoke(cli_app, ["server", schema])

    expected_error = "Error: The `schema` must be an instance of strawberry.Schema"

    assert result.exit_code == 2
    assert expected_error in result.stdout


@pytest.mark.parametrize("dependency", ["uvicorn", "starlette"])
def test_missing_debug_server_dependencies(
    cli_app: Typer, cli_runner: CliRunner, mocker: MockerFixture, dependency: str
):
    mocker.patch.dict(sys.modules, {dependency: None})

    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["server", schema])

    assert result.exit_code == 1
    assert result.stdout == (
        "Error: "
        "The debug server requires additional packages, install them by running:\n"
        "pip install 'strawberry-graphql[debug-server]'\n"
    )


def test_debug_server_routes(debug_server_client: TestClient):
    for path in ["/", "/graphql"]:
        response = debug_server_client.get(path)
        assert response.status_code == 200
