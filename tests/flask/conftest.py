import pytest

from .app import create_app


@pytest.fixture
def flask_client():
    with create_app().test_client() as client:
        yield client
