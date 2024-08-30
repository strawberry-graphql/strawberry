import pytest


@pytest.fixture
def test_client():
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive():
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)
