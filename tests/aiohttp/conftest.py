import pytest

from .app import create_app


@pytest.fixture
def aiohttp_app_client(loop, aiohttp_client):
    app_dings = create_app(graphiql=True)
    loop.set_debug(True)
    return loop.run_until_complete(aiohttp_client(app_dings))
