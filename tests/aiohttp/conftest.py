import pytest

from tests.aiohttp.app import create_app


@pytest.fixture
def aiohttp_app_client(loop, aiohttp_client):
    app = create_app(graphiql=True)
    loop.set_debug(True)
    return loop.run_until_complete(aiohttp_client(app))
