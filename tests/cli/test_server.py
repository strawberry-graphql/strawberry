import hupper
import uvicorn

from strawberry.cli.commands.server import server as cmd_server


def test_cli_cmd_server(cli_runner):
    result = cli_runner.invoke(cmd_server, ["tests.cli.helpers.sample_schema"], "")
    assert result.exit_code == 0

    # We started the reloader
    assert hupper.start_reloader.call_count == 1
    assert uvicorn.run.call_count == 1

    assert result.output == "Running strawberry on http://0.0.0.0:8000/ 🍓\n"


def test_cli_cmd_server_app_dir_option(cli_runner):
    result = cli_runner.invoke(
        cmd_server, ["--app-dir=./tests/cli/helpers", "sample_schema"], ""
    )
    assert result.exit_code == 0

    # We started the reloader
    assert hupper.start_reloader.call_count == 1
    assert uvicorn.run.call_count == 1

    assert result.output == "Running strawberry on http://0.0.0.0:8000/ 🍓\n"
