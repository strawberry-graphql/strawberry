import pytest

from .app import create_app


@pytest.fixture
def sanic_client():
    yield create_app()
