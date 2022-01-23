import pytest

from .app import create_app


@pytest.fixture
def sanic_client():
    yield create_app()


@pytest.fixture
def sanic_client_no_graphiql():
    yield create_app(graphiql=False)
