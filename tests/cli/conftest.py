import sys

import pytest

from click.testing import CliRunner
from starlette.testclient import TestClient


@pytest.fixture
def cli_runner(mocker):
    # Mock of uvicorn.run
    uvicorn_run_patch = mocker.patch("uvicorn.run")
    uvicorn_run_patch.return_value = True
    return CliRunner()


@pytest.fixture
def debug_server_client(mocker):
    schema_import_path = "tests.fixtures.sample_package.sample_module"
    mocker.patch.object(sys, "argv", ["strawberry", "server", schema_import_path])

    from strawberry.cli.debug_server import app

    return TestClient(app)
