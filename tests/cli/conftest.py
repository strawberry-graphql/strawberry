import pytest

from click.testing import CliRunner


@pytest.fixture
def cli_runner(mocker):
    # Mock of uvicorn.run
    uvicorn_run_patch = mocker.patch("uvicorn.run")
    uvicorn_run_patch.return_value = True
    # Mock to prevent the reloader from kicking in
    hupper_reloader_patch = mocker.patch("hupper.start_reloader")
    hupper_reloader_patch.return_value = MockReloader()
    return CliRunner()


class MockReloader:
    @staticmethod
    def watch_files(*args, **kwargs):
        return True
