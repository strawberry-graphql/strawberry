import sys

import pytest

import hupper
import uvicorn

from strawberry.cli.commands.server import server as cmd_server


def test_cli_cmd_server(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_server, [schema])
    assert result.exit_code == 0

    # We started the reloader
    assert hupper.start_reloader.call_count == 1
    assert uvicorn.run.call_count == 1

    assert result.output == "Running strawberry on http://0.0.0.0:8000/graphql 🍓\n"


def test_cli_cmd_server_app_dir_option(cli_runner):
    result = cli_runner.invoke(
        cmd_server, ["--app-dir=./tests/fixtures/sample_package", "sample_module"]
    )
    assert result.exit_code == 0

    # We started the reloader
    assert hupper.start_reloader.call_count == 1
    assert uvicorn.run.call_count == 1

    assert result.output == "Running strawberry on http://0.0.0.0:8000/graphql 🍓\n"


def test_default_schema_symbol_name(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_server, [schema])

    assert result.exit_code == 0


def test_invalid_module(cli_runner):
    schema = "not.existing.module"
    result = cli_runner.invoke(cmd_server, [schema])

    expected_error = "Error: No module named 'not'"

    assert result.exit_code == 2
    assert expected_error in result.output


def test_invalid_symbol(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    result = cli_runner.invoke(cmd_server, [schema])

    expected_error = (
        "Error: module 'tests.fixtures.sample_package.sample_module' "
        "has no attribute 'not'"
    )

    assert result.exit_code == 2
    assert expected_error in result.output


def test_invalid_schema_instance(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module:not_a_schema"
    result = cli_runner.invoke(cmd_server, [schema])

    expected_error = "Error: The `schema` must be an instance of strawberry.Schema"

    assert result.exit_code == 2
    assert expected_error in result.output


@pytest.mark.parametrize("dependency", ["hupper", "uvicorn", "starlette.applications"])
def test_missing_debug_server_dependencies(cli_runner, mocker, dependency):
    mocker.patch.dict(sys.modules, {dependency: None})

    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_server, [schema])

    assert result.exit_code == 1
    assert result.output == (
        "Error: "
        "The debug server requires additional packages, install them by running:\n"
        "pip install strawberry-graphql[debug-server]\n"
    )
