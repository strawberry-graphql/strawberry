import pytest


@pytest.fixture
def test_client():
    from starlite.testing import TestClient
    from tests.starlite.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive():
    from starlite.testing import TestClient
    from tests.starlite.app import create_app

    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)
