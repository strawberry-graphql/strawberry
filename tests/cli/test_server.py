from click.testing import CliRunner

from strawberry.cli.commands.server import server as cmd_server

import uvicorn
import hupper

from unittest.mock import Mock


def test_cli_cmd_server(monkeypatch):

    def mock_uvicorn_run(*args, **kwargs):
        exit(0)

    def mock_hupper_start_reloader(*args, **kwargs):
        return MockReloader()

    # Mock of uvicorn.run
    monkeypatch.setattr(uvicorn, "run", Mock(wraps=mock_uvicorn_run))
    # Mock to prevent the reloader from kicking in
    monkeypatch.setattr(hupper, "start_reloader", Mock(wraps=mock_hupper_start_reloader))
    runner = CliRunner()

    result = runner.invoke(cmd_server, ['tests.cli.helpers.sample_schema'], "")
    assert result.exit_code == 0

    # We started the reloader
    hupper.start_reloader.assert_called_once
    uvicorn.run.assert_called_once

    assert result.output == 'Running strawberry on http://0.0.0.0:8000/graphql 🍓\n'


class MockReloader:
    @staticmethod
    def watch_files(*args, **kwargs):
        return True
