from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


@pytest.fixture
def test_client() -> TestClient:
    from fastapi.testclient import TestClient
    from tests.fastapi.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive() -> TestClient:
    from fastapi.testclient import TestClient
    from tests.fastapi.app import create_app

    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql() -> TestClient:
    from fastapi.testclient import TestClient
    from tests.fastapi.app import create_app

    app = create_app(graphiql=False)
    return TestClient(app)
