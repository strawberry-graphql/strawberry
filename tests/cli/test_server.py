import hupper
import uvicorn
from click.testing import CliRunner

from strawberry.cli.commands.server import server as cmd_server


def test_cli_cmd_server(mocker):

    # Mock of uvicorn.run
    uvicorn_run_patch = mocker.patch("uvicorn.run")
    uvicorn_run_patch.return_value = True
    # Mock to prevent the reloader from kicking in
    hupper_reloader_patch = mocker.patch("hupper.start_reloader")
    hupper_reloader_patch.return_value = MockReloader()
    runner = CliRunner()

    result = runner.invoke(cmd_server, ["tests.cli.helpers.sample_schema"], "")
    assert result.exit_code == 0

    # We started the reloader
    assert hupper.start_reloader.call_count == 1
    assert uvicorn.run.call_count == 1

    assert result.output == "Running strawberry on http://0.0.0.0:8000/ 🍓\n"


class MockReloader:
    @staticmethod
    def watch_files(*args, **kwargs):
        return True
