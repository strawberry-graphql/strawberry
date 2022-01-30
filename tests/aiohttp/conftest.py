import pytest

from strawberry.aiohttp.test.client import GraphQLTestClient
from tests.aiohttp.app import create_app


@pytest.fixture
def aiohttp_app_client(loop, aiohttp_client):
    app = create_app(graphiql=True)
    loop.set_debug(True)
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def graphql_client(aiohttp_app_client):
    yield GraphQLTestClient(aiohttp_app_client)
