import pytest

from click.testing import CliRunner


@pytest.fixture
def cli_runner(mocker):
    # Mock of uvicorn.run
    uvicorn_run_patch = mocker.patch("uvicorn.run")
    uvicorn_run_patch.return_value = True
    return CliRunner()
