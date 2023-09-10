from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest
from pytest_mock import MockFixture
from typer.testing import CliRunner

if TYPE_CHECKING:
    from starlette.testclient import TestClient
    from typer import Typer


@pytest.fixture
def cli_runner(mocker: MockFixture) -> CliRunner:
    # Mock of uvicorn.run
    uvicorn_run_patch = mocker.patch("uvicorn.run")
    uvicorn_run_patch.return_value = True
    return CliRunner()


@pytest.fixture
def debug_server_client(mocker: MockFixture) -> TestClient:
    from starlette.testclient import TestClient

    schema_import_path = "tests.fixtures.sample_package.sample_module"
    mocker.patch.object(sys, "argv", ["strawberry", "server", schema_import_path])

    from strawberry.cli.debug_server import app

    return TestClient(app)


@pytest.fixture
def cli_app() -> Typer:
    from strawberry.cli.app import app

    return app
