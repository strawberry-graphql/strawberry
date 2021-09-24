import os
import re
import sys
import time

import pytest

import requests
import uvicorn
from xprocess import ProcessStarter

from strawberry.cli.commands.server import server as cmd_server


BOOT_MSG = "Running strawberry on http://0.0.0.0:8000/graphql"
if sys.platform != "win32":
    # UTF-8 chars are not supported by default console on Windows
    BOOT_MSG = BOOT_MSG + " 🍓"

BOOT_MSG_RE = re.compile(f"^{BOOT_MSG}\n")


def test_cli_cmd_server(cli_runner):
    schema = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_server, [schema])

    assert result.exit_code == 0
    assert uvicorn.run.call_count == 1
    assert BOOT_MSG_RE.match(result.output)


def test_cli_cmd_server_app_dir_option(cli_runner):
    result = cli_runner.invoke(
        cmd_server, ["--app-dir=./tests/fixtures/sample_package", "sample_module"]
    )

    assert result.exit_code == 0
    assert uvicorn.run.call_count == 1
    assert BOOT_MSG_RE.match(result.output)


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


def test_automatic_reloading(xprocess, tmp_path):

    # used to start our dev server
    class Starter(ProcessStarter):
        # Unbuffered output improves start up detection reliabiity on Windows
        env = {"PYTHONUNBUFFERED": "1", **os.environ}
        # considered started once this pattern is found
        pattern = BOOT_MSG_RE
        terminate_on_interrupt = True
        timeout = 10
        args = [
            "poetry",
            "run",
            "strawberry",
            "server",
            "--app-dir",
            # Python Versions < 3.8 on Windows do not have an Iterable WindowsPath
            # casting to str prevents this from throwing a TypeError on Windows
            str(tmp_path),
            "schema",
        ]

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

    xprocess.ensure("dev_server", Starter)

    url = "http://127.0.0.1:8000/graphql"
    query = {"query": "{ number }"}

    # this disables proxy use on Windows
    proxies = {"http": None}

    for _ in range(5):
        try:
            response = requests.post(url, json=query, proxies=proxies)
            assert response.status_code == 200
            assert response.json() == {"data": {"number": 42}}
        except requests.RequestException:
            time.sleep(0.5)

    # trigger reload
    schema_file_path.write_text(source.format(1234))

    # It takes uvicorn some time to detect file changes
    for _ in range(5):
        try:
            response = requests.post(url, json=query, proxies=proxies)
            assert response.status_code == 200
            assert response.json() == {"data": {"number": 1234}}
        except AssertionError:
            time.sleep(0.5)

    xprocess.getinfo("dev_server").terminate()
