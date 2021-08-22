import os
import signal
import subprocess
import sys
import time

import pytest

import requests
import uvicorn

from strawberry.cli.commands.server import server as cmd_server


def test_cli_cmd_server(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_server, [schema])

    assert result.exit_code == 0
    assert uvicorn.run.call_count == 1
    assert result.output == "Running strawberry on http://0.0.0.0:8000/graphql 🍓\n"


def test_cli_cmd_server_app_dir_option(cli_runner):
    result = cli_runner.invoke(
        cmd_server, ["--app-dir=./tests/fixtures/sample_package", "sample_module"]
    )

    assert result.exit_code == 0
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


@pytest.mark.parametrize("dependency", ["uvicorn", "starlette"])
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


def test_debug_server_routes(debug_server_client):
    for path in ["/", "/graphql"]:
        response = debug_server_client.get(path)
        assert response.status_code == 200


def test_automatic_reloading(tmp_path):
    source = (
        "import strawberry\n"
        "@strawberry.type\n"
        "class Query:\n"
        "    @strawberry.field\n"
        "    def number(self) -> int:\n"
        "        return {}\n"
        "schema = strawberry.Schema(query=Query)\n"
    )

    schema_file_path = tmp_path / "schema.py"
    schema_file_path.touch()
    schema_file_path.write_text(source.format(42))

    args = ["poetry", "run", "strawberry", "server", "--app-dir", tmp_path, "schema"]

    with subprocess.Popen(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
    ) as proc:

        url = "http://127.0.0.1:8000/graphql"
        query = {"query": "{ number }"}

        # It takes uvicorn some time to initially start the server
        for i in range(5):
            try:
                response = requests.post(url, json=query)
                assert response.status_code == 200
                assert response.json() == {"data": {"number": 42}}
            except requests.RequestException:
                time.sleep(0.5)

        schema_file_path.write_text(source.format(1234))

        # It takes uvicorn some time to detect file changes
        for _ in range(5):
            try:
                response = requests.post(url, json=query)
                assert response.status_code == 200
                assert response.json() == {"data": {"number": 1234}}
            except AssertionError:
                time.sleep(0.5)

        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate(timeout=10)
