import pytest

from .app import create_app


@pytest.fixture
def flask_client():
    with create_app().test_client() as client:
        yield client


@pytest.fixture
def async_flask_client():
    with create_app(use_async_view=True).test_client() as client:
        yield client


@pytest.fixture
def flask_client_no_graphiql():
    with create_app(graphiql=False).test_client() as client:
        yield client


@pytest.fixture
def flask_client_no_get():
    with create_app(allow_queries_via_get=False).test_client() as client:
        yield client
