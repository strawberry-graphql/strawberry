from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from strawberry.cli.constants import DEV_SERVER_SCHEMA_ENV_VAR_KEY

if TYPE_CHECKING:
    from starlette.testclient import TestClient
    from typer import Typer


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def dev_server_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from starlette.testclient import TestClient

    from strawberry.cli.dev_server import app

    monkeypatch.setenv(
        DEV_SERVER_SCHEMA_ENV_VAR_KEY,
        "tests.fixtures.sample_package.sample_module",
    )

    return TestClient(app)


@pytest.fixture
def cli_app() -> Typer:
    from strawberry.cli.app import app

    return app
