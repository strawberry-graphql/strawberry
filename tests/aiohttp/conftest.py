import pytest

import pytest_asyncio

from strawberry.aiohttp.test.client import GraphQLTestClient
from tests.aiohttp.app import create_app


@pytest_asyncio.fixture
async def aiohttp_app_client(event_loop, aiohttp_client):
    app = create_app(graphiql=True)
    event_loop.set_debug(True)
    return await aiohttp_client(app)


@pytest_asyncio.fixture
async def aiohttp_app_client_no_get(event_loop, aiohttp_client):
    app = create_app(graphiql=True, allow_queries_via_get=False)
    event_loop.set_debug(True)
    return await aiohttp_client(app)


@pytest.fixture
def graphql_client(aiohttp_app_client):
    yield GraphQLTestClient(aiohttp_app_client)
